from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


# ─── Requests ────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    disease: Literal["malaria", "flu", "cholera"] = "malaria"
    population_density: float | None = Field(None, ge=0)


# ─── Responses ───────────────────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    id: int | None = None
    lat: float
    lon: float
    location_name: str | None = None
    disease: str
    risk_level: str
    expected_cases: int
    confidence: float
    temperature: float
    rainfall: float
    humidity: float
    wind_speed: float | None = None
    population_density: float | None = None
    predicted_at: datetime

    model_config = {"from_attributes": True}


class WeatherResponse(BaseModel):
    lat: float
    lon: float
    location_name: str | None = None
    temperature: float
    rainfall: float
    humidity: float
    wind_speed: float
    fetched_at: datetime

    model_config = {"from_attributes": True}


class WeatherHistoryResponse(BaseModel):
    lat: float
    lon: float
    start_date: str
    end_date: str
    records: list[dict]


class LocationResult(BaseModel):
    name: str | None
    country: str | None
    admin1: str | None
    lat: float | None
    lon: float | None
    population: int | None


class DiseaseDataResponse(BaseModel):
    disease: str
    country: str | None
    records: list[dict]


class StatsResponse(BaseModel):
    total_predictions: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    by_disease: dict[str, int]
    avg_confidence: float
    most_predicted_disease: str | None


class PaginatedPredictions(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[PredictionResponse]
