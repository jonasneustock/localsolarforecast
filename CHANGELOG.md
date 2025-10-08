# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

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

