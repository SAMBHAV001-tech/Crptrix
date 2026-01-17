import os
import requests
from datetime import datetime
from sqlalchemy import text
from database.db import engine

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

def fetch_btc_prices():
    params = {
        "vs_currency": "usd",
        "days": 1
    }

    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": os.getenv("CG-cdnsbrNkMVFMegtydE21Tiu4")
    }

    response = requests.get(
        COINGECKO_URL,
        params=params,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()
    return response.json()

def insert_prices(data):
    prices = data["prices"]
    volumes = data["total_volumes"]

    with engine.begin() as conn:
        for i in range(len(prices)):
            ts = datetime.fromtimestamp(prices[i][0] / 1000)
            price = prices[i][1]
            volume = volumes[i][1]

            exists = conn.execute(
                text("""
                    SELECT 1 FROM prices
                    WHERE symbol = 'BTC' AND timestamp = :ts
                """),
                {"ts": ts}
            ).fetchone()

            if exists:
                continue

            conn.execute(
                text("""
                    INSERT INTO prices
                    (symbol, timestamp, open, high, low, close, volume)
                    VALUES ('BTC', :ts, :p, :p, :p, :p, :v)
                """),
                {"ts": ts, "p": price, "v": volume}
            )

if __name__ == "__main__":
    data = fetch_btc_prices()
    insert_prices(data)
    print("✅ LIVE BTC prices ingested successfully (free tier compatible)")

