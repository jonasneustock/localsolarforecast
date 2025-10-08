import pandas as pd

from app.services.forecast_engine import compute_forecast


def test_engine_output_types():
    out = compute_forecast(
        lat=54.32, lon=10.12, tilt=30, azimuth_convention=0, kwp=5, resolution="60m"
    )
    assert set(out.keys()) == {"watts", "watt_hours", "watt_hours_day"}
    assert isinstance(next(iter(out["watts"].values()), 0.0), float)

