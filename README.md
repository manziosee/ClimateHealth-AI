<div align="center">

<img src="https://img.shields.io/badge/ClimateHealth_AI-Global_Outbreak_Forecasting-0ea5e9?style=for-the-badge&logo=globe&logoColor=white" alt="ClimateHealth AI" />

<br/>
<br/>

<p align="center">
  <strong>AI-powered global disease outbreak prediction using real-time weather, environmental, and demographic data.</strong><br/>
  Predicts malaria, influenza, and cholera outbreaks weeks in advance — anywhere in the world.
</p>

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-FF6600?style=flat-square&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![Fly.io](https://img.shields.io/badge/Deployed-Fly.io-8B5CF6?style=flat-square&logo=flydotio&logoColor=white)](https://fly.io/)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Live API](#live-api)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Data Sources](#data-sources)
- [ML Models](#ml-models)
- [API Reference](#api-reference)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [CI/CD](#cicd)
- [Roadmap](#roadmap)

---

## Overview

Health organizations typically **react** after disease cases rise rather than predicting outbreaks beforehand. **ClimateHealth AI** solves this by correlating real-time weather patterns with historical disease data to forecast outbreak risk weeks in advance — for any location on Earth.

| Weather Signal | Disease Impact |
|---|---|
| High rainfall | More mosquito breeding → Malaria spike |
| High humidity | Respiratory infections spread faster |
| Temperature drop | Influenza outbreaks increase |
| Flooding events | Waterborne diseases (Cholera) surge |

**Key capabilities:**
- **Global coverage** — predict for any lat/lon worldwide, no region restrictions
- **Real-time weather** — live data from Open-Meteo API (no API key required)
- **ML ensemble** — XGBoost + Random Forest with feature importance explanations
- **Risk scoring** — Low / Medium / High outbreak classification with confidence scores
- **7-day forecast** — day-by-day disease risk ribbon for the coming week
- **Disease comparison** — malaria, flu, and cholera side-by-side in one call
- **CSV export** — download predictions for field use by NGOs and health workers
- **Fully deployed** — Fly.io + Neon PostgreSQL + Upstash Redis

---

## Live API

| URL | Description |
|---|---|
| [https://climatehealth-ai.fly.dev/](https://climatehealth-ai.fly.dev/) | API root — links to all endpoints |
| [https://climatehealth-ai.fly.dev/health](https://climatehealth-ai.fly.dev/health) | DB + Redis connectivity status |
| [https://climatehealth-ai.fly.dev/swagger](https://climatehealth-ai.fly.dev/swagger) | Redirects to Swagger UI |
| [https://climatehealth-ai.fly.dev/api/docs](https://climatehealth-ai.fly.dev/api/docs) | Swagger UI (interactive docs) |
| [https://climatehealth-ai.fly.dev/api/redoc](https://climatehealth-ai.fly.dev/api/redoc) | ReDoc documentation |

**Local development:**
```
http://localhost:8000           → API root
http://localhost:8000/api/docs  → Swagger UI
http://localhost:8000/health    → Health check
```

---

## Tech Stack

### Backend
| Technology | Purpose | Version |
|---|---|---|
| **Python** | Core language | 3.13 |
| **FastAPI** | REST API framework | 0.115 |
| **SQLAlchemy** | Async ORM | 2.0 |
| **Neon PostgreSQL** | Serverless database | Latest |
| **Upstash Redis** | Caching + rate limiting | 5.0 |
| **Alembic** | DB migrations | 1.13 |

### Machine Learning
| Technology | Purpose | Version |
|---|---|---|
| **XGBoost** | Outbreak regression models | 2.1 |
| **scikit-learn** | Feature pipeline + Random Forest | 1.6 |
| **Pandas** | Data manipulation | 2.2 |
| **NumPy** | Numerical computing | 2.1 |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Fly.io** | Cloud deployment |
| **Docker + Compose** | Local containerization |
| **GitHub Actions** | CI/CD — lint, smoke test, deploy, monthly model retraining |

---

## System Architecture

```
                    ┌──────────────────────────────────────┐
                    │          Client / Consumer            │
                    │  (browser, curl, health app, NGO)    │
                    └──────────────┬───────────────────────┘
                                   │ HTTPS
                    ┌──────────────▼───────────────────────┐
                    │         Fly.io (Production)           │
                    │                                       │
                    │   FastAPI 1.1.0  (Python 3.13)        │
                    │                                       │
                    │  POST /api/v1/predictions             │
                    │  POST /api/v1/predictions/batch       │
                    │  POST /api/v1/predictions/forecast    │
                    │  GET  /api/v1/predictions/compare     │
                    │  GET  /api/v1/predictions/export      │
                    │  GET  /api/v1/weather[/forecast|/history]
                    │  GET  /api/v1/disease                 │
                    │  GET  /api/v1/stats                   │
                    │  GET  /api/v1/locations/search        │
                    │  GET  /health                         │
                    └──────┬──────────────┬────────────────┘
                           │              │
           ┌───────────────▼──┐   ┌───────▼────────────────┐
           │  Upstash Redis    │   │  Neon PostgreSQL        │
           │                  │   │                          │
           │  Weather cache   │   │  predictions             │
           │  Predictions     │   │  weather_snapshots       │
           │  Rate limiting   │   │  disease_records         │
           └───────────────────┘   │  locations (geocache)   │
                           │       │  model_metrics           │
                           │       └────────────────────────┘
                           │
           ┌───────────────▼────────────────────────────────┐
           │            External Data Sources                │
           │                                                 │
           │  Open-Meteo API      weather + forecast + archive│
           │  WHO GHO API         disease surveillance data   │
           │  Nominatim OSM       reverse geocoding           │
           │  Open-Meteo Geo      city/region search          │
           │  World Bank API      population density          │
           └─────────────────────────────────────────────────┘
```

### Redis Caching Strategy

| Cache Key | TTL | Description |
|---|---|---|
| `weather:{lat}:{lon}` | 30 min | Weather fetch per location |
| `forecast:{lat}:{lon}:{days}` | 30 min | Multi-day forecast |
| `prediction:{disease}:{lat}:{lon}` | 1 hour | Prediction result |
| `forecast_pred:{disease}:{lat}:{lon}:{days}` | 1 hour | 7-day disease forecast |
| `compare:{lat}:{lon}` | 1 hour | Disease comparison result |
| `wb:pop:{country_code}` | 24 hours | World Bank population density |
| `disease:{disease}:{country}` | 24 hours | WHO GHO data |
| `history:{lat}:{lon}:{start}:{end}` | 24 hours | Historical weather (immutable) |
| `rate:{ip}` | 1 min | Sliding window rate limiter (60 req/min) |

---

## Project Structure

```
ClimateHealth-AI/
├── .github/
│   └── workflows/
│       ├── ci-backend.yml      # Lint, import checks, ML pipeline smoke test, deploy to Fly.io
│       └── train-models.yml    # Monthly model retraining + GitHub Release with .pkl files
├── app/
│   ├── main.py                 # FastAPI entry, lifespan, middleware, root routes
│   ├── api/
│   │   └── v1/
│   │       ├── predictions.py  # POST/GET/DELETE + batch, forecast, compare, export
│   │       ├── weather.py      # Current weather, forecast (1–16d), historical archive
│   │       ├── locations.py    # City/region search via Open-Meteo Geocoding
│   │       ├── stats.py        # Aggregate prediction statistics + model metrics
│   │       ├── disease.py      # WHO GHO disease surveillance data
│   │       └── health.py       # DB + Redis health check with latency
│   ├── core/
│   │   ├── config.py           # Pydantic settings from .env
│   │   ├── database.py         # Async SQLAlchemy + Neon PostgreSQL
│   │   ├── cache.py            # Async Redis client with graceful NoopRedis fallback
│   │   └── middleware.py       # IP rate limiting (60 req/min, sliding window)
│   ├── models/
│   │   ├── db_models.py        # ORM: Prediction, WeatherSnapshot, DiseaseRecord, LocationCache, ModelMetrics
│   │   └── schemas.py          # Pydantic request/response schemas
│   ├── services/
│   │   ├── weather.py          # Open-Meteo client (current + forecast + archive)
│   │   ├── disease.py          # WHO GHO OData API client
│   │   ├── geocoding.py        # Nominatim reverse geocoding with DB cache
│   │   ├── predictor.py        # ML ensemble inference + feature importance + heuristic fallback
│   │   └── worldbank.py        # World Bank population density API
│   └── ml/
│       ├── pipeline.py         # Feature engineering (24 features)
│       ├── data_generator.py   # Synthetic training data generator
│       ├── train.py            # XGBoost + Random Forest training + DB metrics logging
│       ├── model_registry.py   # Auto-download models from GitHub Releases
│       └── saved_models/       # Trained .pkl files (6 models) + metrics.json
│           ├── malaria_xgb.pkl
│           ├── malaria_rf.pkl
│           ├── flu_xgb.pkl
│           ├── flu_rf.pkl
│           ├── cholera_xgb.pkl
│           ├── cholera_rf.pkl
│           └── metrics.json
├── alembic/
│   └── versions/
│       ├── 0001_initial_tables.py
│       ├── 0002_add_wind_speed_and_indexes.py
│       └── 0003_add_disease_records_locations_model_metrics.py
├── .env.example
├── alembic.ini
├── docker-compose.yml          # Local stack: app + redis, port 8000
├── Dockerfile
├── fly.toml                    # Fly.io deployment config
├── requirements.txt
└── README.md
```

---

## Data Sources

| Source | Data | Cost |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | Temperature, rainfall, humidity, wind speed, UV index, ET₀, precipitation probability — forecast + historical archive (back to 1940) | Free, no key |
| [WHO GHO API](https://www.who.int/data/gho/info/gho-odata-api) | Malaria and cholera case records by country and year | Free |
| [Nominatim / OSM](https://nominatim.org/) | Reverse geocoding (lat/lon → city name + country code) | Free |
| [Open-Meteo Geocoding](https://open-meteo.com/en/docs/geocoding-api) | City name → lat/lon search | Free |
| [World Bank API](https://api.worldbank.org/v2/) | Population density by country | Free |

---

## ML Models

### Phase 1 — XGBoost + Random Forest Ensemble (current)

Both models are trained per disease and averaged for improved stability. Every prediction includes a **feature importance breakdown** showing which variables drove the result.

**Input features (24 total):**

| Feature | Source | Notes |
|---|---|---|
| `temperature` | Open-Meteo | Avg of daily max/min (°C) |
| `rainfall` | Open-Meteo | Daily precipitation sum (mm) |
| `humidity` | Open-Meteo | Relative humidity (%) |
| `wind_speed` | Open-Meteo | Daily max wind (km/h) |
| `population_density` | World Bank | Auto-resolved by country code |
| `uv_index` | Open-Meteo | Daily max UV |
| `et0_evapotranspiration` | Open-Meteo | Evapotranspiration mm/day |
| `precipitation_probability` | Open-Meteo | Max daily % |
| `apparent_temperature` | Open-Meteo | Feels-like temperature (°C) |
| `month_sin / month_cos` | System date | Cyclical month encoding |
| `rain_humidity` | Derived | rainfall × humidity / 100 |
| `temp_humidity` | Derived | temperature × humidity / 100 |
| `rain_temp` | Derived | rainfall × temperature |
| `pop_rain` | Derived | population_density × rainfall |
| `heat_index` | Derived | Apparent temperature proxy |
| `flood_risk` | Derived | Binary: rainfall > 100 mm |
| `high_humidity` | Derived | Binary: humidity > 75% |
| `high_uv` | Derived | Binary: uv_index > 7 |
| `uv_temp` | Derived | uv_index × temperature |
| `drought_stress` | Derived | Binary: ET₀ > 5 mm/day |
| `rain_prob_rain` | Derived | precipitation_probability × rainfall / 100 |
| `feels_like_diff` | Derived | apparent_temperature − temperature |

**Training:** 8,000 synthetic samples per disease, 80/20 train/test split.

**Model metrics (latest):**

| Disease | Model | MAE | R² |
|---|---|---|---|
| Malaria | XGBoost | ~4.1 | ~0.975 |
| Malaria | Random Forest | ~4.4 | ~0.972 |
| Flu | XGBoost | ~2.4 | ~0.889 |
| Flu | Random Forest | ~2.4 | ~0.885 |
| Cholera | XGBoost | ~3.5 | ~0.997 |
| Cholera | Random Forest | ~3.5 | ~0.997 |

**Risk classification:**

| Disease | Low | Medium | High |
|---|---|---|---|
| Malaria | < 40 cases | 40–100 | > 100 |
| Flu | < 25 cases | 25–70 | > 70 |
| Cholera | < 10 cases | 10–35 | > 35 |

### Phase 2 — Time-series Forecasting (planned)
- **LSTM** — sequential outbreak progression
- **Prophet** — seasonal decomposition
- **Temporal Fusion Transformer** — multi-horizon 1–8 week forecasting

---

## API Reference

All endpoints are available at `https://climatehealth-ai.fly.dev` or via [Swagger UI](https://climatehealth-ai.fly.dev/api/docs).

### `POST /api/v1/predictions`
Run a disease outbreak prediction for any global location. Fetches live weather from Open-Meteo, auto-resolves population density from World Bank, and runs the XGBoost + RF ensemble.

**Request:**
```json
{
  "lat": -1.9403,
  "lon": 29.8739,
  "disease": "malaria",
  "population_density": 620
}
```

**Response:**
```json
{
  "id": 42,
  "lat": -1.9403,
  "lon": 29.8739,
  "location_name": "Kigali, Rwanda",
  "disease": "malaria",
  "risk_level": "High",
  "expected_cases": 145,
  "confidence": 0.88,
  "temperature": 28.2,
  "rainfall": 210.0,
  "humidity": 85.0,
  "wind_speed": 12.4,
  "population_density": 620.0,
  "predicted_at": "2025-01-15T10:30:00",
  "feature_importance": {
    "rain_humidity": 0.312,
    "rainfall": 0.218,
    "temperature": 0.154,
    "humidity": 0.127,
    "pop_rain": 0.089
  }
}
```

---

### `POST /api/v1/predictions/batch`
Run up to 20 predictions in one request. Results are cached individually.

---

### `POST /api/v1/predictions/forecast`
Predict disease risk for each of the next 1–16 days using Open-Meteo's weather forecast. Returns a per-day risk ribbon.

**Request:**
```json
{
  "lat": 6.3703,
  "lon": 2.3912,
  "disease": "malaria",
  "days": 7
}
```

**Response:**
```json
{
  "lat": 6.3703,
  "lon": 2.3912,
  "location_name": "Cotonou, Benin",
  "disease": "malaria",
  "days": 7,
  "feature_importance": { "rain_humidity": 0.31, "rainfall": 0.22, "..." : 0.0 },
  "forecast": [
    { "date": "2025-01-15", "temperature": 29.1, "rainfall": 12.0, "humidity": 78.4, "risk_level": "Medium", "expected_cases": 68, "confidence": 0.84 },
    { "date": "2025-01-16", "temperature": 30.2, "rainfall": 45.0, "humidity": 84.2, "risk_level": "High",   "expected_cases": 112, "confidence": 0.81 }
  ]
}
```

---

### `GET /api/v1/predictions/compare`
Run malaria, flu, and cholera predictions simultaneously for one location. Single weather fetch, three model results.

**Query params:** `lat`, `lon`, `population_density` (optional)

**Response:**
```json
{
  "lat": 5.3599,
  "lon": -4.0082,
  "location_name": "Abidjan, Ivory Coast",
  "temperature": 27.8,
  "rainfall": 95.0,
  "humidity": 82.0,
  "compared_at": "2025-01-15T10:30:00Z",
  "diseases": {
    "malaria":  { "risk_level": "High",   "expected_cases": 118, "confidence": 0.83, "feature_importance": { "..." : 0.0 } },
    "flu":      { "risk_level": "Low",    "expected_cases": 8,   "confidence": 0.91, "feature_importance": { "..." : 0.0 } },
    "cholera":  { "risk_level": "Medium", "expected_cases": 28,  "confidence": 0.87, "feature_importance": { "..." : 0.0 } }
  }
}
```

---

### `GET /api/v1/predictions/export`
Download predictions as a CSV file. Filterable by disease and risk level.

**Query params:** `disease`, `risk_level`, `limit` (max 5000)

**Response:** `text/csv` file download — useful for NGOs, field health workers, and researchers.

---

### `GET /api/v1/predictions`
List stored predictions with pagination.

| Param | Type | Description |
|---|---|---|
| `disease` | string | Filter: `malaria`, `flu`, `cholera` |
| `risk_level` | string | Filter: `Low`, `Medium`, `High` |
| `limit` | int | Max results (default: 50, max: 200) |
| `offset` | int | Pagination offset |

---

### `GET /api/v1/predictions/{id}` · `DELETE /api/v1/predictions/{id}`
Get or delete a single prediction by ID.

---

### `GET /api/v1/weather`
Fetch current weather + today's summary for any coordinate.

| Param | Type | Description |
|---|---|---|
| `lat` | float | Latitude (-90 to 90) |
| `lon` | float | Longitude (-180 to 180) |

---

### `GET /api/v1/weather/forecast`
Fetch multi-day forecast (up to 16 days). Includes temperature, rainfall, humidity, wind, UV, ET₀.

| Param | Type | Description |
|---|---|---|
| `lat` | float | Latitude |
| `lon` | float | Longitude |
| `days` | int | Forecast days (default: 7, max: 16) |

---

### `GET /api/v1/weather/history`
Fetch historical daily weather from the Open-Meteo archive (back to 1940).

| Param | Type | Description |
|---|---|---|
| `lat` | float | Latitude |
| `lon` | float | Longitude |
| `start_date` | string | `YYYY-MM-DD` |
| `end_date` | string | `YYYY-MM-DD` |

---

### `GET /api/v1/locations/search`
Search locations by name. Returns lat/lon, country, region, and population.

| Param | Type | Description |
|---|---|---|
| `q` | string | City or region name (min 2 chars) |
| `count` | int | Max results (default: 5, max: 20) |

---

### `GET /api/v1/stats`
Aggregate statistics over all stored predictions — totals, risk breakdown, per-disease counts, average confidence, and 24h/7d/30d trend.

### `GET /api/v1/stats/model-metrics`
Training metrics for all models (MAE, R², sample counts). Falls back to `metrics.json` if DB is empty.

---

### `GET /api/v1/disease`
Query WHO GHO disease surveillance records.

| Param | Type | Description |
|---|---|---|
| `disease` | string | `malaria`, `flu`, or `cholera` |
| `country` | string | ISO 2-letter country code (optional) |

---

### `GET /health`
Returns DB and Redis connectivity status with latency measurements.

```json
{
  "status": "ok",
  "environment": "production",
  "version": "1.1.0",
  "uptime_s": 3600.0,
  "services": {
    "database": { "ok": true, "latency_ms": 12.4 },
    "redis":    { "ok": true, "latency_ms": 3.1 }
  },
  "models": {
    "all_loaded": true,
    "files": { "malaria_xgb.pkl": true, "...": true }
  }
}
```

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Neon account](https://neon.tech/) (free tier)

### 1. Clone & configure

```bash
git clone https://github.com/manziosee/ClimateHealth-AI.git
cd ClimateHealth-AI

cp .env.example .env
# Edit .env — fill in DATABASE_URL and REDIS_URL
```

### 2. Train ML models (first time only)

```bash
pip install -r requirements.txt
python -m app.ml.train
```

### 3. Run with Docker

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/api/docs |
| Health Check | http://localhost:8000/health |

### 4. Test the API

```bash
# Single prediction
curl -X POST http://localhost:8000/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"lat": -1.9403, "lon": 29.8739, "disease": "malaria"}'

# 7-day forecast
curl -X POST http://localhost:8000/api/v1/predictions/forecast \
  -H "Content-Type: application/json" \
  -d '{"lat": -1.9403, "lon": 29.8739, "disease": "malaria", "days": 7}'

# Disease comparison
curl "http://localhost:8000/api/v1/predictions/compare?lat=-1.9403&lon=29.8739"

# Export CSV
curl "http://localhost:8000/api/v1/predictions/export?disease=malaria" -o predictions.csv
```

---

## Deployment

The API is deployed on **Fly.io** with **Neon PostgreSQL** and **Upstash Redis**.

### Manual deploy

```bash
# First-time setup
flyctl apps create climatehealth-ai

# Set secrets
flyctl secrets set \
  DATABASE_URL="postgresql+asyncpg://..." \
  REDIS_URL="redis://..." \
  SECRET_KEY="your-secret-key" \
  APP_ENV="production"

# Deploy
flyctl deploy --remote-only
```

### Auto-deploy via GitHub Actions

Any push to `main` that modifies `app/**`, `requirements.txt`, or `Dockerfile` automatically triggers the CI pipeline which lints, smoke-tests, and deploys to Fly.io.

**Required GitHub secret:** `FLY_API_TOKEN`
```bash
flyctl tokens create deploy -a climatehealth-ai
```

### Live endpoints

| URL | Description |
|---|---|
| https://climatehealth-ai.fly.dev/ | API root |
| https://climatehealth-ai.fly.dev/health | Service health |
| https://climatehealth-ai.fly.dev/api/docs | Swagger UI |
| https://climatehealth-ai.fly.dev/api/redoc | ReDoc |

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | Neon PostgreSQL async connection string | `postgresql+asyncpg://user:pass@host/db?ssl=require` |
| `REDIS_URL` | Redis connection string | `redis://default:pass@host:6379` |
| `APP_ENV` | Environment name | `development` / `production` |
| `SECRET_KEY` | App secret key | Random 32-char string |
| `OPEN_METEO_BASE_URL` | Open-Meteo forecast API | `https://api.open-meteo.com/v1` |
| `OPEN_METEO_ARCHIVE_URL` | Open-Meteo archive API | `https://archive-api.open-meteo.com/v1` |
| `WHO_BASE_URL` | WHO GHO OData API | `https://ghoapi.azureedge.net/api` |
| `WORLD_BANK_BASE_URL` | World Bank API | `https://api.worldbank.org/v2` |
| `WEATHER_CACHE_TTL` | Weather cache TTL (seconds) | `1800` |
| `PREDICTION_CACHE_TTL` | Prediction cache TTL (seconds) | `3600` |
| `DISEASE_CACHE_TTL` | WHO data cache TTL (seconds) | `86400` |

Copy `.env.example` to `.env` and fill in `DATABASE_URL` and `REDIS_URL`. All other variables have working defaults.

---

## CI/CD

| Workflow | Trigger | Steps |
|---|---|---|
| `ci-backend.yml` | Push to `main`/`dev`, PR to `main` | Install deps → verify all imports → smoke-test ML pipeline → verify FastAPI loads → deploy to Fly.io |
| `train-models.yml` | 1st of every month (or manual) | Train XGBoost + RF for all diseases → upload artifacts → create GitHub Release with `.pkl` files |

Model `.pkl` files are published as GitHub Release assets and automatically downloaded by `model_registry.py` on each Fly.io deploy (Fly.io filesystem is ephemeral — models are also baked into the Docker image at build time as a primary path).

---

## Roadmap

- [x] Phase 1 — XGBoost + Random Forest ensemble (malaria, flu, cholera)
- [x] Real-time weather ingestion (Open-Meteo) — 24 features
- [x] Redis caching + IP rate limiting + graceful fallback
- [x] Neon PostgreSQL + async SQLAlchemy + Alembic migrations
- [x] Fly.io production deployment + GitHub Actions CI/CD
- [x] World Bank population density auto-resolution
- [x] WHO GHO disease data endpoint
- [x] Batch predictions endpoint
- [x] Prediction stats + model metrics endpoint
- [x] Weather forecast (1–16 days) + historical archive endpoints
- [x] **7-day disease risk forecast** — per-day risk ribbon
- [x] **Disease comparison** — malaria + flu + cholera in one call
- [x] **Feature importance** — which variables drove each prediction
- [x] **CSV export** — download predictions for offline use
- [ ] Phase 2 — LSTM / Prophet time-series forecasting (1–8 weeks ahead)
- [ ] Scheduled data ingestion (APScheduler)
- [ ] Email / SMS alert system for high-risk thresholds
- [ ] Additional diseases: dengue, pneumonia, meningitis
- [ ] Historical trend comparison (5-year climate + WHO case overlay)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with open data from **Open-Meteo**, **WHO**, and **World Bank** • Designed to support early disease outbreak warning

[![Open-Meteo](https://img.shields.io/badge/Data-Open--Meteo-00BFFF?style=flat-square)](https://open-meteo.com/)
[![WHO](https://img.shields.io/badge/Data-WHO_GHO-0093D5?style=flat-square)](https://www.who.int/data/gho)
[![World Bank](https://img.shields.io/badge/Data-World_Bank-003087?style=flat-square)](https://api.worldbank.org/v2/)
[![Fly.io](https://img.shields.io/badge/Deployed-Fly.io-8B5CF6?style=flat-square&logo=flydotio&logoColor=white)](https://climatehealth-ai.fly.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>
