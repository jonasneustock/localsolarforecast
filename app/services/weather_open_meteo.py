"""Open-Meteo weather adapter with Redis caching and CMF factor.

Fetches hourly weather and derives a scaling factor to adjust clear-sky
irradiance. Falls back gracefully if network/cache is unavailable.
"""

from __future__ import annotations

import json
from typing import Optional, Dict, Any

import httpx
import pandas as pd

from app.core.config import settings
from app.services.cache import _get_client as get_redis_client


def _weather_cache_key(lat: float, lon: float, tz: str, start_date: str, end_date: str) -> str:
    return f"weather:om:{round(lat,3)}:{round(lon,3)}:{tz}:{start_date}:{end_date}"


def _to_dataframe(payload: Dict[str, Any], tz: str) -> Optional[pd.DataFrame]:
    try:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time")
        if not times:
            return None
        df = pd.DataFrame({k: v for k, v in hourly.items() if k != "time"})
        idx = pd.DatetimeIndex(pd.to_datetime(times)).tz_localize(tz)
        df.index = idx
        return df
    except Exception:
        return None


def fetch_open_meteo(lat: float, lon: float, tz: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    client = get_redis_client()
    key = _weather_cache_key(lat, lon, tz, start_date, end_date)
    if client:
        try:
            cached = client.get(key)
            if cached:
                data = json.loads(cached)
                df = _to_dataframe(data, tz)
                if df is not None:
                    return df
        except Exception:
            pass

    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(
            [
                "cloudcover",
                "shortwave_radiation",
                "direct_radiation",
                "diffuse_radiation",
                "direct_normal_irradiance",
                "temperature_2m",
                "windspeed_10m",
            ]
        ),
    }

    try:
        with httpx.Client(timeout=settings.weather_timeout_seconds) as http:
            r = http.get(settings.open_meteo_base_url, params=params)
            if r.status_code != 200:
                return None
            data = r.json()
    except Exception:
        return None

    if client:
        try:
            client.setex(key, settings.weather_ttl_seconds, json.dumps(data))
        except Exception:
            pass

    return _to_dataframe(data, tz)


def cmf_factor_from_weather(
    index: pd.DatetimeIndex,
    tz: str,
    cs_ghi: pd.Series,
    weather_df: Optional[pd.DataFrame],
    alpha: float,
) -> Optional[pd.Series]:
    if weather_df is None or len(weather_df) == 0:
        return None
    # Prefer shortwave_radiation-based factor if available
    if "shortwave_radiation" in weather_df.columns:
        sw = weather_df["shortwave_radiation"].astype(float)
        # Map clearsky GHI to weather timestamps
        cs_on_w = cs_ghi.reindex(weather_df.index, method="nearest")
        # avoid div by zero at night
        with pd.option_context("mode.use_inf_as_na", True):
            ratio = (sw / cs_on_w.clip(lower=1e-6)).fillna(0.0)
        factor = ratio.clip(lower=0.0, upper=1.0)
    elif "cloudcover" in weather_df.columns:
        cc = weather_df["cloudcover"].astype(float).clip(lower=0.0, upper=100.0)
        factor = (1.0 - alpha * (cc / 100.0)).clip(lower=0.0, upper=1.0)
    else:
        return None

    # Align factor to requested index
    factor = factor.reindex(index, method="nearest")
    factor = factor.fillna(method="ffill").fillna(method="bfill").fillna(0.0)
    return factor

