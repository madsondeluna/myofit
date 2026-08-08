"""Pydantic v2 request and response models for the HTTP layer.

Kept separate from the SQLModel tables so the wire format can carry derived
data (resolved exercise details, muscle aggregation, validation warnings)
without those becoming database columns.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Defaults from the project brief: 3 sets of 12, rest inside the 60-90s window.
DEFAULT_SETS = 3
DEFAULT_REPS = 12
DEFAULT_REST_SECONDS = 75


class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garmin_category: str
    garmin_exercise_name: str
    display_name: str
    primary_muscles: list[str]
    secondary_muscles: list[str]
    equipment_type: str
    is_compound: bool
    is_strength: bool


class ExercisePage(BaseModel):
    """Paginated catalog slice. The catalog has ~1850 rows, so the browse
    endpoint never returns it whole."""

    items: list[ExerciseRead]
    total: int
    offset: int
    limit: int


class WorkoutExerciseIn(BaseModel):
    exercise_id: int
    sets: int = Field(default=DEFAULT_SETS, ge=1, le=99)
    reps: int = Field(default=DEFAULT_REPS, ge=1, le=999)
    rest_seconds: int = Field(default=DEFAULT_REST_SECONDS, ge=0, le=3600)
    load_kg: float | None = Field(default=None, ge=0, le=1000)
    notes: str | None = Field(default=None, max_length=500)


class WorkoutExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    position: int
    sets: int
    reps: int
    rest_seconds: int
    load_kg: float | None
    notes: str | None
    exercise: ExerciseRead


class WorkoutIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)
    # Order of this list is the order of the workout; position is derived from
    # the index so the client never has to keep the two in sync.
    exercises: list[WorkoutExerciseIn] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank")
        return stripped


class MuscleLoad(BaseModel):
    """Aggregated work on one muscle group across a whole workout."""

    muscle: str
    # Weighted score: a primary hit counts 1.0, a secondary hit 0.5, each
    # scaled by the number of sets. Drives the heat map intensity.
    score: float
    primary_count: int
    secondary_count: int
    # score normalised to 0..1 against the hardest-worked muscle of the workout.
    intensity: float


class ValidationWarning(BaseModel):
    code: str
    message: str
    exercise_position: int | None = None


class WorkoutRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    garmin_workout_id: str | None
    garmin_synced_at: datetime | None
    exercises: list[WorkoutExerciseRead]
    muscle_load: list[MuscleLoad] = Field(default_factory=list)
    warnings: list[ValidationWarning] = Field(default_factory=list)


class WorkoutSummary(BaseModel):
    """Row shape for the workout list; omits the exercise detail."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    garmin_workout_id: str | None
    exercise_count: int


class ReorderIn(BaseModel):
    """New order, given as workout_exercise ids from first to last."""

    workout_exercise_ids: list[int]


class GarminLoginIn(BaseModel):
    email: str
    password: str
    # Garmin prompts for an MFA code on accounts that have it enabled.
    mfa_code: str | None = None


class GarminStatus(BaseModel):
    authenticated: bool
    profile_name: str | None = None
    detail: str | None = None


class SyncResult(BaseModel):
    ok: bool
    garmin_workout_id: str | None = None
    detail: str | None = None
