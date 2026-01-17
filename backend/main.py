from fastapi import FastAPI, Query
import requests

app = FastAPI(title="Crptrix API")

SUPPORTED_CURRENCIES = ["USD", "INR", "EUR"]

def get_btc_price(currency: str = "USD") -> float:
    """
    Fetch current BTC price in selected currency using CoinGecko
    """
    currency = currency.lower()

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": currency
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()["bitcoin"][currency]


@app.get("/")
def health():
    return {"status": "Crptrix backend running"}


@app.get("/predict")
def predict(currency: str = Query("USD")):
    currency = currency.upper()

    if currency not in SUPPORTED_CURRENCIES:
        return {
            "error": "Unsupported currency",
            "supported_currencies": SUPPORTED_CURRENCIES
        }

    # Placeholder values until ML model is trained
    growth_probability = None
    risk_level = "unknown"

    btc_price = get_btc_price(currency)

    return {
        "symbol": "BTC",
        "currency": currency,
        "current_price": btc_price,
        "growth_probability": growth_probability,
        "risk_level": risk_level,
        "note": "Model not trained yet"
    }
