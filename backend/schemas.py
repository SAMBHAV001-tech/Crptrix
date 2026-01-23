from pydantic import BaseModel

class PredictionResponse(BaseModel):
    symbol: str
    growth_probability: float
    risk_level: str
