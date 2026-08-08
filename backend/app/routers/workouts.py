"""Workout CRUD, reordering, FIT export and Garmin push."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func
from sqlmodel import Session, select

from .. import garmin as garmin_client
from ..crud import (
    apply_exercises,
    get_workout_or_404,
    load_entries,
    render_workout,
)
from ..db import get_session
from ..fit_export import build_fit_workout
from ..models import Workout, WorkoutExercise
from ..schemas import ReorderIn, SyncResult, WorkoutIn, WorkoutRead, WorkoutSummary

router = APIRouter(prefix="/api/workouts", tags=["workouts"])


def _safe_filename(name: str) -> str:
    """ASCII, no path separators. The value goes into a Content-Disposition
    header, where a stray quote or slash would break the download."""
    cleaned = "".join(char if char.isalnum() or char in "-_ " else "_" for char in name)
    return (cleaned.strip().replace(" ", "_") or "workout")[:60]


@router.get("", response_model=list[WorkoutSummary])
def list_workouts(session: Session = Depends(get_session)) -> list[WorkoutSummary]:
    workouts = session.exec(select(Workout).order_by(Workout.updated_at.desc())).all()
    counts = dict(
        session.exec(
            select(WorkoutExercise.workout_id, func.count(WorkoutExercise.id)).group_by(
                WorkoutExercise.workout_id
            )
        ).all()
    )
    return [
        WorkoutSummary(
            id=workout.id,
            name=workout.name,
            created_at=workout.created_at,
            updated_at=workout.updated_at,
            garmin_workout_id=workout.garmin_workout_id,
            exercise_count=counts.get(workout.id, 0),
        )
        for workout in workouts
    ]


@router.post("", response_model=WorkoutRead, status_code=201)
def create_workout(payload: WorkoutIn, session: Session = Depends(get_session)) -> WorkoutRead:
    workout = Workout(name=payload.name, notes=payload.notes)
    session.add(workout)
    session.flush()
    apply_exercises(session, workout, payload)
    session.commit()
    session.refresh(workout)
    return render_workout(session, workout)


@router.get("/{workout_id}", response_model=WorkoutRead)
def get_workout(workout_id: int, session: Session = Depends(get_session)) -> WorkoutRead:
    return render_workout(session, get_workout_or_404(session, workout_id))


@router.put("/{workout_id}", response_model=WorkoutRead)
def update_workout(
    workout_id: int, payload: WorkoutIn, session: Session = Depends(get_session)
) -> WorkoutRead:
    workout = get_workout_or_404(session, workout_id)
    workout.name = payload.name
    workout.notes = payload.notes
    apply_exercises(session, workout, payload)
    session.commit()
    session.refresh(workout)
    return render_workout(session, workout)


@router.delete("/{workout_id}", status_code=204)
def delete_workout(workout_id: int, session: Session = Depends(get_session)) -> Response:
    workout = get_workout_or_404(session, workout_id)
    session.delete(workout)
    session.commit()
    return Response(status_code=204)


@router.post("/{workout_id}/reorder", response_model=WorkoutRead)
def reorder_workout(
    workout_id: int, payload: ReorderIn, session: Session = Depends(get_session)
) -> WorkoutRead:
    """Apply a new order given as the full list of workout_exercise ids.

    The list must be a permutation of what the workout already holds. Accepting
    a partial list would leave the remaining entries with ambiguous positions.
    """
    workout = get_workout_or_404(session, workout_id)
    current = {entry.id: entry for entry in workout.exercises}

    if sorted(payload.workout_exercise_ids) != sorted(current.keys()):
        raise HTTPException(
            status_code=422,
            detail="workout_exercise_ids must be a permutation of the workout entries",
        )

    for index, entry_id in enumerate(payload.workout_exercise_ids):
        current[entry_id].position = index

    workout.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(workout)
    return render_workout(session, workout)


@router.get("/{workout_id}/export.fit")
def export_fit(workout_id: int, session: Session = Depends(get_session)) -> Response:
    workout = get_workout_or_404(session, workout_id)
    entries = load_entries(session, workout)
    if not entries:
        raise HTTPException(status_code=422, detail="cannot export an empty workout")

    payload = build_fit_workout(workout, entries)
    filename = f"{_safe_filename(workout.name)}.fit"
    return Response(
        content=payload,
        media_type="application/vnd.ant.fit",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{workout_id}/sync", response_model=SyncResult)
def sync_to_garmin(workout_id: int, session: Session = Depends(get_session)) -> SyncResult:
    workout = get_workout_or_404(session, workout_id)
    entries = load_entries(session, workout)
    if not entries:
        raise HTTPException(status_code=422, detail="cannot sync an empty workout")

    result = garmin_client.push_workout(workout, entries)
    if result.ok and result.garmin_workout_id:
        workout.garmin_workout_id = result.garmin_workout_id
        workout.garmin_synced_at = datetime.now(timezone.utc)
        session.commit()
    return result
