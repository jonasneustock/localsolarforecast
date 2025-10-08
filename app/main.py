from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.estimate import router as estimate_router
from app.api.clearsky import router as clearsky_router


def create_app() -> FastAPI:
    app = FastAPI(title="Local Forecast.Solar-compatible API", version="0.1.0")

    # CORS: allow all by default; can be restricted via env later
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(estimate_router, prefix="/estimate", tags=["estimate"])
    app.include_router(clearsky_router, prefix="/clearsky", tags=["clearsky"])

    return app


app = create_app()

