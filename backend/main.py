from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import time

from backend.model import predict_probability

app = FastAPI(title="Crptrix API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # public, read-only API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SUPPORTED_CURRENCIES = ["USD", "INR", "EUR"]

_price_cache = {
    "timestamp": 0,
    "usd": None
}

def get_btc_price_usd() -> float | None:
    import time

    now = time.time()
    if _price_cache["usd"] and now - _price_cache["timestamp"] < 60:
        return _price_cache["usd"]

    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd"},
            timeout=10
        )
        r.raise_for_status()
        price = r.json()["bitcoin"]["usd"]

        _price_cache["usd"] = price
        _price_cache["timestamp"] = now
        return price

    except Exception:
        return None




# ---------------------------
# Risk interpretation
# ---------------------------
def risk_from_probability(p: float) -> str:
    if p >= 0.75:
        return "Low Risk"
    elif p >= 0.55:
        return "Medium Risk"
    else:
        return "High Risk"


# ---------------------------
# Routes
# ---------------------------
@app.get("/")
def health():
    return {"status": "Crptrix backend running"}


@app.get("/predict")
def predict(currency: str = Query("USD")):
    currency = currency.upper()

    if currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Unsupported currency",
                "supported_currencies": SUPPORTED_CURRENCIES
            }
        )

    # --- ML prediction (CORE FEATURE) ---
    prob = predict_probability()   # always works

    # --- CoinGecko price (NON-CRITICAL) ---
    try:
        btc_price = get_btc_price(currency)
    except Exception as e:
        print("CoinGecko error:", e)
        btc_price = None   # graceful degradation

    return {
        "symbol": "BTC",
        "currency": currency,
        "current_price": btc_price,
        "growth_probability": round(prob * 100, 2),
        "risk_level": risk_from_probability(prob),
        "disclaimer": "Probability-based insight. Not financial advice."
    }

