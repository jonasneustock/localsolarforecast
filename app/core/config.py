from pydantic import BaseModel
import os


class Settings(BaseModel):
    timezone: str = os.getenv("TZ", "Europe/Berlin")
    default_resolution: str = os.getenv("DEFAULT_RESOLUTION", "60m")
    system_loss: float = float(os.getenv("SYSTEM_LOSS", "0.14"))  # fraction
    max_horizon_days: int = int(os.getenv("MAX_HORIZON_DAYS", "6"))
    log_level: str = os.getenv("LOG_LEVEL", "info")
    service_name: str = "solar-forecast-local"
    http_host: str = os.getenv("HOST", "0.0.0.0")
    http_port: int = int(os.getenv("PORT", "8080"))
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL", "1800"))  # 30 minutes
    metrics_enabled: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    refresh_enabled: bool = os.getenv("REFRESH_ENABLED", "true").lower() == "true"
    refresh_interval_seconds: int = int(os.getenv("REFRESH_INTERVAL_SECONDS", "300"))
    weather_enabled: bool = os.getenv("WEATHER_ENABLED", "true").lower() == "true"
    weather_ttl_seconds: int = int(os.getenv("WEATHER_TTL", "1800"))
    weather_alpha: float = float(os.getenv("WEATHER_ALPHA", "0.75"))
    weather_timeout_seconds: float = float(os.getenv("WEATHER_TIMEOUT", "8.0"))
    open_meteo_base_url: str = os.getenv(
        "OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast"
    )


settings = Settings()
