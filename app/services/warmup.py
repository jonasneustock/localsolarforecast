from __future__ import annotations

import threading
import time
from typing import Dict, List

from app.models.spec import ForecastSpec


_lock = threading.Lock()
_specs: Dict[str, ForecastSpec] = {}
_timestamps: Dict[str, float] = {}


def track_spec(key: str, spec: ForecastSpec) -> None:
    with _lock:
        _specs[key] = spec
        _timestamps[key] = time.time()


def list_specs(max_age_seconds: int | None = None) -> List[ForecastSpec]:
    now = time.time()
    with _lock:
        keys = list(_specs.keys())
        result: List[ForecastSpec] = []
        for k in keys:
            if max_age_seconds is not None and (now - _timestamps.get(k, 0)) > max_age_seconds:
                # drop stale
                _specs.pop(k, None)
                _timestamps.pop(k, None)
                continue
            result.append(_specs[k])
        return result

