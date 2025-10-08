from datetime import datetime, timedelta
import pandas as pd
import pytz


def parse_resolution(res: str) -> str:
    res = res.strip().lower()
    if res.endswith("m"):
        minutes = int(res[:-1])
        if minutes in (5, 10, 15, 30, 60):
            return f"{minutes}min"
    # fallback to 60 minutes
    return "60min"


def now_local(tz_name: str) -> datetime:
    tz = pytz.timezone(tz_name)
    return datetime.now(tz)


def time_index(
    tz_name: str,
    horizon_days: int,
    resolution: str,
) -> pd.DatetimeIndex:
    freq = parse_resolution(resolution)
    now = now_local(tz_name)
    # Align to frequency start
    if freq.endswith("min"):
        mins = int(freq.replace("min", ""))
        minute = (now.minute // mins) * mins
        now = now.replace(minute=minute, second=0, microsecond=0)
    start = now
    end = start + timedelta(days=horizon_days)
    return pd.date_range(start=start, end=end, freq=freq, tz=tz_name, inclusive="both")

