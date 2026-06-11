from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    OPEN_METEO_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1"
    WHO_BASE_URL: str = "https://ghoapi.azureedge.net/api"
    WORLD_BANK_BASE_URL: str = "https://api.worldbank.org/v2"

    WEATHER_CACHE_TTL: int = 1800
    PREDICTION_CACHE_TTL: int = 3600
    DISEASE_CACHE_TTL: int = 86400


settings = Settings()
