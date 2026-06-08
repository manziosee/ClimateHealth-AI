from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.cache import init_redis, close_redis
from app.core.database import engine, Base
from app.core.middleware import rate_limit_middleware
from app.api.v1 import predictions, weather, health, locations, stats, disease


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await close_redis()


# ─── Tag descriptions shown in Swagger UI ────────────────────────────────────
TAGS_METADATA = [
    {
        "name": "predictions",
        "description": (
            "Run AI-powered disease outbreak predictions for any global coordinate. "
            "Fetches real-time weather from **Open-Meteo**, auto-resolves population density "
            "from **World Bank**, and runs an **XGBoost + Random Forest ensemble** to return "
            "risk level, expected cases, and confidence score."
        ),
    },
    {
        "name": "weather",
        "description": (
            "Fetch current weather conditions, 7–16 day forecasts, and historical archive data "
            "from **Open-Meteo** for any lat/lon worldwide. No API key required. "
            "Weather snapshots are persisted to the DB for future LSTM training."
        ),
    },
    {
        "name": "disease",
        "description": (
            "Query disease surveillance records from the **WHO Global Health Observatory (GHO)** "
            "OData API. Supports malaria, cholera, and influenza indicators. "
            "Results are cached in Redis for 24 hours."
        ),
    },
    {
        "name": "stats",
        "description": (
            "Aggregate statistics over all stored predictions — "
            "total count, risk breakdown, per-disease distribution, and average model confidence."
        ),
    },
    {
        "name": "locations",
        "description": (
            "Search locations by name using the **Open-Meteo Geocoding API**. "
            "Returns lat/lon, country, region, and population for up to 20 results."
        ),
    },
    {
        "name": "health",
        "description": "Service health check — returns DB and Redis connectivity status with latency measurements.",
    },
]


app = FastAPI(
    title="ClimateHealth AI",
    summary="Global AI-powered disease outbreak prediction platform",
    description="""
## Overview
**ClimateHealth AI** predicts disease outbreaks (malaria, flu, cholera) weeks in advance
by correlating real-time weather data with epidemiological patterns using XGBoost + Random Forest models.

## Data Sources
| Source | Data | Auth |
|--------|------|------|
| [Open-Meteo](https://open-meteo.com/) | Weather forecasts + historical archive | Free, no key |
| [WHO GHO OData](https://ghoapi.azureedge.net/api/) | Disease surveillance records | Free |
| [World Bank V2](https://api.worldbank.org/v2/) | Population density + health indicators | Free |
| [Nominatim OSM](https://nominatim.org/) | Reverse geocoding | Free |

## ML Models
- **Phase 1 (current):** XGBoost + Random Forest ensemble — tabular features
- **Phase 2 (planned):** LSTM / Prophet — time-series 1–8 week forecasting

## Rate Limiting
`60 requests / minute` per IP address (sliding window via Redis).

## Caching
| Resource | TTL |
|----------|-----|
| Weather | 30 min |
| Predictions | 1 hour |
| Disease data | 24 hours |
""",
    version="1.0.0",
    contact={
        "name":  "ClimateHealth AI",
        "url":   "https://github.com/manziosee/ClimateHealth-AI",
        "email": "osee@climatehealth.ai",
    },
    license_info={
        "name": "MIT License",
        "url":  "https://github.com/manziosee/ClimateHealth-AI/blob/main/LICENSE",
    },
    openapi_tags=TAGS_METADATA,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)

PREFIX = "/api/v1"
app.include_router(predictions.router, prefix=PREFIX)
app.include_router(weather.router,     prefix=PREFIX)
app.include_router(locations.router,   prefix=PREFIX)
app.include_router(stats.router,       prefix=PREFIX)
app.include_router(disease.router,     prefix=PREFIX)
app.include_router(health.router)


# ─── Custom OpenAPI schema — adds server URLs and example responses ───────────
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        summary=app.summary,
        description=app.description,
        contact=app.contact,
        license_info=app.license_info,
        tags=TAGS_METADATA,
        routes=app.routes,
    )

    schema["servers"] = [
        {"url": "http://localhost",       "description": "Docker (Nginx proxy)"},
        {"url": "http://localhost:8000",  "description": "Local FastAPI dev server"},
    ]

    # Mark all string responses as UTF-8
    schema.setdefault("info", {})["x-logo"] = {
        "url": "https://img.shields.io/badge/ClimateHealth_AI-0ea5e9?style=for-the-badge"
    }

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
