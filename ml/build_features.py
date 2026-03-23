import pandas as pd
from datetime import timedelta
from backend.db import engine

# ---------------------------
# Load required data
# ---------------------------
def load_data():
    prices = pd.read_sql(
        "SELECT * FROM prices WHERE symbol = 'BTC' ORDER BY timestamp",
        engine
    )

    sentiment = pd.read_sql(
        "SELECT * FROM news_sentiment WHERE symbol = 'BTC' ORDER BY timestamp",
        engine
    )

    existing_ts = pd.read_sql(
        "SELECT timestamp FROM features WHERE symbol = 'BTC'",
        engine
    )

    prices["timestamp"] = pd.to_datetime(prices["timestamp"])
    sentiment["timestamp"] = pd.to_datetime(sentiment["timestamp"])
    existing_ts["timestamp"] = pd.to_datetime(existing_ts["timestamp"])

    return prices, sentiment, set(existing_ts["timestamp"])


# ---------------------------
# Feature Engineering
# ---------------------------
def build_features():
    prices, sentiment, existing_timestamps = load_data()
    rows = []

    for i in range(24, len(prices) - 24):
        now = prices.iloc[i]["timestamp"]

        # 🔒 IMMUTABILITY GUARD (no recomputation)
        if now in existing_timestamps:
            continue

        past = prices.iloc[i - 24:i]
        future = prices.iloc[i + 24]

        # --- PAST RETURN (FEATURE) ---
        past_return_24h = (
            prices.iloc[i]["close"] - prices.iloc[i - 24]["close"]
        ) / prices.iloc[i - 24]["close"]

        # --- FUTURE RETURN (LABEL ONLY) ---
        future_return_24h = (
            future["close"] - prices.iloc[i]["close"]
        ) / prices.iloc[i]["close"]

        # --- PRICE FEATURES ---
        # Coefficient of Variation (std / mean) — unitless, scale-independent
        # Matches live feature computation in backend/model.py
        mean_price_24h = past["close"].mean()
        volatility_24h = past["close"].std() / mean_price_24h if mean_price_24h != 0 else 0.0

        volume_change_24h = (
            prices.iloc[i]["volume"] - prices.iloc[i - 24]["volume"]
        ) / max(prices.iloc[i - 24]["volume"], 1)

        # --- SENTIMENT FEATURES ---
        sent_window = sentiment[
            (sentiment["timestamp"] >= now - timedelta(hours=24)) &
            (sentiment["timestamp"] <= now)
        ]

        if len(sent_window) < 2:
            continue

        avg_sentiment = sent_window["sentiment_score"].mean()

        sentiment_momentum = (
            sent_window["sentiment_score"].iloc[-1] -
            sent_window["sentiment_score"].iloc[0]
        )

        # --- LABEL ---
        label = 1 if future_return_24h > 0.01 else 0

        rows.append({
            "symbol": "BTC",
            "timestamp": now,
            "return_24h": past_return_24h,
            "volatility_24h": volatility_24h,
            "volume_change_24h": volume_change_24h,
            "avg_news_sentiment_24h": avg_sentiment,
            "sentiment_momentum": sentiment_momentum,
            "label": label
        })

    return pd.DataFrame(rows)


# ---------------------------
# Save Features
# ---------------------------
def save_features(df):
    if df.empty:
        print("No features to save.")
        return

    df.to_sql(
        name="features",
        con=engine,
        if_exists="append",   # do NOT replace
        index=False,
        method="multi"
    )

    print(f"✅ Inserted {len(df)} feature rows")


# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    df = build_features()
    save_features(df)