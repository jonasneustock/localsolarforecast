PYTHON := python
UVICORN := uvicorn

.PHONY: dev test build run fmt

dev:
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8080

test:
	pytest -q

build:
	docker compose build

run:
	docker compose up

fmt:
	$(PYTHON) -m pip install ruff black && ruff check --fix . && black .

