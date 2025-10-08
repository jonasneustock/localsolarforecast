from __future__ import annotations

import time
from typing import Optional, Tuple

from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse

from app.core.config import settings
from app.services.cache import _get_client as get_redis_client


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = 4096):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        # content-length header is lowercase bytes key b'content-length'
        cl = headers.get(b"content-length")
        if cl is not None:
            try:
                size = int(cl.decode())
                if size > self.max_bytes:
                    await JSONResponse(
                        status_code=413,
                        content={
                            "result": {"watts": {}, "watt_hours": {}, "watt_hours_day": {}},
                            "message": {"type": "error", "code": 413, "text": "Request entity too large"},
                        },
                    )(scope, receive, send)
                    return
            except Exception:
                pass
        await self.app(scope, receive, send)


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, limit_per_minute: int = 120):
        self.app = app
        self.limit = max(1, limit_per_minute)
        # in-memory fallback store: {window_start_epoch: {ip: count}}
        self._window_start = int(time.time() // 60)
        self._local_counts: dict[str, int] = {}

    def _client_ip(self, scope: Scope) -> str:
        headers = dict(scope.get("headers") or [])
        xff = headers.get(b"x-forwarded-for")
        if xff:
            ip = xff.decode().split(",")[0].strip()
            if ip:
                return ip
        client = scope.get("client") or (None,)
        return client[0] or "unknown"

    def _redis_allow(self, ip: str) -> Tuple[bool, int]:
        r = get_redis_client()
        if not r:
            return False, 0
        key = f"rl:{ip}"
        try:
            cur = r.incr(key)
            if cur == 1:
                # first increment, set window TTL 60s
                r.expire(key, 60)
            ttl = r.ttl(key)
            allowed = cur <= self.limit
            return allowed, max(0, int(ttl))
        except Exception:
            return False, 0

    def _local_allow(self, ip: str) -> Tuple[bool, int]:
        now_window = int(time.time() // 60)
        if now_window != self._window_start:
            self._window_start = now_window
            self._local_counts = {}
        count = self._local_counts.get(ip, 0) + 1
        self._local_counts[ip] = count
        allowed = count <= self.limit
        # approximate remaining seconds in window
        ttl = int(60 - (time.time() % 60))
        return allowed, ttl

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        ip = self._client_ip(scope)
        allowed, ttl = self._redis_allow(ip)
        if allowed is False and ttl == 0:
            # Redis not available -> use local
            allowed, ttl = self._local_allow(ip)
        if not allowed:
            await JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(ttl),
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                },
                content={
                    "result": {"watts": {}, "watt_hours": {}, "watt_hours_day": {}},
                    "message": {
                        "type": "error",
                        "code": 429,
                        "text": "Too Many Requests",
                    },
                },
            )(scope, receive, send)
            return
        await self.app(scope, receive, send)

