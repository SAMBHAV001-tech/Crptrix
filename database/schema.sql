CREATE TABLE IF NOT EXISTS features (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    return_24h FLOAT,
    volatility_24h FLOAT,
    volume_change_24h FLOAT,

    avg_news_sentiment_24h FLOAT,
    sentiment_momentum FLOAT,

    label INTEGER
);
