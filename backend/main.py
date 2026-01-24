from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

from backend.model import predict_probability

app = FastAPI(title="Crptrix API")

# -----------------------
# CORS
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # public frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# CoinGecko (USD ONLY)
# -----------------------
def get_btc_price_usd():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd"
    }

    r = requests.get(url, params=params, timeout=10)

    if r.status_code != 200:
        raise RuntimeError("CoinGecko rate-limited or unavailable")

    return r.json()["bitcoin"]["usd"]


# -----------------------
# Risk interpretation
# -----------------------
def risk_from_probability(p):
    if p >= 0.75:
        return "Low Risk"
    elif p >= 0.55:
        return "Medium Risk"
    return "High Risk"


# -----------------------
# Routes
# -----------------------
@app.get("/")
def health():
    return {"status": "Crptrix backend running"}


@app.get("/predict")
def predict():
    # --- ML prediction (always works) ---
    prob = predict_probability()  # e.g. 0.04

    # --- BTC price in USD (non-critical) ---
    try:
        btc_price_usd = get_btc_price_usd()
    except Exception:
        btc_price_usd = None  # graceful degradation

    return {
        "symbol": "BTC",
        "price_usd": btc_price_usd,
        "growth_probability": round(prob * 100, 2),  # percentage for UI
        "risk_level": risk_from_probability(prob),
    }
