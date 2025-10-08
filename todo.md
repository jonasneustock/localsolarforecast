# todo.md — Local Forecast.Solar-compatible API (Dockerized)

> Objective: Stand up a **drop-in, locally hosted** API that mirrors Forecast.Solar’s key endpoints and payloads so Home Assistant (HA) can consume it with **zero (or minimal)** config change. Execution driven, scope-controlled, production-grade.

---

## P0 — Program setup & governance

- [x] Define scope boundary (MVP = `/estimate`, `/clearsky`; P1 = `/history`, multi-plane).
- [x] Select licenses (Apache-2.0 for our code; respect pvlib license).
- [x] Repo bootstrap:
  - [x] Create repo `solar-forecast-local`.
  - [x] Enable branch protection, PR checks, semantic versioning (tags).
  - [x] Add GitHub Actions workflow to build/push Docker image to GHCR.
  - [x] Add issue templates & PR template.
- [x] Decide API compatibility target (HA uses Forecast.Solar public endpoints/fields).
- [x] Add disclaimer (no affiliation; interface-compatible only).

---

## P0 — System architecture (design freeze)

- [x] Confirm target stack: Python 3.11, FastAPI, uvicorn, pvlib, Redis, Docker, docker-compose.
- [x] Define service boundaries:
  - `api` (routes, validation)
  - `engine` (pvlib pipeline)
  - `weather` (Open-Meteo adapter; pluggable)
  - `cache` (Redis)
  - `calibration` (optional, site-specific tuning)
- [x] Timezone policy: default `Europe/Berlin`, override via env.
- [x] Observability baseline: `/health`, structured logs, Prometheus metrics (P1).

---

## P0 — API contract (HA compatibility)

- [x] Implement endpoints with **Forecast.Solar-shaped** responses:
  - [x] `GET /estimate/{lat}/{lon}/{declination}/{azimuth}/{kwp}`
  - [x] `GET /clearsky/{lat}/{lon}/{declination}/{azimuth}/{kwp}`
- [x] Response schema (must match HA expectations):
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
- [x] Conventions:
  - [x] Timestamps in **local time**, string keys.
  - [x] Resolution default 60-min; query `?time=15m` accepted (round to available weather cadence).
  - [x] Azimuth convention: **0 = South, +E, −W** (mirror Forecast.Solar/HA).
  - [x] Declination = tilt in degrees from horizontal.

---

## P0 — Repo structure & scaffolding

- [x] Project tree
  ```
  app/
    api/
      __init__.py
      estimate.py
      clearsky.py
    core/
      config.py
      logging.py
    models/
      site.py
      schemas.py
    services/
      forecast_engine.py
      weather_open_meteo.py
      cache.py
      calibration.py
    util/
      timeindex.py
      units.py
  tests/
    test_api_contract.py
    test_engine_basics.py
    data/
  Dockerfile
  docker-compose.yml
  pyproject.toml
  README.md
  LICENSE
  ```
- [x] `pyproject.toml` with pinned deps (fastapi, uvicorn, pvlib, httpx, pydantic, redis, pytz, numpy, pandas).
- [x] `README.md` quickstart.

---

## P0 — Core engine (clear-sky MVP)

- [x] Create time index for [now → +6 days] at selected cadence (local tz).
- [x] Solar position via pvlib SPA.
- [x] Clear-sky irradiance (Ineichen + Linke turbidity).
- [x] Transposition to plane (Hay-Davies or Perez).
- [x] Module temperature model (SAPM/NOCT with ambient fallback).
- [x] DC → AC conversion with generic CEC module & Sandia inverter; cap at `kWp`; apply scalar system loss.
- [x] Compute:
  - [x] `watts` (AC W time-series)
  - [x] cumulative `watt_hours`
  - [x] daily totals `watt_hours_day`
- [x] Package output to API schema.

---

## P0 — API layer

- [x] FastAPI app with routers `/estimate`, `/clearsky`.
- [x] Input validation: ranges for lat, lon, declination, azimuth, kWp.
- [x] Error handling to Forecast.Solar-like `message` block.
- [x] Add CORS (optional).
- [x] `/health` endpoint.

---

## P0 — Containerization & ops

- [x] `Dockerfile` (slim Python base, non-root user, uvicorn worker).
- [x] `docker-compose.yml` with:
  - [x] `solar-api` (port 8080)
  - [x] `redis` (7-alpine)
- [x] `TZ` env wiring; graceful shutdown; healthcheck.
- [x] Makefile: `make dev`, `make test`, `make build`, `make run`.

---

## P0 — Contract tests (black-box)

- [x] Unit tests for schema compliance (keys, types).
- [ ] Deterministic tests for clear-sky (fixed inputs, snapshot outputs).
- [x] Timestamp formatting tests (local tz, DST boundaries).
- [x] Numeric sanity checks (nighttime = 0; noon > morning/evening).

**Curl smoke tests**
```bash
curl "http://localhost:8080/estimate/54.32/10.12/30/0/5?time=60m" | jq .
curl "http://localhost:8080/clearsky/54.32/10.12/30/0/5" | jq .
```

---

## P1 — Weather-aware forecast (Open-Meteo)

- [ ] Weather adapter `weather_open_meteo.py`:
  - [ ] Pull hourly cloud cover, temp, wind (and direct/global if available).
  - [ ] Local cache TTL (e.g., 30–60 min).
- [ ] Cloud Modification Factor (CMF) scaler:
  - [ ] Map cloud cover → scale GHI/DNI/DHI (α configurable).
  - [ ] Fallback to clear-sky if gaps.
- [ ] Recompute POA & AC with weather-adjusted irradiance.
- [ ] Add query param `?source=open-meteo|clearsky`.

---

## P1 — Caching & scheduling

- [x] Redis response cache keyed by `(lat,lon,decl,az,kwp,res,source,date_range)`.
- [x] Background refresh task (every N minutes).
- [x] Cache-control headers (short max-age).

---

## P1 — Multi-plane support

- [ ] Accept `planes` via config file (`/config/site.yml`) or query token:
  ```yaml
  planes:
    - { tilt: 30, azimuth: -90, kwp: 4.0 }
    - { tilt: 30, azimuth:  90, kwp: 4.0 }
  system_loss: 0.14
  albedo: 0.2
  ```
- [ ] Sum per-plane AC outputs → single combined response.
- [ ] Validate total `kWp` = sum of planes.

---

## P1 — `/history` endpoint

- [ ] Endpoint: `GET /history/{lat}/{lon}/{decl}/{az}/{kwp}`
- [ ] Strategy options:
  - [ ] Rolling DB from your live inverter logs (preferred).
  - [ ] Or climatology proxy (monthly average day curves).
- [ ] Output: daily Wh time-series in same schema.

---

## P1 — Observability & SRE

- [x] Structured JSON logging (request id, latency, cache hit/miss).
- [x] `/metrics` (Prometheus) for QPS, p95 latency, error rate, cache stats.
- [ ] Tracing hooks (OpenTelemetry; optional).

---

## P1 — Security & compliance

- [x] Rate limiting (basic token bucket).
- [x] Input sanitization & length limits.
- [x] Container runs non-root; read-only FS where possible.

---

## P1 — Home Assistant integration validation

- [ ] Replace Forecast.Solar base URL in HA config with local service:
  ```yaml
  sensor:
    - platform: rest
      name: Local Solar Forecast
      resource: "http://solar-forecast.local:8080/estimate/{lat}/{lon}/{decl}/{az}/{kwp}"
  ```
- [ ] Validate entities populate (`watts`, `watt_hours_day`).
- [ ] Regression test after HA core updates.

---

## P2 — Calibration & quality uplift

- [ ] Add `/calibrate` job that fits α (cloud scaling) and loss factors against inverter telemetry (least squares on daytime hours).
- [ ] Per-site profiles stored in SQLite.
- [ ] Optional: plug higher-fidelity sources (ICON-D2/ECMWF) via adapter interface.
- [ ] Confidence bands in response (p10/p50/p90) — optional fields.

---

## P2 — Packaging & discovery

- [ ] Avahi/mDNS advertising `solar-forecast.local`.
- [ ] Versioned Docker image releases (`:v0.1.0`, `:latest`).
- [ ] Helm chart (optional).

---

## P2 — Documentation & DX

- [ ] OpenAPI `/docs` with examples.
- [ ] “HA playbook” doc page.
- [ ] Troubleshooting guide (TZ issues, DST, cache misses, weather gaps).
- [ ] Performance guide (res vs CPU, cache sizing).

---

## P2 — Resilience & edge cases

- [ ] Nighttime handling hard-zero with hysteresis around sunrise/sunset.
- [ ] Leap day, DST transition correctness.
- [ ] Invalid coordinate hardening (polar edge behavior).
- [ ] Empty result behavior (graceful message block).

---

## Engineering prompts (use a code-capable GPT to accelerate)

- [ ] **API skeleton generation**
  ```
  Generate a FastAPI service with endpoints
  /estimate/{lat}/{lon}/{decl}/{az}/{kwp} and /clearsky/...
  Return Forecast.Solar-shaped JSON (watts, watt_hours, watt_hours_day).
  Use pvlib to compute clear-sky → POA → AC power.
  Add Dockerfile and docker-compose with Redis.
  ```
- [ ] **pvlib pipeline**
  ```
  Given lat, lon, tilt, azimuth, kWp, produce AC power time-series at 60-min resolution for next 6 days:
  1) SPA position 2) Ineichen clear-sky 3) Hay-Davies transposition
  4) SAPM temperature 5) CEC module + Sandia inverter 6) Apply 14% system loss.
  Return dataframe columns: P_ac_W, E_Wh, E_day_Wh.
  ```
- [ ] **Weather adapter**
  ```
  Implement Open-Meteo client that returns cloud cover (%), temp (°C), wind (m/s) indexed to local tz.
  Provide function to map cloud cover to CMF scaling factor for GHI/DNI/DHI (α configurable).
  ```

---

## Acceptance criteria (go/no-go)

- [ ] HA sensors ingest without code changes (or with a documented, minimal config change).
- [ ] API responses mirror schema and timestamp format for both endpoints.
- [ ] Clear-sky mode deterministic & tested.
- [ ] Weather-aware mode operational and cached; graceful fallback on weather gaps.
- [ ] Dockerized deploy in <5 minutes; single command `docker compose up`.
- [ ] Basic load test: 50 RPS sustained, p95 < 200 ms (cached).

---

## Risk register & mitigations

- [ ] **Forecast quality variability** — Calibrate with inverter logs; allow α tuning per site.
- [ ] **Weather API downtime** — Cache + clear-sky fallback; circuit breaker.
- [ ] **Timezone/DST bugs** — Centralized time utilities; explicit tests for transitions.
- [ ] **API drift in HA expectations** — Freeze against captured samples; add contract tests.

---

## Quickstart (dev)

- [ ] `make dev` → run uvicorn with hot reload.
- [ ] `make test` → unit + contract tests.
- [ ] `docker compose up` → API on `:8080`.
- [ ] Test:
  ```bash
  curl "http://localhost:8080/clearsky/54.32/10.12/30/0/5" | jq .
  ```

---

## Backlog (nice-to-have)

- [ ] `/windows` endpoint parity (best solar windows).
- [ ] Quantiles/uncertainty bands.
- [ ] Per-plane outputs in response (debug mode).
- [ ] Helm chart + Ingress for k8s.
- [ ] Grafana dashboard JSON out-of-the-box.

---

**Definition of done:** HA wired to the local endpoint, stable daily operation for 7 days, parity with clear-sky reference, weather-aware forecasting within calibrated error bands, and operational playbooks documented.

---

## Future Work — Differentiating Features & Next‑Gen Capabilities

- [ ] **Local‑first, privacy‑centric design**
  - All forecasts computed locally; zero cloud dependency.
  - Edge‑ready for Raspberry Pi, NAS, or embedded controllers.
  - Offline fallback and caching for network‑isolated operation.

- [ ] **Hybrid Physics + Machine‑Learning Core**
  - Combine pvlib’s deterministic solar model with site‑specific ML residual correction.
  - Use inverter telemetry for continuous retraining.
  - Kalman‑style fusion of multiple data sources (Open‑Meteo, satellite irradiance, skycams).

- [ ] **Multi‑plane & Multi‑system Support**
  - Arbitrary plane definitions (E/W, trackers, façades, BIPV).
  - Consolidated forecasts and per‑plane diagnostics.

- [ ] **Sensor Fusion & Self‑Calibration**
  - Integrate local irradiance sensors, power meters, and cameras.
  - Dynamically adjust cloud modification factors (CMF) via sensor feedback.
  - Rolling calibration jobs to fit loss and clipping parameters.

- [ ] **Actionable Forecast Windows**
  - Provide endpoints like `/best_window?duration=2h` for optimal load shifting.
  - Integrate with smart‑home energy scheduling and autonomous control agents.

- [ ] **Explainable Forecast Diagnostics**
  - Embed model metadata and confidence metrics in every response.
  - Example:
    ```json
    "meta": {"cloud_source": "open-meteo", "cmf_alpha": 0.83, "temp_model": "SAPM", "confidence": 92}
    ```

- [ ] **AI‑driven Anomaly Detection**
  - Monitor residuals between forecast and measured data.
  - Flag inverter derating, soiling, or shading anomalies.

- [ ] **Open Integration Ecosystem**
  - REST, MQTT, GraphQL, and ROS 2/DDS interfaces.
  - Optional Modbus/TCP and Home Assistant native adapter.

- [ ] **Security & Deployment Excellence**
  - Signed containers, non‑root operation, and minimal image footprint.
  - Optional air‑gapped and read‑only modes.

- [ ] **Scalable Product Strategy**
  - Community edition (local‑only) and enterprise edition (fleet dashboards, ML calibration, API extensions).
  - Plugin SDK for third‑party data or AI modules.
  - Fleet‑level analytics dashboard for industrial clients.

---
