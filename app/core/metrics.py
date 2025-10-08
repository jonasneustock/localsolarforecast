from __future__ import annotations

import time
from typing import Callable

from prometheus_client import Counter, Histogram, CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import Response


registry = CollectorRegistry()

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
    registry=registry,
)

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["endpoint"],
    registry=registry,
)


class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "").upper()
        route = scope.get("route")
        path_template = getattr(route, "path", scope.get("path", "/"))

        start = time.perf_counter()
        status_container = {}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_container["status"] = message["status"]
            await send(message)

        await self.app(scope, receive, send_wrapper)
        duration = time.perf_counter() - start
        status = str(status_container.get("status", 0))

        http_requests_total.labels(method=method, path=path_template, status=status).inc()
        http_request_duration_seconds.labels(method=method, path=path_template).observe(duration)


def metrics_endpoint(_: Request) -> Response:
    output = generate_latest(registry)
    return Response(content=output, media_type=CONTENT_TYPE_LATEST)

