from fastapi import FastAPI
from backend.db import engine

app = FastAPI(title="Crptrix API")

@app.get("/")
def health():
    return {"status": "Crptrix backend running"}

@app.get("/predict")
def predict():
    return {
        "symbol": "BTC",
        "growth_probability": None,
        "message": "Model not trained yet"
    }
