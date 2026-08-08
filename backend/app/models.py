"""SQLModel tables. Muscle lists are stored as JSON columns because SQLite has
no array type and the lists are always read whole, never queried element-wise.

Note: this module deliberately does NOT use `from __future__ import annotations`.
SQLModel resolves Relationship targets by inspecting the annotation at class
creation, and postponed evaluation turns `list[WorkoutExercise]` into a string
that SQLAlchemy then rejects as "a generic class as the argument".
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Exercise(SQLModel, table=True):
    """One entry of the catalog, identified by the FIT (category, name) pair.

    garmin_category and garmin_exercise_name hold the SDK enum *member names*
    (for example SQUAT / HACK_SQUAT). The matching integer values are kept
    alongside because the FIT binary encoding needs the ints while the Garmin
    Connect workout-service JSON uses the lowercase strings.
    """

    __tablename__ = "exercise"
    __table_args__ = (UniqueConstraint("garmin_category", "garmin_exercise_name"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    garmin_category: str = Field(index=True)
    garmin_category_value: int
    garmin_exercise_name: str = Field(index=True)
    garmin_exercise_name_value: int
    display_name: str = Field(index=True)
    primary_muscles: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    secondary_muscles: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    equipment_type: str = Field(index=True)
    is_compound: bool = Field(default=False, index=True)
    is_strength: bool = Field(default=True, index=True)


class Workout(SQLModel, table=True):
    __tablename__ = "workout"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    # Set after a successful push so the UI can show sync state.
    garmin_workout_id: Optional[str] = Field(default=None)
    garmin_synced_at: Optional[datetime] = Field(default=None)

    exercises: list["WorkoutExercise"] = Relationship(
        back_populates="workout",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "WorkoutExercise.position",
        },
    )


class WorkoutExercise(SQLModel, table=True):
    """An exercise placed in a workout, with its prescription."""

    __tablename__ = "workout_exercise"

    id: Optional[int] = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workout.id", index=True, ondelete="CASCADE")
    exercise_id: int = Field(foreign_key="exercise.id")
    # Zero-based position; the API keeps it dense and gap-free on every write.
    position: int = Field(default=0)
    sets: int = Field(default=3)
    reps: int = Field(default=12)
    rest_seconds: int = Field(default=75)
    load_kg: Optional[float] = Field(default=None)
    notes: Optional[str] = Field(default=None)

    workout: Optional[Workout] = Relationship(back_populates="exercises")
