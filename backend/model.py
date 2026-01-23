import os
import joblib
import pandas as pd
from sqlalchemy import text
from backend.db import engine

# ---------------------------
# Model path (Docker-safe)
# ---------------------------
MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "xgboost_model.joblib"
)

# ---------------------------
# Lazy-loaded model (safe)
# ---------------------------
_model = None

def load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(f"Model file not found at {MODEL_PATH}")
        _model = joblib.load(MODEL_PATH)
    return _model


# ---------------------------
# Feature columns (ORDER MATTERS)
# ---------------------------
FEATURE_COLUMNS = [
    "return_24h",
    "volatility_24h",
    "volume_change_24h",
    "avg_news_sentiment_24h",
    "sentiment_momentum",
]


# ---------------------------
# Fetch latest feature row
# ---------------------------
def get_latest_features():
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
        raise RuntimeError("No features available for prediction")

    return df[FEATURE_COLUMNS]


# ---------------------------
# Public prediction API
# ---------------------------
def predict_probability():
    model = load_model()     # ✅ THIS LINE FIXES EVERYTHING
    X = get_latest_features()
    prob = model.predict_proba(X)[0][1]
    return float(prob)
