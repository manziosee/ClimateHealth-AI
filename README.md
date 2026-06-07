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
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-FF6600?style=flat-square&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)

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
- [Environment Variables](#-environment-variables)
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
- 🤖 **ML-powered** — XGBoost models trained on epidemiological patterns
- 🔴 **Risk scoring** — Low / Medium / High outbreak classification
- 📊 **Interactive dashboard** — GIS map, trend charts, alert panels
- 🚀 **Fully containerized** — Docker + Nginx + Redis

---

## 🎬 Live Demo

> Dashboard preview — interactive GIS map with real-time outbreak hotspots, climate-disease correlation charts, and a prediction simulator.

```
http://localhost       → Full dashboard (via Docker)
http://localhost/api   → FastAPI REST endpoints
http://localhost/docs  → Swagger UI (auto-generated)
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose | Version |
|---|---|---|
| ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) **Python** | Core language | 3.11 |
| ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) **FastAPI** | REST API framework | 0.111 |
| ![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white) **SQLAlchemy** | Async ORM | 2.0 |
| ![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white) **Neon PostgreSQL** | Serverless database | Latest |
| ![Redis](https://img.shields.io/badge/-Redis-DC382D?style=flat-square&logo=redis&logoColor=white) **Redis** | Caching + rate limiting | 7 |
| ![Alembic](https://img.shields.io/badge/-Alembic-6BA81E?style=flat-square&logo=python&logoColor=white) **Alembic** | DB migrations | 1.13 |

### Machine Learning
| Technology | Purpose | Version |
|---|---|---|
| ![XGBoost](https://img.shields.io/badge/-XGBoost-FF6600?style=flat-square&logo=xgboost&logoColor=white) **XGBoost** | Outbreak regression models | 2.0 |
| ![scikit-learn](https://img.shields.io/badge/-scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white) **scikit-learn** | Feature pipeline + evaluation | 1.4 |
| ![Pandas](https://img.shields.io/badge/-Pandas-150458?style=flat-square&logo=pandas&logoColor=white) **Pandas** | Data manipulation | 2.2 |
| ![NumPy](https://img.shields.io/badge/-NumPy-013243?style=flat-square&logo=numpy&logoColor=white) **NumPy** | Numerical computing | 1.26 |

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
| ![Docker](https://img.shields.io/badge/-Docker-2496ED?style=flat-square&logo=docker&logoColor=white) **Docker + Compose** | Containerization |
| ![Nginx](https://img.shields.io/badge/-Nginx-009639?style=flat-square&logo=nginx&logoColor=white) **Nginx** | Reverse proxy + routing |

---

## 🏗️ System Architecture

```
                        ┌─────────────────────────────────────┐
                        │           User / Browser             │
                        └──────────────┬──────────────────────┘
                                       │ HTTP :80
                        ┌──────────────▼──────────────────────┐
                        │              Nginx                   │
                        │   /api/* → backend:8000              │
                        │   /*     → frontend:3000             │
                        └──────┬───────────────┬──────────────┘
                               │               │
               ┌───────────────▼──┐    ┌───────▼────────────┐
               │   FastAPI        │    │   Next.js           │
               │   (Python 3.11)  │    │   (App Router)      │
               │                  │    │                      │
               │  /api/v1/        │    │  Dashboard          │
               │  predictions     │    │  GIS Map            │
               │  weather         │    │  Trend Charts       │
               │  locations       │    │  Alert Panel        │
               └──┬───────┬───────┘    └────────────────────┘
                  │       │
     ┌────────────▼─┐  ┌──▼──────────────┐
     │    Redis      │  │  Neon PostgreSQL │
     │  Cache:       │  │                  │
     │  • Weather    │  │  • predictions   │
     │  • Predictions│  │  • weather_      │
     │  • Rate limit │  │    snapshots     │
     └───────────────┘  └──────────────────┘
                  │
     ┌────────────▼──────────────────────────────┐
     │           External Data Sources            │
     │                                            │
     │  🌤️  Open-Meteo API  (weather, free)       │
     │  🏥  WHO GHO API     (disease data, free)  │
     │  📍  Nominatim       (reverse geocoding)   │
     │  🔍  Open-Meteo Geo  (location search)     │
     └────────────────────────────────────────────┘
```

### Redis Caching Strategy

| Cache Key | TTL | Description |
|---|---|---|
| `weather:{lat}:{lon}` | 30 min | Weather fetch per location |
| `prediction:{disease}:{lat}:{lon}` | 1 hour | Prediction result per location |
| `rate:{ip}` | 1 min | Sliding window rate limiter (60 req/min) |

---

## 📁 Project Structure

```
ClimateHealth-AI/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry, lifespan, middleware
│   │   ├── api/v1/
│   │   │   ├── predictions.py       # POST & GET predictions
│   │   │   ├── weather.py           # Weather by coordinates
│   │   │   ├── locations.py         # Location search
│   │   │   └── health.py            # DB + Redis health check
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic settings from .env
│   │   │   ├── database.py          # Async SQLAlchemy + Neon
│   │   │   ├── cache.py             # Async Redis client
│   │   │   └── middleware.py        # IP rate limiting
│   │   ├── models/
│   │   │   ├── db_models.py         # ORM: Prediction, WeatherSnapshot
│   │   │   └── schemas.py           # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── weather.py           # Open-Meteo API client
│   │   │   ├── disease.py           # WHO GHO API client
│   │   │   ├── geocoding.py         # Location search + reverse geocode
│   │   │   └── predictor.py         # ML inference wrapper
│   │   └── ml/
│   │       ├── pipeline.py          # Feature engineering
│   │       ├── data_generator.py    # Synthetic training data
│   │       ├── train.py             # XGBoost model training
│   │       └── saved_models/        # Trained .pkl model files
│   ├── alembic/                     # DB migrations
│   ├── data/raw|processed/          # Training datasets
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx                 # Main dashboard
│   │   ├── layout.tsx               # Root layout + Leaflet CSS
│   │   ├── types.ts                 # Shared TypeScript interfaces
│   │   └── mockData.ts              # Offline demo seed data
│   ├── components/
│   │   ├── Map.tsx                  # Leaflet GIS map
│   │   ├── OutbreakCalculator.tsx   # Prediction input form
│   │   ├── TrendsChart.tsx          # Recharts correlation chart
│   │   └── AlertsPanel.tsx          # Real-time alert log
│   └── Dockerfile
├── nginx/nginx.conf
├── docker-compose.yml
└── README.md
```

---

## 📡 Data Sources

| Source | Data | Cost |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | Temperature, rainfall, humidity, wind speed, historical weather | Free, no key |
| [WHO GHO API](https://www.who.int/data/gho/info/gho-odata-api) | Malaria & cholera case records by country/year | Free |
| [Nominatim / OSM](https://nominatim.org/) | Reverse geocoding (lat/lon → city name) | Free |
| [Open-Meteo Geocoding](https://open-meteo.com/en/docs/geocoding-api) | City name → lat/lon search | Free |

---

## 🤖 ML Models

### Phase 1 — XGBoost Regression (current)

**Input features:**

| Feature | Source | Engineering |
|---|---|---|
| `temperature` | Open-Meteo | Raw °C |
| `rainfall` | Open-Meteo | Raw mm |
| `humidity` | Open-Meteo | Raw % |
| `wind_speed` | Open-Meteo | Raw km/h |
| `population_density` | User input | Raw /km² |
| `month_sin / month_cos` | System date | Cyclical encoding |
| `rain_humidity` | Derived | rainfall × humidity / 100 |
| `temp_humidity` | Derived | temperature × humidity / 100 |
| `heat_index` | Derived | Apparent temperature proxy |
| `flood_risk` | Derived | Binary: rainfall > 100mm |

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
  "predicted_at": "2025-01-15T10:30:00"
}
```

### `GET /api/v1/predictions`
List stored predictions, optionally filtered by disease.

| Param | Type | Description |
|---|---|---|
| `disease` | string | Filter: `malaria`, `flu`, `cholera` |
| `limit` | int | Max results (default: 50) |

### `GET /api/v1/weather`
Fetch current weather conditions for a coordinate.

| Param | Type | Description |
|---|---|---|
| `lat` | float | Latitude (-90 to 90) |
| `lon` | float | Longitude (-180 to 180) |

### `GET /api/v1/locations/search`
Search locations by name.

| Param | Type | Description |
|---|---|---|
| `q` | string | City or region name (min 2 chars) |

### `GET /health`
Returns DB and Redis connectivity status.

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Neon account](https://neon.tech/) (free tier works)

### 1. Clone & configure

```bash
git clone https://github.com/your-username/ClimateHealth-AI.git
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

## 🔧 Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string | `postgresql+asyncpg://user:pass@host/db?sslmode=require` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `APP_ENV` | Environment name | `development` / `production` |
| `SECRET_KEY` | App secret key | Random 32-char string |
| `WEATHER_CACHE_TTL` | Weather cache TTL (seconds) | `1800` |
| `PREDICTION_CACHE_TTL` | Prediction cache TTL (seconds) | `3600` |
| `DISEASE_CACHE_TTL` | WHO data cache TTL (seconds) | `86400` |

### Frontend (`frontend/.env`)

| Variable | Description | Example |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost/api/v1` |

---

## 🗺️ Roadmap

- [x] Phase 1 — XGBoost prediction engine (malaria, flu, cholera)
- [x] Interactive GIS dashboard with Leaflet maps
- [x] Real-time weather ingestion (Open-Meteo)
- [x] Redis caching + IP rate limiting
- [x] Neon PostgreSQL + async SQLAlchemy
- [x] Docker + Nginx + Redis deployment
- [ ] Phase 2 — LSTM / Prophet time-series forecasting
- [ ] Scheduled data ingestion (APScheduler)
- [ ] Email / SMS alert system for high-risk thresholds
- [ ] WHO disease data integration pipeline
- [ ] Additional diseases: dengue, pneumonia, meningitis
- [ ] Railway / cloud deployment

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ using open data from **Open-Meteo** and **WHO** • Designed to save lives through early warning

[![Open-Meteo](https://img.shields.io/badge/Data-Open--Meteo-00BFFF?style=flat-square)](https://open-meteo.com/)
[![WHO](https://img.shields.io/badge/Data-WHO_GHO-0093D5?style=flat-square)](https://www.who.int/data/gho)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>
