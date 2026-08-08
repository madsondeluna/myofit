"""Database helpers shared by the routers.

Kept apart from the route handlers so that resolving a workout into the shape
the API returns (exercises joined, muscles aggregated, warnings computed)
happens in exactly one place.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlmodel import Session, select

from .analysis import aggregate_muscle_load, validate_ordering
from .models import Exercise, Workout, WorkoutExercise
from .schemas import WorkoutIn, WorkoutRead


def get_workout_or_404(session: Session, workout_id: int) -> Workout:
    workout = session.get(Workout, workout_id)
    if workout is None:
        raise HTTPException(status_code=404, detail=f"workout {workout_id} not found")
    return workout


def load_entries(session: Session, workout: Workout) -> list[tuple[WorkoutExercise, Exercise]]:
    """Pair each workout entry with its catalog row, ordered by position.

    Fetches the exercises in one query rather than per row, because a workout
    of 10 movements would otherwise cost 10 round trips on every read.
    """
    entries = sorted(workout.exercises, key=lambda item: item.position)
    if not entries:
        return []

    exercise_ids = {entry.exercise_id for entry in entries}
    rows = session.exec(select(Exercise).where(Exercise.id.in_(exercise_ids))).all()
    by_id = {row.id: row for row in rows}

    paired: list[tuple[WorkoutExercise, Exercise]] = []
    for entry in entries:
        exercise = by_id.get(entry.exercise_id)
        # A missing catalog row would mean the database was reseeded with a
        # different id space. Skip rather than fail the whole read.
        if exercise is not None:
            paired.append((entry, exercise))
    return paired


def render_workout(session: Session, workout: Workout) -> WorkoutRead:
    entries = load_entries(session, workout)

    exercises_payload = []
    for entry, exercise in entries:
        exercises_payload.append(
            {
                "id": entry.id,
                "exercise_id": entry.exercise_id,
                "position": entry.position,
                "sets": entry.sets,
                "reps": entry.reps,
                "rest_seconds": entry.rest_seconds,
                "load_kg": entry.load_kg,
                "notes": entry.notes,
                "exercise": exercise,
            }
        )

    return WorkoutRead.model_validate(
        {
            "id": workout.id,
            "name": workout.name,
            "notes": workout.notes,
            "created_at": workout.created_at,
            "updated_at": workout.updated_at,
            "garmin_workout_id": workout.garmin_workout_id,
            "garmin_synced_at": workout.garmin_synced_at,
            "exercises": exercises_payload,
            "muscle_load": aggregate_muscle_load(entries),
            "warnings": validate_ordering(entries),
        }
    )


def assert_exercises_exist(session: Session, exercise_ids: list[int]) -> None:
    if not exercise_ids:
        return
    found = session.exec(
        select(Exercise.id).where(Exercise.id.in_(set(exercise_ids)))
    ).all()
    missing = set(exercise_ids) - set(found)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"unknown exercise ids: {sorted(missing)}",
        )


def apply_exercises(session: Session, workout: Workout, payload: WorkoutIn) -> None:
    """Replace the workout's exercise list with the one in the payload.

    Position is taken from the list index, so the client expresses order purely
    by the order it sends. Replacing wholesale keeps positions dense and avoids
    a separate reconciliation path for adds, removes and moves.
    """
    assert_exercises_exist(session, [item.exercise_id for item in payload.exercises])

    for existing in list(workout.exercises):
        session.delete(existing)
    # Flush the deletes before the inserts so the two do not interleave and
    # collide on the workout_exercise unique constraints.
    session.flush()
    workout.exercises.clear()

    for index, item in enumerate(payload.exercises):
        workout.exercises.append(
            WorkoutExercise(
                exercise_id=item.exercise_id,
                position=index,
                sets=item.sets,
                reps=item.reps,
                rest_seconds=item.rest_seconds,
                load_kg=item.load_kg,
                notes=item.notes,
            )
        )

    workout.updated_at = datetime.now(timezone.utc)
