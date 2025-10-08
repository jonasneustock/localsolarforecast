from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
import pvlib

from app.core.config import settings
from app.models.site import Site
from app.util.timeindex import time_index
from app.util.units import clamp


def _validate_inputs(site: Site) -> None:
    if not (-90 <= site.lat <= 90):
        raise ValueError("lat out of range [-90,90]")
    if not (-180 <= site.lon <= 180):
        raise ValueError("lon out of range [-180,180]")
    if not (0 <= site.tilt <= 90):
        raise ValueError("declination/tilt out of range [0,90]")
    if not (0 < site.kwp <= 1000):
        raise ValueError("kwp must be (0,1000]")


def _build_index(resolution: str) -> pd.DatetimeIndex:
    return time_index(settings.timezone, settings.max_horizon_days, resolution)


def _compute_clearsky(site: Site, index: pd.DatetimeIndex) -> pd.DataFrame:
    location = pvlib.location.Location(site.lat, site.lon, tz=settings.timezone)
    cs = location.get_clearsky(index, model="ineichen")  # ghi, dni, dhi

    solar_pos = pvlib.solarposition.get_solarposition(index, site.lat, site.lon)

    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=site.tilt,
        surface_azimuth=site.to_pvlib_azimuth(),
        dni=cs["dni"],
        ghi=cs["ghi"],
        dhi=cs["dhi"],
        solar_zenith=solar_pos["zenith"],
        solar_azimuth=solar_pos["azimuth"],
        model="haydavies",
        albedo=0.2,
    )

    # Ambient fallback assumptions
    temp_air = pd.Series(20.0, index=index)
    wind_speed = pd.Series(1.0, index=index)

    temp_cell = pvlib.temperature.sapm_cell(
        poa_global=poa["poa_global"],
        temp_air=temp_air,
        wind_speed=wind_speed,
        a=-3.56,  # SAPM NOCT-like coefficients
        b=-0.075,
        deltaT=3,
    )

    # PVWatts-like DC power model (simple)
    pdc0 = site.kwp * 1000.0
    gamma_pdc = -0.004  # per deg C
    poa_kw = poa["poa_global"].clip(lower=0) / 1000.0
    pdc = pdc0 * poa_kw * (1 + gamma_pdc * (temp_cell - 25.0))
    pdc = pdc.clip(lower=0)

    # System losses and clipping at nameplate
    ac = pdc * (1.0 - settings.system_loss)
    ac = ac.clip(lower=0, upper=pdc0)

    df = pd.DataFrame({"ac": ac})
    return df


def _serialize_timeseries(series: pd.Series) -> Dict[str, float]:
    # Format as "YYYY-MM-DD HH:MM:SS" keys in local tz
    out: Dict[str, float] = {}
    for ts, val in series.items():
        key = ts.strftime("%Y-%m-%d %H:%M:%S")
        out[key] = float(round(val, 3))
    return out


def _energy_wh(ac_w: pd.Series) -> pd.Series:
    # Integrate power over time increments to Wh
    if len(ac_w.index) < 2:
        return pd.Series([0.0] * len(ac_w), index=ac_w.index)
    deltas = ac_w.index.to_series().diff().dt.total_seconds().fillna(0) / 3600.0
    inc_wh = ac_w * deltas
    cum_wh = inc_wh.cumsum().fillna(0)
    return cum_wh


def _daily_wh(ac_w: pd.Series) -> pd.Series:
    # Daily energy totals in Wh
    # Compute incremental Wh per step and sum per day
    if len(ac_w.index) < 2:
        return pd.Series(dtype=float)
    deltas = ac_w.index.to_series().diff().dt.total_seconds().fillna(0) / 3600.0
    inc_wh = (ac_w * deltas).fillna(0)
    daily = inc_wh.groupby(ac_w.index.strftime("%Y-%m-%d")).sum()
    return daily


def compute_forecast(
    *,
    lat: float,
    lon: float,
    tilt: float,
    azimuth_convention: float,
    kwp: float,
    resolution: str,
    source: str = "clearsky",
) -> Dict[str, Dict[str, float]]:
    site = Site(
        lat=lat,
        lon=lon,
        tilt=tilt,
        azimuth_conv=azimuth_convention,
        kwp=kwp,
        resolution=resolution or settings.default_resolution,
    )
    _validate_inputs(site)
    idx = _build_index(site.resolution)

    if source != "clearsky":
        raise ValueError("Only 'clearsky' source supported in P0")

    df = _compute_clearsky(site, idx)
    watts = df["ac"].round(3)
    wh_cum = _energy_wh(watts)
    wh_day = _daily_wh(watts)

    return {
        "watts": _serialize_timeseries(watts),
        "watt_hours": _serialize_timeseries(wh_cum),
        "watt_hours_day": {k: float(round(v, 3)) for k, v in wh_day.items()},
    }

