from datetime import datetime
import pytz

import pytest

from app.services import forecast_engine
from app.util import timeindex


@pytest.fixture
def freeze_time(monkeypatch):
    def _freeze(dt: datetime, tz: str):
        tzinfo = pytz.timezone(tz)
        fixed = tzinfo.localize(dt)

        def fake_now_local(tz_name: str):
            assert tz_name == tz
            return fixed

        monkeypatch.setattr(timeindex, "now_local", fake_now_local)

    return _freeze


def test_timestamps_are_local_and_string_keys(freeze_time):
    freeze_time(datetime(2024, 6, 21, 0, 0, 0), "Europe/Berlin")
    out = forecast_engine.compute_forecast(
        lat=54.32, lon=10.12, tilt=30, azimuth_convention=0, kwp=5, resolution="60m"
    )
    watts = out["watts"]
    # Ensure keys are string timestamps
    k = next(iter(watts))
    assert isinstance(k, str)
    # Check a known local-time formatted key exists for the start hour
    assert "2024-06-21 00:00:00" in watts


def test_dst_boundary_has_valid_series(freeze_time):
    # Start near EU DST start (2024-03-31)
    freeze_time(datetime(2024, 3, 31, 0, 0, 0), "Europe/Berlin")
    out = forecast_engine.compute_forecast(
        lat=52.52, lon=13.405, tilt=30, azimuth_convention=0, kwp=5, resolution="60m"
    )
    watts = out["watts"]
    # Ensure series spans the day and contains local timestamps before/after DST jump
    assert "2024-03-31 01:00:00" in watts
    # 02:00 local jumps to 03:00; presence of 03:00 is expected
    assert "2024-03-31 03:00:00" in watts


def test_numeric_sanity_day_curve(freeze_time):
    freeze_time(datetime(2024, 6, 21, 0, 0, 0), "Europe/Berlin")
    out = forecast_engine.compute_forecast(
        lat=48.137, lon=11.575, tilt=30, azimuth_convention=0, kwp=5, resolution="60m"
    )
    watts = out["watts"]
    # Nighttime hours should be ~0
    assert float(watts["2024-06-21 00:00:00"]) == 0.0
    # Noon should be higher than morning and evening
    noon = float(watts.get("2024-06-21 12:00:00", 0.0))
    morning = float(watts.get("2024-06-21 09:00:00", 0.0))
    evening = float(watts.get("2024-06-21 18:00:00", 0.0))
    assert noon > morning
    assert noon > evening
    # Upper bound by nameplate
    assert noon <= 5000.0

