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


settings = Settings()

