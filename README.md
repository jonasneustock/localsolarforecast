# Local Forecast.Solar-compatible API

Drop-in, locally hosted API that mirrors key Forecast.Solar endpoints for Home Assistant. Ships as a Docker Compose stack.

No affiliation with Forecast.Solar. Interface-compatible only.

## Features (P0)

- Endpoints: `/estimate/{lat}/{lon}/{declination}/{azimuth}/{kwp}`, `/clearsky/...`
- Clear-sky forecast using pvlib (Ineichen + Hay-Davies)
- Local timezone timestamps (default `Europe/Berlin`)
- Response schema compatible with HA’s Forecast.Solar integration
- Health check at `/health`
- Prometheus metrics at `/metrics` (toggle with `METRICS_ENABLED`)
- Redis response caching with `Cache-Control` headers
- Rate limiting (per IP, configurable)

## Quickstart (Docker Compose)

Prereqs: Docker & Docker Compose.

```bash
docker compose up --build
# then in another shell
curl "http://localhost:8080/clearsky/54.32/10.12/30/0/5?time=60m" | jq .
curl "http://localhost:8080/metrics" | head -n 20
```

## API

Path params: `lat`, `lon`, `declination` (tilt from horizontal, deg), `azimuth` (0=South, +E, -W), `kwp` (kWp DC).

Query: `time` cadence like `15m`, `30m`, `60m`.

Response example:

```json
{
  "result": {
    "watts": {"YYYY-MM-DD HH:MM:SS": 123.0},
    "watt_hours": {"YYYY-MM-DD HH:MM:SS": 456.0},
    "watt_hours_day": {"YYYY-MM-DD": 7890.0}
  },
  "message": {"type":"success","code":0,"text":""}
}
```

Notes:
- Timestamps are local time (configurable via `TZ`).
- For P0, `/estimate` uses the clear-sky engine; weather-aware source is P1.
- Responses are cached in Redis with `Cache-Control: public, max-age=...`.
- Container runs as non-root and with a read-only filesystem.

## Configuration

Environment variables (see `docker-compose.yml`):

- `TZ` (default `Europe/Berlin`)
- `SYSTEM_LOSS` (fraction, default `0.14`)
- `DEFAULT_RESOLUTION` (e.g., `60m`)
- `MAX_HORIZON_DAYS` (default `6`)
- `REDIS_URL` (default `redis://redis:6379/0`)
- `CACHE_TTL` (seconds, default `1800`)
- `METRICS_ENABLED` (default `true`)
- `RATE_LIMIT_PER_MINUTE` (default `120`)
- `REFRESH_ENABLED` (default `true`)
- `REFRESH_INTERVAL_SECONDS` (default `300`)

## Development

Install (optional) and run locally:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload --port 8080
```

Run tests:

```bash
pytest
```

## License

Apache-2.0 for this repository; pvlib is licensed separately — see pvlib documentation.
