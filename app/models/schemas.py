from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


# ─── Requests ────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    disease: Literal["malaria", "flu", "cholera"] = "malaria"
    population_density: float | None = Field(None, ge=0)


class ForecastPredictRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    disease: Literal["malaria", "flu", "cholera"] = "malaria"
    days: int = Field(default=7, ge=1, le=16)
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
    feature_importance: dict[str, float] | None = None

    model_config = {"from_attributes": True}


class ForecastDayResult(BaseModel):
    date: str
    temperature: float
    rainfall: float
    humidity: float
    risk_level: str
    expected_cases: int
    confidence: float


class DiseaseForecastResponse(BaseModel):
    lat: float
    lon: float
    location_name: str | None = None
    disease: str
    days: int
    feature_importance: dict[str, float] | None = None
    forecast: list[ForecastDayResult]


class DiseaseComparisonItem(BaseModel):
    risk_level: str
    expected_cases: int
    confidence: float
    feature_importance: dict[str, float] | None = None


class DiseaseComparisonResponse(BaseModel):
    lat: float
    lon: float
    location_name: str | None = None
    temperature: float
    rainfall: float
    humidity: float
    diseases: dict[str, DiseaseComparisonItem]
    compared_at: datetime


class WeatherResponse(BaseModel):
    lat: float
    lon: float
    location_name: str | None = None
    # Core
    temperature: float
    rainfall: float
    humidity: float
    wind_speed: float
    # Extended
    rain_sum: float | None = None
    wind_gusts: float | None = None
    wind_direction: float | None = None
    precipitation_probability: float | None = None
    weather_code: int | None = None
    uv_index: float | None = None
    apparent_temperature: float | None = None
    cloud_cover: float | None = None
    surface_pressure: float | None = None
    sunshine_duration: float | None = None
    et0_evapotranspiration: float | None = None
    is_day: int | None = None
    sunrise: str | None = None
    sunset: str | None = None
    fetched_at: datetime

    model_config = {"from_attributes": True}


class WeatherHistoryResponse(BaseModel):
    lat: float
    lon: float
    start_date: str
    end_date: str
    records: list[dict]


class ForecastResponse(BaseModel):
    lat: float
    lon: float
    location_name: str | None = None
    days: int
    forecast: list[dict]


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
    last_24h: int = 0
    last_7d: int = 0
    last_30d: int = 0
    trend: str = "stable"
    latest_high_risk_location: str | None = None


class BatchPredictRequest(BaseModel):
    predictions: list[PredictRequest] = Field(..., max_length=20)


class PaginatedPredictions(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[PredictionResponse]
