from __future__ import annotations

import asyncio
from typing import Callable

from app.core.config import settings
from app.models.spec import ForecastSpec
from app.services.forecast_engine import compute_forecast
from app.services.cache import set_cached, make_key
from app.services.warmup import list_specs


async def refresh_once() -> int:
    specs = list_specs(max_age_seconds=settings.cache_ttl_seconds)
    count = 0
    for spec in specs:
        try:
            result = compute_forecast(
                lat=spec.lat,
                lon=spec.lon,
                tilt=spec.tilt,
                azimuth_convention=spec.azimuth,
                kwp=spec.kwp,
                resolution=spec.resolution,
                source=spec.source,
            )
            key = make_key(
                endpoint=spec.endpoint,
                lat=spec.lat,
                lon=spec.lon,
                tilt=spec.tilt,
                azimuth=spec.azimuth,
                kwp=spec.kwp,
                resolution=spec.resolution,
                source=spec.source,
            )
            set_cached(key, result)
            count += 1
        except Exception:
            # Swallow to keep loop healthy; observability via logs could be added
            pass
    return count


async def refresher_loop():
    if not settings.refresh_enabled:
        return
    interval = max(30, settings.refresh_interval_seconds)
    while True:
        await refresh_once()
        await asyncio.sleep(interval)

