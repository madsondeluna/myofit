.PHONY: install dev api web build test clean

VENV := .venv
PY := $(VENV)/bin/python

install:
	uv venv --python 3.12
	uv pip install --python $(PY) -r pyproject.toml
	uv pip install --python $(PY) pytest httpx
	cd frontend && npm install

# Runs the API and the Vite dev server together. Vite proxies /api to 8000, so
# the app is reached at http://localhost:5173 with a single origin.
dev:
	@echo "API on http://127.0.0.1:8000, app on http://localhost:5173"
	@$(PY) -m uvicorn backend.app.main:app --reload --port 8000 & \
	 cd frontend && npm run dev; \
	 kill %1 2>/dev/null || true

api:
	$(PY) -m uvicorn backend.app.main:app --reload --port 8000

web:
	cd frontend && npm run dev

# Production shape: build the frontend, then serve it from the API process.
build:
	cd frontend && npm run build

test:
	$(PY) -m pytest backend/tests -q

clean:
	rm -rf frontend/dist myofit.db .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
