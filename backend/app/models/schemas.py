from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    disease: Literal["malaria", "flu", "cholera"] = "malaria"
    population_density: float | None = Field(None, ge=0)


class PredictionResponse(BaseModel):
    lat: float
    lon: float
    location_name: str | None
    disease: str
    risk_level: str
    expected_cases: int
    confidence: float
    temperature: float
    rainfall: float
    humidity: float
    predicted_at: datetime

    model_config = {"from_attributes": True}


class WeatherResponse(BaseModel):
    lat: float
    lon: float
    temperature: float
    rainfall: float
    humidity: float
    wind_speed: float
    fetched_at: datetime

    model_config = {"from_attributes": True}
