from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

from backend.model import predict_probability, get_live_features, get_latest_features_from_db

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

# backend/main.py
import time

_price_cache = {
    "value": None,
    "timestamp": 0
}

def get_btc_price_usd_cached():
    now = time.time()
    if _price_cache["value"] and now - _price_cache["timestamp"] < 300:
        return _price_cache["value"]  # reuse for 5 minutes

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin", "vs_currencies": "usd"}
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        price = r.json()["bitcoin"]["usd"]
    except Exception:
        # Fallback to Coinbase API (Binance blocks Render's US IP addresses)
        fallback_url = "https://api.coinbase.com/v2/prices/spot?currency=USD"
        r = requests.get(fallback_url, timeout=5)
        r.raise_for_status()
        price = float(r.json()["data"]["amount"])

    _price_cache["value"] = price
    _price_cache["timestamp"] = now
    return price



# -----------------------
# Risk interpretation
# -----------------------
def risk_from_probability(p):
    if p >= 0.60:
        return "Low Risk"
    elif p >= 0.40:
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
    # --- ML prediction (live features from CoinGecko) ---
    try:
        prob = predict_probability()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Prediction unavailable: {str(e)}"
        )

    # --- BTC price in USD (non-critical) ---
    try:
        btc_price_usd = get_btc_price_usd_cached()
    except Exception:
        btc_price_usd = None  # graceful degradation

    return {
        "symbol": "BTC",
        "price_usd": btc_price_usd,
        "growth_probability": round(prob * 100, 2),  # percentage for UI
        "risk_level": risk_from_probability(prob),
    }


@app.get("/debug")
def debug():
    """Developer endpoint — returns raw live features for diagnostics."""
    try:
        features = get_live_features()
        source = "live"
    except Exception as e:
        try:
            features = get_latest_features_from_db()
            source = "db_fallback"
        except Exception as e2:
            raise HTTPException(status_code=503, detail=f"Live: {e} | DB: {e2}")

    return {
        "source": source,
        "features": features.to_dict(orient="records")[0]
    }
