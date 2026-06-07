from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


app = FastAPI(
    title="ClimateHealth AI",
    description="Global disease outbreak prediction from weather and environmental data",
    version="1.0.0",
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
