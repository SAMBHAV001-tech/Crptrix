import os
import time
import joblib
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from backend.db import engine

# ---------------------------
# Model path
# ---------------------------
MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "xgboost_model.joblib"
)

# ---------------------------
# Lazy-loaded model
# ---------------------------
_model = None

def load_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model

# ---------------------------
# Feature cache (15-minute TTL)
# Prevents second-by-second drift between local & cloud.
# Both servers refresh at their own 15-min cadence → values
# stay stable within each window instead of changing every hit.
# ---------------------------
_feature_cache = {
    "data": None,       # cached DataFrame
    "timestamp": 0.0    # unix time of last fetch
}
FEATURE_CACHE_TTL = 900  # 15 minutes


# ---------------------------
# Feature columns (ORDER MATTERS)
# ---------------------------
FEATURE_COLUMNS = [
    "return_24h",
    "volatility_24h",
    "volume_change_24h",
    "avg_news_sentiment_24h",
    "sentiment_momentum"
]


# ---------------------------
# Live Feature Computation (primary — same on local + cloud)
# ---------------------------
def get_live_features() -> pd.DataFrame:
    """
    Computes BTC features in real-time using the CoinGecko API for price data
    and the DB for the latest available sentiment data.

    Results are cached for 15 minutes to keep predictions stable within each
    time window and avoid second-by-second drift between local & cloud.
    """
    global _feature_cache

    # --- Return cached result if still fresh ---
    now_ts = time.time()
    if _feature_cache["data"] is not None and (now_ts - _feature_cache["timestamp"]) < FEATURE_CACHE_TTL:
        age = int(now_ts - _feature_cache["timestamp"])
        print(f"[model] Using cached features (age: {age}s / {FEATURE_CACHE_TTL}s TTL)")
        return _feature_cache["data"]

    print("[model] Cache miss — fetching fresh features from CoinGecko...")

    # --- 1. Fetch last 2 days of hourly BTC prices from CoinGecko ---
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": 2, "interval": "hourly"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        # Fallback: try Coinbase for current price only
        raise RuntimeError("CoinGecko API unavailable for live features")

    prices_raw = data.get("prices", [])
    volumes_raw = data.get("total_volumes", [])

    if len(prices_raw) < 25:
        raise RuntimeError("Not enough price data from CoinGecko")

    closes = np.array([p[1] for p in prices_raw])
    volumes = np.array([v[1] for v in volumes_raw])

    # Use the last 25 data points (roughly 24 hours of hourly data)
    closes_24h = closes[-25:]
    volumes_24h = volumes[-25:]

    past_close = closes_24h[0]
    current_close = closes_24h[-1]
    past_volume = volumes_24h[0]
    current_volume = volumes_24h[-1]

    return_24h = (current_close - past_close) / past_close if past_close != 0 else 0.0
    # Coefficient of Variation (std / mean) — unitless, scale-independent
    # This matches the normalization applied during model training
    mean_price = float(np.mean(closes_24h))
    volatility_24h = float(np.std(closes_24h)) / mean_price if mean_price != 0 else 0.0
    volume_change_24h = (current_volume - past_volume) / max(past_volume, 1)

    # --- 2. Get sentiment from DB (last 24h) ---
    now_utc = datetime.now(timezone.utc)
    since = now_utc - timedelta(hours=24)

    try:
        query = text("""
            SELECT sentiment_score
            FROM news_sentiment
            WHERE symbol = 'BTC'
              AND timestamp >= :since
            ORDER BY timestamp ASC
        """)
        df_sent = pd.read_sql(query, engine, params={"since": since})
    except Exception:
        df_sent = pd.DataFrame(columns=["sentiment_score"])

    if len(df_sent) >= 2:
        avg_news_sentiment_24h = float(df_sent["sentiment_score"].mean())
        sentiment_momentum = float(
            df_sent["sentiment_score"].iloc[-1] - df_sent["sentiment_score"].iloc[0]
        )
    elif len(df_sent) == 1:
        avg_news_sentiment_24h = float(df_sent["sentiment_score"].iloc[0])
        sentiment_momentum = 0.0
    else:
        # Neutral sentiment if no data available
        avg_news_sentiment_24h = 0.0
        sentiment_momentum = 0.0

    features = pd.DataFrame([{
        "return_24h": return_24h,
        "volatility_24h": volatility_24h,
        "volume_change_24h": volume_change_24h,
        "avg_news_sentiment_24h": avg_news_sentiment_24h,
        "sentiment_momentum": sentiment_momentum
    }])

    result = features[FEATURE_COLUMNS]

    # --- Store in cache ---
    _feature_cache["data"] = result
    _feature_cache["timestamp"] = time.time()
    print(f"[model] Features cached for {FEATURE_CACHE_TTL // 60} minutes.")

    return result


# ---------------------------
# Fallback: Fetch latest feature row from DB
# ---------------------------
def get_latest_features_from_db():
    """Fallback: reads pre-computed features from DB (may be stale)."""
    query = text("""
        SELECT
            return_24h,
            volatility_24h,
            volume_change_24h,
            avg_news_sentiment_24h,
            sentiment_momentum
        FROM features
        WHERE symbol = 'BTC'
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    df = pd.read_sql(query, engine)

    if df.empty:
        raise RuntimeError("No features available in DB")

    return df[FEATURE_COLUMNS]


# ---------------------------
# Public prediction API
# ---------------------------
def predict_probability() -> float:
    """
    Returns BTC growth probability (0.0 – 1.0).

    Strategy:
    1. Try computing features live from CoinGecko API (same on all environments)
    2. Fall back to DB features if API is unavailable
    """
    model = load_model()

    try:
        X = get_live_features()
        source = "live"
    except Exception as e:
        print(f"[model] Live features failed ({e}), falling back to DB features")
        X = get_latest_features_from_db()
        source = "db"

    print(f"[model] Using {source} features: {X.to_dict(orient='records')}")

    # XGBoost trained on array — drop column names
    prob = float(model.predict_proba(X.values)[0][1])
    print(f"[model] Predicted probability: {prob:.4f}")
    return prob