from fastapi import APIRouter, Query
from typing import Optional

from app.models.schemas import ForecastResponse, Message
from app.services.forecast_engine import compute_forecast


router = APIRouter()


@router.get(
    "/{lat}/{lon}/{declination}/{azimuth}/{kwp}",
    response_model=ForecastResponse,
)
def estimate(
    lat: float,
    lon: float,
    declination: float,
    azimuth: float,
    kwp: float,
    time: Optional[str] = Query(default="60m", description="Cadence, e.g. 15m, 30m, 60m"),
):
    try:
        result = compute_forecast(
            lat=lat,
            lon=lon,
            tilt=declination,
            azimuth_convention=azimuth,
            kwp=kwp,
            resolution=time,
            source="clearsky",  # P0: estimate == clearsky
        )
        return ForecastResponse(result=result, message=Message())
    except ValueError as e:
        return ForecastResponse(
            result={"watts": {}, "watt_hours": {}, "watt_hours_day": {}},
            message=Message(type="error", code=400, text=str(e)),
        )

