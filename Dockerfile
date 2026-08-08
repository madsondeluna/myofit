# Two stages: Node builds the frontend, Python serves it alongside the API.
# A single image means Render runs one web service instead of two, and the
# frontend is same-origin with the API so no CORS is involved in production.

FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

# uv resolves and installs faster than pip and honours the lockfile.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

COPY backend/ ./backend/
COPY --from=frontend /build/dist ./frontend/dist

# Render injects PORT. The default keeps `docker run` usable without it.
ENV PORT=8000
ENV MYOFIT_DB=sqlite:////data/myofit.db
ENV GARMINTOKENS=/data/garth

# Created so the image runs without a mounted disk; Render's disk mounts over it.
RUN mkdir -p /data

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
