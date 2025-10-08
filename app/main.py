from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.estimate import router as estimate_router
from app.api.clearsky import router as clearsky_router
from app.core.metrics import MetricsMiddleware, metrics_endpoint
from app.core.refresh import refresher_loop
from app.core.security import RateLimitMiddleware, BodySizeLimitMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="Local Forecast.Solar-compatible API", version="0.3.0")

    # CORS: allow all by default; can be restricted via env later
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security middleware
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=1024 * 4)
    app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)

    if settings.metrics_enabled:
        app.add_middleware(MetricsMiddleware)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    if settings.metrics_enabled:
        app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)

    app.include_router(estimate_router, prefix="/estimate", tags=["estimate"])
    app.include_router(clearsky_router, prefix="/clearsky", tags=["clearsky"])

    return app


app = create_app()

# Start background refresher loop
import asyncio

asyncio.get_event_loop().create_task(refresher_loop())
