"""Redis response cache layer.

Used to cache API responses keyed by input parameters and time horizon.
Falls back to no-op if Redis is unavailable.
"""

from __future__ import annotations

import json
import hashlib
from typing import Optional, Dict, Any

import redis

from app.core.config import settings
from app.util.timeindex import parse_resolution, now_local


_client: Optional[redis.Redis] = None


def _get_client() -> Optional[redis.Redis]:
    global _client
    if _client is not None:
        return _client
    try:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
        # Ping to confirm connectivity
        _client.ping()
        return _client
    except Exception:
        return None


def _aligned_start_key(resolution: str) -> str:
    freq = parse_resolution(resolution)
    now = now_local(settings.timezone)
    if freq.endswith("min"):
        minutes = int(freq.replace("min", ""))
        minute = (now.minute // minutes) * minutes
        now = now.replace(minute=minute, second=0, microsecond=0)
    return now.strftime("%Y-%m-%dT%H:%M:%S%z")


def make_key(
    *,
    endpoint: str,
    lat: float,
    lon: float,
    tilt: float,
    azimuth: float,
    kwp: float,
    resolution: str,
    source: str,
) -> str:
    parts = {
        "v": 1,
        "ep": endpoint,
        "lat": round(float(lat), 5),
        "lon": round(float(lon), 5),
        "tilt": round(float(tilt), 2),
        "az": round(float(azimuth), 2),
        "kwp": round(float(kwp), 3),
        "res": parse_resolution(resolution),
        "src": source,
        "tz": settings.timezone,
        "days": settings.max_horizon_days,
        "start": _aligned_start_key(resolution),
    }
    s = json.dumps(parts, sort_keys=True)
    digest = hashlib.sha256(s.encode()).hexdigest()
    return f"resp:{digest}"


def get_cached(key: str) -> Optional[Dict[str, Any]]:
    client = _get_client()
    if not client:
        return None
    data = client.get(key)
    if not data:
        return None
    return json.loads(data)


def set_cached(key: str, value: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
    client = _get_client()
    if not client:
        return
    ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
    client.setex(name=key, time=ttl, value=json.dumps(value))

