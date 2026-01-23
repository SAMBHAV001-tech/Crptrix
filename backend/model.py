import joblib
import pandas as pd
from sqlalchemy import text
from backend.db import engine

MODEL_PATH = "ml/models/xgb_btc.pkl"

model = joblib.load(MODEL_PATH)

FEATURE_COLUMNS = [
    "return_24h",
    "volatility_24h",
    "volume_change_24h",
    "avg_news_sentiment_24h",
    "sentiment_momentum",
]

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
        raise RuntimeError("No features available")

    return df[FEATURE_COLUMNS]

def predict_probability():
    X = get_latest_features()
    prob = model.predict_proba(X)[0][1]
    return float(prob)
