<div align="center">

<img src="https://img.shields.io/badge/ClimateHealth_AI-Global_Outbreak_Forecasting-0ea5e9?style=for-the-badge&logo=globe&logoColor=white" alt="ClimateHealth AI" />

<br/>
<br/>

<p align="center">
  <strong>AI-powered global disease outbreak prediction using real-time weather, environmental, and demographic data.</strong><br/>
  Predicts malaria, influenza, cholera, dengue, pneumonia, and meningitis outbreaks weeks in advance — anywhere in the world.
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
| High rainfall + humidity | Mosquito breeding → Malaria / Dengue spike |
| Temperature drop + dry air | Respiratory infections → Influenza / Pneumonia surge |
| Flooding events | Waterborne diseases → Cholera outbreak |
| Dry season / low humidity | Bacterial spread → Meningitis risk |

**Key capabilities:**
- **Global coverage** — predict for any lat/lon worldwide, no region restrictions
- **6 diseases** — malaria, flu, cholera, dengue, pneumonia, meningitis
- **Real-time weather** — live data from Open-Meteo API (no API key required)
- **ML ensemble** — XGBoost + Random Forest (12 models) with feature importance
- **AI explanations** — Groq Llama 3 natural-language risk narratives
- **Scenario simulation** — what-if climate deltas (+2°C, +50mm rainfall, etc.)
- **Disease signal detection** — HuggingFace zero-shot classifier on news/reports
- **7-day forecast** — day-by-day disease risk ribbon for the coming week
- **Disease comparison** — all 6 diseases side-by-side in one call
- **Background refresh** — APScheduler keeps WHO data fresh every 6 hours
- **CSV export** — download predictions for field use by NGOs and health workers
- **Fully deployed** — Fly.io + Neon PostgreSQL + Upstash Redis

---

## Live API

| URL | Description |
|---|---|
| [https://climatehealth-ai.fly.dev/](https://climatehealth-ai.fly.dev/) | API root |
| [https://climatehealth-ai.fly.dev/health](https://climatehealth-ai.fly.dev/health) | DB + Redis connectivity status |
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
| **APScheduler** | Background WHO data refresh | 3.10 |

### Machine Learning
| Technology | Purpose | Version |
|---|---|---|
| **XGBoost** | Outbreak regression models | 2.1 |
| **scikit-learn** | Feature pipeline + Random Forest | 1.6 |
| **Pandas** | Data manipulation | 2.2 |
| **NumPy** | Numerical computing | 2.1 |

### AI Services
| Technology | Purpose |
|---|---|
| **Groq Cloud (Llama 3.1-8b)** | Natural-language risk explanations + scenario simulation |
| **HuggingFace (bart-large-mnli)** | Zero-shot disease signal detection + symptom classification |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Fly.io** | Cloud deployment |
| **Docker + Compose** | Local containerization |
| **GitHub Actions** | CI/CD — lint, smoke test, deploy, monthly model retraining |

---

## System Architecture

```
                    +----------------------------------------------+
                    |          Client / Consumer                    |
                    |  (browser, curl, health app, NGO, API user)  |
                    +---------------------------+------------------+
                                                | HTTPS
                    +---------------------------v------------------+
                    |         Fly.io (Production)                  |
                    |                                              |
                    |   FastAPI 1.2.0  (Python 3.13)               |
                    |                                              |
                    |  POST /api/v1/predictions[/batch/forecast]   |
                    |  GET  /api/v1/predictions[/compare/export]   |
                    |  GET  /api/v1/weather[/forecast/history]     |
                    |  GET  /api/v1/disease                        |
                    |  GET  /api/v1/stats[/model-metrics]          |
                    |  GET  /api/v1/locations/search               |
                    |  POST /api/v1/ai[/explain/scenario/signal/symptoms]
                    |  GET  /health                                |
                    +----------+-------------------+--------------+
                               |                   |
           +-------------------v---+   +-----------v----------------+
           |  Upstash Redis        |   |  Neon PostgreSQL            |
           |                       |   |                             |
           |  Weather cache        |   |  predictions                |
           |  Predictions          |   |  weather_snapshots          |
           |  Rate limiting        |   |  disease_records            |
           +-----+--+--------------+   |  locations (geocache)       |
                    |                  |  model_metrics              |
                    |                  +-----------------------------+
                    |
           +--------v-----------------------------------------------+
           |            External Data Sources                        |
           |                                                         |
           |  Open-Meteo API     weather + forecast + archive        |
           |  WHO GHO API        disease surveillance data           |
           |  Nominatim OSM      reverse geocoding                   |
           |  Open-Meteo Geo     city/region search                  |
           |  World Bank API     population density                  |
           |  Groq Cloud         Llama 3.1 AI explanations           |
           |  HuggingFace API    zero-shot classification            |
           +---------------------------------------------------------+
```

### Redis Caching Strategy

| Cache Key | TTL | Description |
|---|---|---|
| `weather:{lat}:{lon}` | 30 min | Weather fetch per location |
| `forecast:{lat}:{lon}:{days}` | 30 min | Multi-day forecast |
| `prediction:{disease}:{lat}:{lon}` | 1 hour | Prediction result |
| `forecast_pred:{disease}:{lat}:{lon}:{days}` | 1 hour | Disease forecast |
| `compare:{lat}:{lon}` | 1 hour | Disease comparison result |
| `wb:pop:{country_code}` | 24 hours | World Bank population density |
| `disease:{disease}:{country}` | 24 hours | WHO GHO data |
| `history:{lat}:{lon}:{start}:{end}` | 24 hours | Historical weather |
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
│   ├── main.py                 # FastAPI entry, lifespan, middleware, scheduler, root routes
│   ├── api/
│   │   └── v1/
│   │       ├── predictions.py  # POST/GET/DELETE + batch, forecast, compare, export
│   │       ├── weather.py      # Current weather, forecast (1-16d), historical archive
│   │       ├── locations.py    # City/region search via Open-Meteo Geocoding
│   │       ├── stats.py        # Aggregate prediction statistics + model metrics
│   │       ├── disease.py      # WHO GHO disease surveillance data
│   │       ├── ai.py           # Groq + HuggingFace AI endpoints
│   │       └── health.py       # DB + Redis health check with latency
│   ├── core/
│   │   ├── config.py           # Pydantic settings from .env
│   │   ├── database.py         # Async SQLAlchemy + Neon PostgreSQL
│   │   ├── cache.py            # Async Redis client with graceful NoopRedis fallback
│   │   ├── middleware.py       # IP rate limiting (60 req/min, sliding window)
│   │   └── scheduler.py        # APScheduler — WHO cache refresh every 6 hours
│   ├── models/
│   │   ├── db_models.py        # ORM: Prediction, WeatherSnapshot, DiseaseRecord, LocationCache, ModelMetrics
│   │   └── schemas.py          # Pydantic request/response schemas
│   ├── services/
│   │   ├── weather.py          # Open-Meteo client (current + forecast + archive)
│   │   ├── disease.py          # WHO GHO OData API client (malaria, cholera, dengue, meningitis, flu, pneumonia)
│   │   ├── geocoding.py        # Nominatim reverse geocoding with DB cache
│   │   ├── predictor.py        # ML ensemble inference + feature importance + heuristic fallback
│   │   ├── worldbank.py        # World Bank population density API
│   │   ├── groq_service.py     # Groq Llama 3 — prediction explanations + scenario narration
│   │   └── huggingface_service.py  # HF zero-shot — disease signal + symptom classification
│   └── ml/
│       ├── pipeline.py         # Feature engineering (24 features)
│       ├── data_generator.py   # Synthetic training data (6 diseases)
│       ├── train.py            # XGBoost + Random Forest training + DB metrics logging
│       ├── model_registry.py   # Auto-download models from GitHub Releases
│       └── saved_models/       # 12 trained .pkl files + metrics.json
├── alembic/
│   └── versions/
│       ├── 0001_initial_tables.py
│       ├── 0002_add_wind_speed_and_indexes.py
│       └── 0003_add_disease_records_locations_model_metrics.py
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── fly.toml
├── requirements.txt
└── README.md
```

---

## Data Sources

| Source | Data | Cost |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | Temperature, rainfall, humidity, wind, UV, ET0, precipitation probability — forecast + archive to 1940 | Free, no key |
| [WHO GHO API](https://www.who.int/data/gho/info/gho-odata-api) | Malaria, cholera, dengue, meningitis, pneumonia, influenza case records | Free |
| [Nominatim / OSM](https://nominatim.org/) | Reverse geocoding (lat/lon → city + country) | Free |
| [Open-Meteo Geocoding](https://open-meteo.com/en/docs/geocoding-api) | City name → lat/lon search | Free |
| [World Bank API](https://api.worldbank.org/v2/) | Population density by country | Free |
| [Groq Cloud](https://console.groq.com/) | Llama 3.1-8b-instant LLM inference | Free tier |
| [HuggingFace](https://huggingface.co/facebook/bart-large-mnli) | bart-large-mnli zero-shot classification | Free tier |

---

## ML Models

### Phase 1 — XGBoost + Random Forest Ensemble (current)

12 trained models (2 per disease × 6 diseases). Averaged at inference for improved stability. Every prediction includes **feature importance** showing which variables drove the result.

**Supported diseases and key drivers:**

| Disease | Key Climate Drivers | Risk: Low / Medium / High |
|---|---|---|
| **Malaria** | Rainfall, humidity, temperature, UV index | ≤40 / ≤100 / >100 cases |
| **Influenza** | Cold weather, dry conditions, seasonal peaks | ≤25 / ≤70 / >70 cases |
| **Cholera** | Flooding, evapotranspiration, population density | ≤10 / ≤35 / >35 cases |
| **Dengue** | Heat + rainfall + humidity, urban density, UV | ≤30 / ≤80 / >80 cases |
| **Pneumonia** | Cold/dry air, overcrowding, winter months | ≤50 / ≤120 / >120 cases |
| **Meningitis** | Dry season, low humidity, dusty winds | ≤15 / ≤40 / >40 cases |

**Input features (24 total):**

| Feature | Source | Notes |
|---|---|---|
| `temperature` | Open-Meteo | Avg daily °C |
| `rainfall` | Open-Meteo | Daily precipitation mm |
| `humidity` | Open-Meteo | Relative humidity % |
| `wind_speed` | Open-Meteo | Max daily km/h |
| `population_density` | World Bank | Auto-resolved by country |
| `uv_index` | Open-Meteo | Daily max UV |
| `et0_evapotranspiration` | Open-Meteo | mm/day |
| `precipitation_probability` | Open-Meteo | Max daily % |
| `apparent_temperature` | Open-Meteo | Feels-like °C |
| `month_sin / month_cos` | System date | Cyclical month encoding |
| `rain_humidity` | Derived | rainfall × humidity / 100 |
| `temp_humidity` | Derived | temperature × humidity / 100 |
| `rain_temp` | Derived | rainfall × temperature |
| `pop_rain` | Derived | population_density × rainfall |
| `heat_index` | Derived | Apparent temperature proxy |
| `flood_risk` | Derived | Binary: rainfall > 100mm |
| `high_humidity` | Derived | Binary: humidity > 75% |
| `high_uv` | Derived | Binary: uv_index > 7 |
| `uv_temp` | Derived | uv_index × temperature |
| `drought_stress` | Derived | Binary: ET0 > 5mm/day |
| `rain_prob_rain` | Derived | precip_prob × rainfall / 100 |
| `feels_like_diff` | Derived | apparent_temp − temperature |

**Training:** 8,000 synthetic samples per disease, 80/20 split.

**Latest model metrics:**

| Disease | MAE | R² |
|---|---|---|
| Malaria (ensemble) | ~4.2 | ~0.975 |
| Flu (ensemble) | ~2.4 | ~0.890 |
| Cholera (ensemble) | ~3.4 | ~0.997 |
| Dengue (ensemble) | ~3.5 | ~0.976 |
| Pneumonia (ensemble) | ~2.9 | ~0.856 |
| Meningitis (ensemble) | ~2.5 | ~0.897 |

### Phase 2 — Time-series Forecasting (planned)
- **LSTM** — sequential outbreak progression
- **Prophet** — seasonal decomposition
- **Temporal Fusion Transformer** — multi-horizon 1–8 week forecasting

---

## API Reference

All endpoints are available at `https://climatehealth-ai.fly.dev` or via [Swagger UI](https://climatehealth-ai.fly.dev/api/docs).

### Predictions

#### `POST /api/v1/predictions`
Run a disease prediction for any global location. Fetches live weather from Open-Meteo, auto-resolves population density from World Bank, runs the XGBoost + RF ensemble.

**Request:**
```json
{
  "lat": -1.9403,
  "lon": 29.8739,
  "disease": "malaria"
}
```

`disease` options: `malaria` | `flu` | `cholera` | `dengue` | `pneumonia` | `meningitis`

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
  "population_density": 620.0,
  "predicted_at": "2025-01-15T10:30:00Z",
  "feature_importance": {
    "rain_humidity": 0.312,
    "rainfall": 0.218,
    "temperature": 0.154,
    "humidity": 0.127
  }
}
```

#### `POST /api/v1/predictions/batch`
Up to 20 predictions in one request.

#### `POST /api/v1/predictions/forecast`
Day-by-day disease risk ribbon for the next 1–16 days using Open-Meteo forecast.

```json
{ "lat": 6.3703, "lon": 2.3912, "disease": "dengue", "days": 7 }
```

#### `GET /api/v1/predictions/compare`
All 6 diseases predicted simultaneously for one location — single weather fetch.

```
GET /api/v1/predictions/compare?lat=-1.9403&lon=29.8739
```

#### `GET /api/v1/predictions/export`
Download predictions as CSV. Filterable by disease / risk level.

```
GET /api/v1/predictions/export?disease=malaria&risk_level=High
```

#### `GET /api/v1/predictions` · `GET /api/v1/predictions/{id}` · `DELETE /api/v1/predictions/{id}`
List (paginated), get, or delete stored predictions.

---

### AI Endpoints

All AI endpoints return `503` gracefully when the corresponding API key is not configured.

#### `POST /api/v1/ai/explain`
**Groq Llama 3** — 3-4 sentence natural-language explanation of a prediction: why the risk level was assigned, which conditions drove it, and what health authorities should do.

```json
{ "prediction_id": 42 }
```
or
```json
{ "lat": -1.9403, "lon": 29.8739, "disease": "malaria" }
```

#### `POST /api/v1/ai/scenario`
**Climate what-if simulator** — apply temperature/rainfall/humidity deltas to current conditions, run the model on both base and modified conditions, and get a Groq-narrated impact assessment.

```json
{
  "lat": -1.9403, "lon": 29.8739, "disease": "malaria",
  "rainfall_delta": 80, "temperature_delta": 2,
  "description": "flooding after heavy monsoon"
}
```

#### `POST /api/v1/ai/signal`
**HuggingFace zero-shot** — classify free text (news article, field report, social media) for disease outbreak signals. Returns ranked labels with confidence scores.

```json
{ "text": "Many residents report mosquito infestations following the recent floods." }
```

#### `POST /api/v1/ai/symptoms`
**HuggingFace zero-shot** — map a symptom description to a ranked differential of likely diseases.

```json
{ "symptoms": "high fever, chills, sweating, severe headache" }
```

---

### Weather

#### `GET /api/v1/weather` — current weather for any coordinate
#### `GET /api/v1/weather/forecast` — 1–16 day forecast
#### `GET /api/v1/weather/history` — historical archive back to 1940

---

### Other

| Endpoint | Description |
|---|---|
| `GET /api/v1/disease` | WHO GHO surveillance records (`disease`, `country` params) |
| `GET /api/v1/disease/indicators` | Search WHO GHO indicator catalogue |
| `GET /api/v1/stats` | Aggregate prediction stats (totals, risk breakdown, 24h/7d/30d trend) |
| `GET /api/v1/stats/model-metrics` | Training MAE + R² for all 12 models |
| `GET /api/v1/locations/search` | Geocoding search (`q` param) |
| `GET /health` | DB + Redis health check with latency |

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Neon account](https://neon.tech/) — free tier

### 1. Clone & configure

```bash
git clone https://github.com/manziosee/ClimateHealth-AI.git
cd ClimateHealth-AI

cp .env.example .env
# Edit .env — fill in DATABASE_URL and REDIS_URL at minimum
```

### 2. Train ML models (first time only)

```bash
pip install -r requirements.txt
python -m app.ml.train
```

This trains 12 models (6 diseases × XGBoost + Random Forest) and saves them to `app/ml/saved_models/`.

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

# Dengue prediction in Bangkok
curl -X POST http://localhost:8000/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"lat": 13.7563, "lon": 100.5018, "disease": "dengue"}'

# 7-day forecast
curl -X POST http://localhost:8000/api/v1/predictions/forecast \
  -H "Content-Type: application/json" \
  -d '{"lat": -1.9403, "lon": 29.8739, "disease": "malaria", "days": 7}'

# All 6 diseases compared
curl "http://localhost:8000/api/v1/predictions/compare?lat=-1.9403&lon=29.8739"

# Export CSV
curl "http://localhost:8000/api/v1/predictions/export?disease=malaria" -o predictions.csv

# AI explanation (requires GROQ_API_KEY)
curl -X POST http://localhost:8000/api/v1/ai/explain \
  -H "Content-Type: application/json" \
  -d '{"lat": -1.9403, "lon": 29.8739, "disease": "malaria"}'
```

---

## Deployment

The API is deployed on **Fly.io** with **Neon PostgreSQL** and **Upstash Redis**.

### Set Fly.io secrets

```powershell
# PowerShell (Windows)
flyctl secrets set DATABASE_URL="postgresql+asyncpg://..." REDIS_URL="rediss://..." GROQ_API_KEY="gsk_..." HUGGINGFACE_API_KEY="hf_..."
```

```bash
# Bash (Linux/Mac)
flyctl secrets set DATABASE_URL="postgresql+asyncpg://..." \
  REDIS_URL="rediss://..." \
  GROQ_API_KEY="gsk_..." \
  HUGGINGFACE_API_KEY="hf_..."
```

### Deploy

```bash
flyctl deploy --remote-only --ha=false
```

### Auto-deploy via GitHub Actions

Any push to `main` that modifies `app/**`, `requirements.txt`, or `Dockerfile` automatically runs CI (import checks + ML pipeline smoke test for all 6 diseases) and deploys to Fly.io.

**Required GitHub secret:** `FLY_API_TOKEN`
```bash
flyctl auth token
```
Add the output as a repository secret named `FLY_API_TOKEN`.

---

## Environment Variables

| Variable | Required | Description | Example |
|---|---|---|---|
| `DATABASE_URL` | Yes | Neon PostgreSQL async URL | `postgresql+asyncpg://user:pass@host/db?ssl=require` |
| `REDIS_URL` | Yes | Redis URL (use `rediss://` for Upstash TLS) | `rediss://default:pass@host:6379` |
| `APP_ENV` | No | Environment name | `production` |
| `SECRET_KEY` | No | App secret | Random 32-char string |
| `GROQ_API_KEY` | No | Groq Cloud key — enables `/ai/explain` + `/ai/scenario` | `gsk_...` |
| `HUGGINGFACE_API_KEY` | No | HF Inference API key — enables `/ai/signal` + `/ai/symptoms` | `hf_...` |
| `WEATHER_CACHE_TTL` | No | Seconds (default 1800) | `1800` |
| `PREDICTION_CACHE_TTL` | No | Seconds (default 3600) | `3600` |
| `DISEASE_CACHE_TTL` | No | Seconds (default 86400) | `86400` |

---

## CI/CD

| Workflow | Trigger | Steps |
|---|---|---|
| `ci-backend.yml` | Push to `main`/`dev`, PR to `main` | Install deps → verify imports (incl. apscheduler, groq) → smoke-test ML pipeline for all 6 diseases → verify FastAPI loads → deploy to Fly.io |
| `train-models.yml` | 1st of every month (or manual) | Train XGBoost + RF for all 6 diseases → upload artifacts → create GitHub Release with `.pkl` files |

Model `.pkl` files are baked into the Docker image at build time (`RUN python -m app.ml.train`) as the primary path. The GitHub Release fallback is used by `model_registry.py` if models are missing at runtime.

---

## Roadmap

- [x] Phase 1 — XGBoost + Random Forest ensemble (malaria, flu, cholera)
- [x] Real-time weather ingestion (Open-Meteo) — 24 engineered features
- [x] Redis caching + IP rate limiting + graceful NoopRedis fallback
- [x] Neon PostgreSQL + async SQLAlchemy + Alembic migrations
- [x] Fly.io production deployment + GitHub Actions CI/CD
- [x] World Bank population density auto-resolution
- [x] WHO GHO disease data endpoint
- [x] Batch predictions endpoint
- [x] Prediction stats + model metrics endpoint
- [x] Weather forecast (1–16 days) + historical archive endpoints
- [x] 7-day disease risk forecast — per-day risk ribbon
- [x] Disease comparison — all 6 diseases in one call
- [x] Feature importance — which variables drove each prediction
- [x] CSV export — download predictions for offline use
- [x] **Additional diseases** — dengue, pneumonia, meningitis (6 total, 12 models)
- [x] **Groq AI** — Llama 3 prediction explanations + climate scenario simulation
- [x] **HuggingFace AI** — zero-shot disease signal detection + symptom classification
- [x] **APScheduler** — automatic WHO data refresh every 6 hours
- [ ] Phase 2 — LSTM / Prophet time-series forecasting (1–8 weeks ahead)
- [ ] Email / SMS alert system for high-risk threshold notifications
- [ ] Historical trend comparison (5-year climate + WHO case overlay)
- [ ] GitHub Release automation for trained model `.pkl` files

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
