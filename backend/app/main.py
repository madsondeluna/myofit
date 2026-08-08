"""FastAPI application entrypoint.

In production the built frontend is served from this same process, so Render
runs one web service instead of two.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from .db import engine, init_db
from .routers import exercises, garmin, workouts
from .seed import seed_exercises

DISCLAIMER = (
    "MyoFit is an educational tool. Training programmes and loads should be "
    "reviewed by a qualified professional before use."
)

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Create tables and seed the catalog on boot. Seeding is idempotent: it
    # returns early when the exercise table already has rows, so a Render
    # restart on a persistent disk does not duplicate the catalog.
    init_db()
    with Session(engine) as session:
        seed_exercises(session)
    yield


app = FastAPI(
    title="MyoFit",
    description="Strength workout builder with an interactive body map and Garmin Connect sync.",
    version="0.1.0",
    lifespan=lifespan,
)

# The Vite dev server runs on a different origin during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "MYOFIT_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exercises.router)
app.include_router(workouts.router)
app.include_router(garmin.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"status": "ok", "disclaimer": DISCLAIMER}


# --- Static frontend ------------------------------------------------------
# Mounted only when a build exists, so `uvicorn` still starts in a checkout
# where the frontend has never been built.
if FRONTEND_DIST.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str) -> FileResponse:
        # Any non-API path falls through to index.html so client-side routing
        # survives a page reload.
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
