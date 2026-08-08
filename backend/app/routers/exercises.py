"""Catalog browsing. The catalog is ~1850 rows, so every list response is
paginated and filterable rather than returned whole.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Text, func
from sqlmodel import Session, select

from ..db import get_session
from ..models import Exercise
from ..muscles import MUSCLE_VIEW, EquipmentType, MuscleGroup
from ..schemas import ExercisePage, ExerciseRead

router = APIRouter(prefix="/api/exercises", tags=["exercises"])


@router.get("", response_model=ExercisePage)
def list_exercises(
    session: Session = Depends(get_session),
    q: str | None = Query(default=None, description="substring of the display name"),
    category: str | None = Query(default=None, description="FIT exercise category"),
    equipment: str | None = Query(default=None, description="equipment type"),
    muscle: str | None = Query(default=None, description="muscle group, primary or secondary"),
    strength_only: bool = Query(default=True),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> ExercisePage:
    statement = select(Exercise)
    count_statement = select(func.count()).select_from(Exercise)

    filters = []
    if strength_only:
        filters.append(Exercise.is_strength == True)  # noqa: E712
    if q:
        filters.append(Exercise.display_name.ilike(f"%{q}%"))
    if category:
        filters.append(Exercise.garmin_category == category.upper())
    if equipment:
        filters.append(Exercise.equipment_type == equipment.lower())
    if muscle:
        # primary_muscles and secondary_muscles are JSON arrays of strings.
        # A LIKE on the serialised text is enough here and avoids depending on
        # the SQLite JSON1 extension being compiled in. The quotes around the
        # needle stop "abs" from matching "abductors".
        needle = f'%"{muscle.lower()}"%'
        filters.append(
            func.coalesce(Exercise.primary_muscles.cast(Text), "").like(needle)
            | func.coalesce(Exercise.secondary_muscles.cast(Text), "").like(needle)
        )

    for condition in filters:
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)

    total = session.exec(count_statement).one()
    statement = statement.order_by(Exercise.display_name).offset(offset).limit(limit)
    items = session.exec(statement).all()

    return ExercisePage(
        items=[ExerciseRead.model_validate(item) for item in items],
        total=int(total),
        offset=offset,
        limit=limit,
    )


@router.get("/facets")
def facets(session: Session = Depends(get_session)) -> dict[str, object]:
    """Values available for the catalog filters, plus the muscle taxonomy.

    The frontend uses this to build its filter controls and to know which
    anatomical view each muscle belongs to, so the taxonomy is never duplicated
    in TypeScript.
    """
    categories = session.exec(
        select(Exercise.garmin_category)
        .where(Exercise.is_strength == True)  # noqa: E712
        .distinct()
        .order_by(Exercise.garmin_category)
    ).all()
    equipment = session.exec(
        select(Exercise.equipment_type).distinct().order_by(Exercise.equipment_type)
    ).all()

    return {
        "categories": list(categories),
        "equipment": list(equipment),
        "equipment_types": [item.value for item in EquipmentType],
        "muscles": [
            {"id": muscle.value, "view": MUSCLE_VIEW[muscle]} for muscle in MuscleGroup
        ],
    }


@router.get("/{exercise_id}", response_model=ExerciseRead)
def get_exercise(exercise_id: int, session: Session = Depends(get_session)) -> Exercise:
    exercise = session.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail=f"exercise {exercise_id} not found")
    return exercise
