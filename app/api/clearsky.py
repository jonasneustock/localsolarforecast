from fastapi import APIRouter, Query, Response
from typing import Optional

from app.models.schemas import ForecastResponse, Message
from app.services.forecast_engine import compute_forecast
from app.services.cache import make_key, get_cached, set_cached
from app.core.config import settings
from app.core.metrics import cache_hits_total
from app.models.spec import ForecastSpec
from app.services.warmup import track_spec


router = APIRouter()


@router.get(
    "/{lat}/{lon}/{declination}/{azimuth}/{kwp}",
    response_model=ForecastResponse,
)
def clearsky(
    lat: float,
    lon: float,
    declination: float,
    azimuth: float,
    kwp: float,
    time: Optional[str] = Query(
        default="60m",
        description="Cadence, e.g. 15m, 30m, 60m",
        pattern=r"^(5|10|15|30|60)m$",
    ),
    response: Response,
):
    try:
        key = make_key(
            endpoint="clearsky",
            lat=lat,
            lon=lon,
            tilt=declination,
            azimuth=azimuth,
            kwp=kwp,
            resolution=time or settings.default_resolution,
            source="clearsky",
        )
        cached = get_cached(key)
        if cached:
            response.headers["X-Cache"] = "HIT"
            response.headers["Cache-Control"] = f"public, max-age={settings.cache_ttl_seconds}"
            cache_hits_total.labels(endpoint="clearsky").inc()
            track_spec(
                key,
                ForecastSpec(
                    endpoint="clearsky",
                    lat=lat,
                    lon=lon,
                    tilt=declination,
                    azimuth=azimuth,
                    kwp=kwp,
                    resolution=time or settings.default_resolution,
                    source="clearsky",
                ),
            )
            return ForecastResponse(result=cached, message=Message())

        result = compute_forecast(
            lat=lat,
            lon=lon,
            tilt=declination,
            azimuth_convention=azimuth,
            kwp=kwp,
            resolution=time,
            source="clearsky",
        )
        set_cached(key, result)
        response.headers["X-Cache"] = "MISS"
        response.headers["Cache-Control"] = f"public, max-age={settings.cache_ttl_seconds}"
        track_spec(
            key,
            ForecastSpec(
                endpoint="clearsky",
                lat=lat,
                lon=lon,
                tilt=declination,
                azimuth=azimuth,
                kwp=kwp,
                resolution=time or settings.default_resolution,
                source="clearsky",
            ),
        )
        return ForecastResponse(result=result, message=Message())
    except ValueError as e:
        return ForecastResponse(
            result={"watts": {}, "watt_hours": {}, "watt_hours_day": {}},
            message=Message(type="error", code=400, text=str(e)),
        )
