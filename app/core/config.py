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

    # Authentication — set ADMIN_API_KEY in Fly.io secrets to protect admin endpoints
    # and to bootstrap user API key creation via POST /api/v1/admin/keys
    ADMIN_API_KEY: str = ""

    # Observability — optional; error tracking disabled when empty
    SENTRY_DSN: str = ""

    # AI services — optional; endpoints return 503 when empty
    GROQ_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""

    # Notification services — optional; alerts silently skipped when empty
    SENDGRID_API_KEY: str = ""
    ALERT_FROM_EMAIL: str = "alerts@climatehealth.ai"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""


settings = Settings()
