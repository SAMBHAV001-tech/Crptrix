import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from datetime import timedelta

# --- DB CONNECTION ---
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL environment variable not set")

engine = create_engine(db_url)


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
        volatility_24h = past["close"].std()

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
# Safe Insert (No Duplicates)
# ---------------------------
def save_features(df):
    if df.empty:
        print("ℹ️ No new features to insert")
        return

    records = df.to_dict(orient="records")

    with engine.begin() as conn:
        table = pd.io.sql.SQLTable(
            "features",
            engine,
            frame=df,
            index=False,
            if_exists="append"
        ).table

        stmt = insert(table).on_conflict_do_nothing(
            index_elements=["symbol", "timestamp"]
        )

        conn.execute(stmt, records)

    print(f"✅ Inserted {len(df)} new feature rows (duplicates ignored)")


# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    df = build_features()
    save_features(df)
