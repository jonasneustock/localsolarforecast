# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

## [0.3.0] - 2025-10-08

### Added
- GitHub Actions workflow to build and publish Docker images to GHCR (multi-arch, cached).
- Background cache refresh task with configurable interval.
- Rate limiting middleware (per-IP) and request body size limits.
- Container hardening: non-root, read-only filesystem, no bytecode writes.

## [0.2.0] - 2025-10-08

### Added
- Redis response cache with TTL and `Cache-Control` headers.
- Prometheus `/metrics` endpoint and middleware for request latency/counts; cache hit metric.
- Config options: `REDIS_URL`, `CACHE_TTL`, `METRICS_ENABLED`.
- Tests for timestamp formatting (local tz), DST boundary handling, and numeric sanity (night=0, noon>morning/evening).

### Changed
- README updated with metrics and caching details.

## [0.1.0] - 2025-10-08

### Added
- P0: FastAPI service with `/estimate` and `/clearsky` endpoints.
- Clear-sky forecast engine using pvlib (Ineichen + Hay-Davies).
- Local timezone support (default `Europe/Berlin`).
- Forecast.Solar-compatible response schema for HA.
- `/health` endpoint and basic JSON logging.
- Dockerfile and docker-compose with Redis service.
- `pyproject.toml`, `README.md`, `LICENSE`, and `Makefile`.
- Basic contract tests for API shape and engine output types.
