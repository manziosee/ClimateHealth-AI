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
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-FF6600?style=flat-square&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![Fly.io](https://img.shields.io/badge/Deployed-Fly.io-8B5CF6?style=flat-square&logo=flydotio&logoColor=white)](https://fly.io/)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Live Demo](#-live-demo)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Data Sources](#-data-sources)
- [ML Models](#-ml-models)
- [API Reference](#-api-reference)
- [Quick Start](#-quick-start)
- [Deployment](#-deployment)
- [Environment Variables](#-environment-variables)
- [CI/CD](#-cicd)
- [Roadmap](#-roadmap)

---

## 🌍 Overview

Health organizations typically **react** after disease cases rise rather than predicting outbreaks beforehand. **ClimateHealth AI** solves this by correlating real-time weather patterns with historical disease data to forecast outbreak risk weeks in advance.

| Weather Signal | Disease Impact |
|---|---|
| 🌧️ High rainfall | More mosquito breeding → Malaria spike |
| 💧 High humidity | Respiratory infections spread faster |
| 🌡️ Temperature drop | Influenza outbreaks increase |
| 🌊 Flooding events | Waterborne diseases (Cholera) surge |

**Key capabilities:**
- 🗺️ **Global coverage** — predict for any coordinate worldwide
- ⚡ **Real-time weather** — live data from Open-Meteo API (no API key required)
- 🤖 **ML-powered** — XGBoost + Random Forest ensemble trained on epidemiological patterns
- 🔴 **Risk scoring** — Low / Medium / High outbreak classification
- 📊 **Interactive dashboard** — GIS map, trend charts, alert panels
- 🚀 **Fully deployed** — Fly.io + Neon PostgreSQL + Upstash Redis

---

## 🎬 Live Demo

> Backend API deployed on Fly.io. Frontend runs locally via Docker.

| URL | Description |
|---|---|
| [https://climatehealth-ai.fly.dev/](https://climatehealth-ai.fly.dev/) | API root — links to all endpoints |
| [https://climatehealth-ai.fly.dev/health](https://climatehealth-ai.fly.dev/health) | DB + Redis connectivity status |
| [https://climatehealth-ai.fly.dev/swagger](https://climatehealth-ai.fly.dev/swagger) | Redirects to Swagger UI |
| [https://climatehealth-ai.fly.dev/api/docs](https://climatehealth-ai.fly.dev/api/docs) | Swagger UI (interactive docs) |
| [https://climatehealth-ai.fly.dev/api/redoc](https://climatehealth-ai.fly.dev/api/redoc) | ReDoc documentation |
| [https://climatehealth-ai.fly.dev/api/v1/predictions](https://climatehealth-ai.fly.dev/api/v1/predictions) | Predictions endpoint |

**Local development:**
```
http://localhost       → Full dashboard (via Docker)
http://localhost/api   → FastAPI REST endpoints
http://localhost/api/docs  → Swagger UI
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose | Version |
|---|---|---|
| ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) **Python** | Core language | 3.13 |
| ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) **FastAPI** | REST API framework | 0.115 |
| ![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white) **SQLAlchemy** | Async ORM | 2.0 |
| ![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white) **Neon PostgreSQL** | Serverless database | Latest |
| ![Redis](https://img.shields.io/badge/-Redis-DC382D?style=flat-square&logo=redis&logoColor=white) **Upstash Redis** | Caching + rate limiting | 5.0 |
| ![Alembic](https://img.shields.io/badge/-Alembic-6BA81E?style=flat-square&logo=python&logoColor=white) **Alembic** | DB migrations | 1.13 |

### Machine Learning
| Technology | Purpose | Version |
|---|---|---|
| ![XGBoost](https://img.shields.io/badge/-XGBoost-FF6600?style=flat-square&logo=xgboost&logoColor=white) **XGBoost** | Outbreak regression models | 2.1 |
| ![scikit-learn](https://img.shields.io/badge/-scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white) **scikit-learn** | Feature pipeline + Random Forest | 1.6 |
| ![Pandas](https://img.shields.io/badge/-Pandas-150458?style=flat-square&logo=pandas&logoColor=white) **Pandas** | Data manipulation | 2.2 |
| ![NumPy](https://img.shields.io/badge/-NumPy-013243?style=flat-square&logo=numpy&logoColor=white) **NumPy** | Numerical computing | 2.1 |

### Frontend
| Technology | Purpose | Version |
|---|---|---|
| ![Next.js](https://img.shields.io/badge/-Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white) **Next.js** | React framework (App Router) | 15 |
| ![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white) **TypeScript** | Type-safe frontend | 5 |
| ![TailwindCSS](https://img.shields.io/badge/-Tailwind_CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white) **Tailwind CSS** | Utility-first styling | 4 |
| ![Leaflet](https://img.shields.io/badge/-Leaflet-199900?style=flat-square&logo=leaflet&logoColor=white) **Leaflet + React-Leaflet** | Interactive GIS maps | 1.9 |
| ![Recharts](https://img.shields.io/badge/-Recharts-22B5BF?style=flat-square&logo=recharts&logoColor=white) **Recharts** | Data visualization charts | 2 |

### Infrastructure
| Technology | Purpose |
|---|---|
| ![Fly.io](https://img.shields.io/badge/-Fly.io-8B5CF6?style=flat-square&logo=flydotio&logoColor=white) **Fly.io** | Backend cloud deployment |
| ![Docker](https://img.shields.io/badge/-Docker-2496ED?style=flat-square&logo=docker&logoColor=white) **Docker + Compose** | Local containerization |
| ![Nginx](https://img.shields.io/badge/-Nginx-009639?style=flat-square&logo=nginx&logoColor=white) **Nginx** | Reverse proxy + routing (local) |
| **GitHub Actions** | CI/CD pipeline — lint, test, deploy |

---

## 🏗️ System Architecture

```
                        ┌─────────────────────────────────────┐
                        │           User / Browser             │
                        └──────────────┬──────────────────────┘
                                       │ HTTPS
                        ┌──────────────▼──────────────────────┐
                        │         Fly.io (Production)          │
                        │                                      │
                        │   FastAPI (Python 3.13)              │
                        │                                      │
                        │  GET  /                → API info    │
                        │  GET  /health          → status      │
                        │  GET  /swagger         → docs        │
                        │  GET  /api/docs        → Swagger UI  │
                        │  POST /api/v1/predictions            │
                        │  GET  /api/v1/weather                │
                        │  GET  /api/v1/locations/search       │
                        │  GET  /api/v1/stats                  │
                        │  GET  /api/v1/disease                │
                        └──────┬───────────────┬──────────────┘
                               │               │
               ┌───────────────▼──┐    ┌───────▼────────────┐
               │  Upstash Redis    │    │  Neon PostgreSQL    │
               │  (Fly.io managed) │    │  (Serverless)       │
               │                  │    │                      │
               │  • Weather cache │    │  • predictions       │
               │  • Predictions   │    │  • weather_snapshots │
               │  • Rate limiting │    │  • Alembic migrations│
               └───────────────────┘    └────────────────────┘
                               │
               ┌───────────────▼────────────────────────────┐
               │           External Data Sources             │
               │                                             │
               │  🌤️  Open-Meteo API   (weather, free)      │
               │  🏥  WHO GHO API      (disease data, free)  │
               │  📍  Nominatim OSM    (reverse geocoding)   │
               │  🔍  Open-Meteo Geo   (location search)     │
               │  🌍  World Bank API   (population density)  │
               └─────────────────────────────────────────────┘
```

### Redis Caching Strategy

| Cache Key | TTL | Description |
|---|---|---|
| `weather:{lat}:{lon}` | 30 min | Weather fetch per location |
| `prediction:{disease}:{lat}:{lon}` | 1 hour | Prediction result per location |
| `wb:pop:{country_code}` | 24 hours | World Bank population density |
| `rate:{ip}` | 1 min | Sliding window rate limiter (60 req/min) |

---

## 📁 Project Structure

```
ClimateHealth-AI/
├── .github/
│   └── workflows/
│       ├── ci-backend.yml           # Lint, import checks, ML pipeline smoke test
│       ├── deploy-backend.yml       # Auto-deploy to Fly.io on push to main
│       └── train-models.yml         # Monthly model retraining + GitHub Release
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry, lifespan, middleware, root routes
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── predictions.py   # POST/GET/DELETE predictions + batch endpoint
│   │   │       ├── weather.py       # Current weather, forecast, historical archive
│   │   │       ├── locations.py     # Location search via Open-Meteo Geocoding
│   │   │       ├── stats.py         # Aggregate prediction statistics
│   │   │       ├── disease.py       # WHO GHO disease surveillance data
│   │   │       └── health.py        # DB + Redis health check
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic settings from .env
│   │   │   ├── database.py          # Async SQLAlchemy + Neon PostgreSQL
│   │   │   ├── cache.py             # Async Redis client with graceful fallback
│   │   │   └── middleware.py        # IP rate limiting (60 req/min)
│   │   ├── models/
│   │   │   ├── db_models.py         # ORM: Prediction, WeatherSnapshot
│   │   │   └── schemas.py           # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── weather.py           # Open-Meteo API client (current + forecast + archive)
│   │   │   ├── disease.py           # WHO GHO OData API client
│   │   │   ├── geocoding.py         # Nominatim reverse geocoding
│   │   │   ├── predictor.py         # ML ensemble inference + heuristic fallback
│   │   │   └── worldbank.py         # World Bank population density API
│   │   └── ml/
│   │       ├── pipeline.py          # Feature engineering (23 features)
│   │       ├── data_generator.py    # Synthetic training data generator
│   │       ├── train.py             # XGBoost + Random Forest training
│   │       ├── model_registry.py    # Auto-download models from GitHub Releases
│   │       └── saved_models/        # Trained .pkl files (6 models)
│   │           ├── malaria_xgb.pkl
│   │           ├── malaria_rf.pkl
│   │           ├── flu_xgb.pkl
│   │           ├── flu_rf.pkl
│   │           ├── cholera_xgb.pkl
│   │           ├── cholera_rf.pkl
│   │           └── metrics.json
│   ├── alembic/
│   │   └── versions/
│   │       ├── 0001_initial_tables.py
│   │       └── 0002_add_wind_speed_and_indexes.py
│   ├── data/
│   │   ├── raw/                     # Raw training datasets
│   │   └── processed/               # Processed feature datasets
│   ├── .env.example
│   ├── alembic.ini
│   ├── fly.toml                     # Fly.io deployment config
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx                 # Main dashboard page
│   │   ├── layout.tsx               # Root layout + Leaflet CSS import
│   │   ├── globals.css              # Global styles
│   │   ├── types.ts                 # Shared TypeScript interfaces
│   │   └── mockData.ts              # Offline demo seed data
│   ├── components/
│   │   ├── Map.tsx                  # Leaflet GIS map with outbreak markers
│   │   ├── OutbreakCalculator.tsx   # Prediction input form
│   │   ├── TrendsChart.tsx          # Recharts climate-disease correlation chart
│   │   └── AlertsPanel.tsx          # Real-time alert log
│   ├── public/                      # Static assets
│   ├── .env.example
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── Dockerfile
├── nginx/
│   └── nginx.conf                   # Reverse proxy: /api/* → backend, /* → frontend
├── docker-compose.yml               # Full local stack: backend + frontend + nginx + redis
├── LICENSE
└── README.md
```

---

## 📡 Data Sources

| Source | Data | Cost |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | Temperature, rainfall, humidity, wind speed, UV index, ET₀, forecast + historical | Free, no key |
| [WHO GHO API](https://www.who.int/data/gho/info/gho-odata-api) | Malaria & cholera case records by country/year | Free |
| [Nominatim / OSM](https://nominatim.org/) | Reverse geocoding (lat/lon → city name + country code) | Free |
| [Open-Meteo Geocoding](https://open-meteo.com/en/docs/geocoding-api) | City name → lat/lon search | Free |
| [World Bank API](https://api.worldbank.org/v2/) | Population density by country | Free |

---

## 🤖 ML Models

### Phase 1 — XGBoost + Random Forest Ensemble (current)

Both models are trained per disease and predictions are averaged for improved stability.

**Input features (23 total):**

| Feature | Source | Engineering |
|---|---|---|
| `temperature` | Open-Meteo | Raw °C (avg of max/min) |
| `rainfall` | Open-Meteo | Raw mm |
| `humidity` | Open-Meteo | Raw % |
| `wind_speed` | Open-Meteo | Raw km/h |
| `population_density` | World Bank / user input | Raw /km² |
| `uv_index` | Open-Meteo | Raw UV max |
| `et0_evapotranspiration` | Open-Meteo | Raw mm/day |
| `precipitation_probability` | Open-Meteo | Raw % |
| `apparent_temperature` | Open-Meteo | Raw °C |
| `month_sin / month_cos` | System date | Cyclical encoding |
| `rain_humidity` | Derived | rainfall × humidity / 100 |
| `temp_humidity` | Derived | temperature × humidity / 100 |
| `rain_temp` | Derived | rainfall × temperature |
| `pop_rain` | Derived | population_density × rainfall |
| `heat_index` | Derived | Apparent temperature proxy |
| `flood_risk` | Derived | Binary: rainfall > 100mm |
| `high_humidity` | Derived | Binary: humidity > 75% |
| `high_uv` | Derived | Binary: uv_index > 7 |
| `uv_temp` | Derived | uv_index × temperature |
| `drought_stress` | Derived | Binary: ET₀ > 5mm/day |
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

## 📋 API Reference

All endpoints are available at `https://climatehealth-ai.fly.dev` or via [Swagger UI](https://climatehealth-ai.fly.dev/api/docs).

### `POST /api/v1/predictions`
Run a disease outbreak prediction for any global location.

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
  "predicted_at": "2025-01-15T10:30:00"
}
```

### `POST /api/v1/predictions/batch`
Run up to 20 predictions in one request — used to seed the map on dashboard load.

### `GET /api/v1/predictions`
List stored predictions with optional filters.

| Param | Type | Description |
|---|---|---|
| `disease` | string | Filter: `malaria`, `flu`, `cholera` |
| `risk_level` | string | Filter: `Low`, `Medium`, `High` |
| `limit` | int | Max results (default: 50, max: 200) |
| `offset` | int | Pagination offset (default: 0) |

### `GET /api/v1/predictions/{id}`
Get a single prediction by ID.

### `DELETE /api/v1/predictions/{id}`
Delete a prediction and invalidate its cache entry.

### `GET /api/v1/weather`
Fetch current weather + today's forecast for a coordinate.

| Param | Type | Description |
|---|---|---|
| `lat` | float | Latitude (-90 to 90) |
| `lon` | float | Longitude (-180 to 180) |

### `GET /api/v1/weather/forecast`
Fetch multi-day forecast (up to 16 days).

| Param | Type | Description |
|---|---|---|
| `lat` | float | Latitude |
| `lon` | float | Longitude |
| `days` | int | Forecast days (default: 7, max: 16) |

### `GET /api/v1/weather/history`
Fetch historical daily weather from the Open-Meteo archive (back to 1940).

| Param | Type | Description |
|---|---|---|
| `lat` | float | Latitude |
| `lon` | float | Longitude |
| `start` | string | Start date `YYYY-MM-DD` |
| `end` | string | End date `YYYY-MM-DD` |

### `GET /api/v1/locations/search`
Search locations by name.

| Param | Type | Description |
|---|---|---|
| `q` | string | City or region name (min 2 chars) |

### `GET /api/v1/stats`
Aggregate statistics over all stored predictions.

### `GET /api/v1/disease`
Query WHO GHO disease surveillance records.

| Param | Type | Description |
|---|---|---|
| `disease` | string | `malaria`, `flu`, or `cholera` |
| `country` | string | ISO country code (optional) |

### `GET /health`
Returns DB and Redis connectivity status with latency measurements.

```json
{
  "status": "ok",
  "environment": "production",
  "version": "1.0.0",
  "services": {
    "database": { "ok": true, "latency_ms": 12.4 },
    "redis":    { "ok": true, "latency_ms": 3.1 }
  }
}
```

### `GET /`
Returns API info with links to all key endpoints.

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Neon account](https://neon.tech/) (free tier works)

### 1. Clone & configure

```bash
git clone https://github.com/manziosee/ClimateHealth-AI.git
cd ClimateHealth-AI

cp backend/.env.example backend/.env
# Edit backend/.env — fill in DATABASE_URL and REDIS_URL
```

### 2. Train ML models (first time only)

```bash
cd backend
pip install -r requirements.txt
python -m app.ml.train
```

### 3. Run the full stack

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost |
| API | http://localhost/api/v1 |
| Swagger Docs | http://localhost/api/docs |
| Health Check | http://localhost/health |

### 4. Test the API

```bash
curl -X POST http://localhost/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"lat": -1.9403, "lon": 29.8739, "disease": "malaria", "population_density": 620}'
```

---

## ☁️ Deployment

The backend is deployed on **Fly.io** with **Neon PostgreSQL** and **Upstash Redis**.

### Deploy manually

```bash
cd backend

# First time setup
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

Any push to `main` that modifies `backend/**` automatically triggers a deploy via `.github/workflows/deploy-backend.yml`.

**Required GitHub secret:** `FLY_API_TOKEN` — get it with:
```bash
flyctl tokens create deploy -a climatehealth-ai
```

### Live endpoints

| URL | Description |
|---|---|
| https://climatehealth-ai.fly.dev/ | API root — JSON with links |
| https://climatehealth-ai.fly.dev/health | DB + Redis status |
| https://climatehealth-ai.fly.dev/swagger | Redirects to Swagger UI |
| https://climatehealth-ai.fly.dev/api/docs | Swagger UI (interactive) |
| https://climatehealth-ai.fly.dev/api/redoc | ReDoc documentation |
| https://climatehealth-ai.fly.dev/api/v1/predictions | Predictions API |

---

## 🔧 Environment Variables

### Backend (`backend/.env`)

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

### Frontend (`frontend/.env`)

| Variable | Description | Example |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `https://climatehealth-ai.fly.dev/api/v1` |

---

## ⚙️ CI/CD

| Workflow | Trigger | Steps |
|---|---|---|
| `ci-backend.yml` | Push to `main`/`dev`, PR to `main` | Install deps → verify imports → smoke test ML pipeline → verify FastAPI loads → deploy to Fly.io |
| `deploy-backend.yml` | Push to `main` (`backend/**`) | Deploy to Fly.io via `flyctl deploy --remote-only` |
| `train-models.yml` | 1st of every month (or manual) | Train XGBoost + RF → upload artifacts → create GitHub Release with `.pkl` files |

Model `.pkl` files are published as GitHub Release assets and automatically downloaded by `model_registry.py` on each Fly.io deploy (since the filesystem is ephemeral).

---

## 🗺️ Roadmap

- [x] Phase 1 — XGBoost + Random Forest ensemble (malaria, flu, cholera)
- [x] Interactive GIS dashboard with Leaflet maps
- [x] Real-time weather ingestion (Open-Meteo) — 23 features
- [x] Redis caching + IP rate limiting + graceful fallback
- [x] Neon PostgreSQL + async SQLAlchemy + Alembic migrations
- [x] Docker + Nginx + Redis local deployment
- [x] Fly.io production deployment + GitHub Actions CI/CD
- [x] World Bank population density auto-resolution
- [x] WHO GHO disease data endpoint
- [x] Batch predictions endpoint
- [x] Prediction stats + aggregation endpoint
- [x] Weather forecast + historical archive endpoints
- [ ] Phase 2 — LSTM / Prophet time-series forecasting
- [ ] Scheduled data ingestion (APScheduler)
- [ ] Email / SMS alert system for high-risk thresholds
- [ ] Additional diseases: dengue, pneumonia, meningitis
- [ ] Frontend deployment (Vercel)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ using open data from **Open-Meteo**, **WHO**, and **World Bank** • Designed to save lives through early warning

[![Open-Meteo](https://img.shields.io/badge/Data-Open--Meteo-00BFFF?style=flat-square)](https://open-meteo.com/)
[![WHO](https://img.shields.io/badge/Data-WHO_GHO-0093D5?style=flat-square)](https://www.who.int/data/gho)
[![World Bank](https://img.shields.io/badge/Data-World_Bank-003087?style=flat-square)](https://api.worldbank.org/v2/)
[![Fly.io](https://img.shields.io/badge/Deployed-Fly.io-8B5CF6?style=flat-square&logo=flydotio&logoColor=white)](https://climatehealth-ai.fly.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>
