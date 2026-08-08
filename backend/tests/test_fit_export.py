"""FIT export round trip.

The file is written with fit-tool and read back with the official Garmin FIT
SDK decoder. Two independent implementations agreeing is the evidence that
matters; a library round-tripping its own output would only prove it is
self-consistent.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from garmin_fit_sdk import Decoder, Stream
from sqlmodel import select

from backend.app.fit_export import build_fit_workout
from backend.app.models import Exercise, Workout, WorkoutExercise


def _exercise(session, category: str, name: str) -> Exercise:
    return session.exec(
        select(Exercise).where(
            Exercise.garmin_category == category,
            Exercise.garmin_exercise_name == name,
        )
    ).one()


def _decode(payload: bytes):
    messages, errors = Decoder(Stream.from_byte_array(payload)).read()
    assert errors == []
    return messages


@pytest.fixture(name="sample")
def sample_fixture(seeded_session):
    squat = _exercise(seeded_session, "SQUAT", "BARBELL_HACK_SQUAT")
    bench = _exercise(seeded_session, "BENCH_PRESS", "BARBELL_BENCH_PRESS")
    workout = Workout(id=1, name="Lower and push")
    entries = [
        (
            WorkoutExercise(
                id=1, workout_id=1, exercise_id=squat.id, position=0,
                sets=3, reps=8, rest_seconds=120, load_kg=80.0,
            ),
            squat,
        ),
        (
            WorkoutExercise(
                id=2, workout_id=1, exercise_id=bench.id, position=1,
                sets=2, reps=10, rest_seconds=90,
            ),
            bench,
        ),
    ]
    return workout, entries


def test_file_decodes_with_the_official_sdk(sample):
    workout, entries = sample
    messages = _decode(build_fit_workout(workout, entries))

    assert "file_id_mesgs" in messages
    assert messages["file_id_mesgs"][0]["type"] == "workout"

    header = messages["workout_mesgs"][0]
    assert header["wkt_name"] == "Lower and push"
    assert header["sport"] == "training"
    assert header["sub_sport"] == "strength_training"


def test_step_count_matches_the_declared_count(sample):
    workout, entries = sample
    messages = _decode(build_fit_workout(workout, entries))
    declared = messages["workout_mesgs"][0]["num_valid_steps"]
    assert declared == len(messages["workout_step_mesgs"])


def test_every_set_round_trips_its_exercise_identity(sample):
    """The (category, name) pair is what makes the watch resolve the movement."""
    workout, entries = sample
    messages = _decode(build_fit_workout(workout, entries))
    active = [
        step
        for step in messages["workout_step_mesgs"]
        if step.get("intensity") == "active"
    ]

    # 3 sets of squats plus 2 sets of bench.
    assert len(active) == 5

    expected = []
    for workout_exercise, exercise in entries:
        for _ in range(workout_exercise.sets):
            expected.append(
                (
                    exercise.garmin_category.lower(),
                    exercise.garmin_exercise_name_value,
                    workout_exercise.reps,
                )
            )

    actual = [
        (step["exercise_category"], step["exercise_name"], step["duration_reps"])
        for step in active
    ]
    assert actual == expected


def test_rest_duration_is_in_seconds(sample):
    """FIT stores duration_time with a scale of 1000; a missed conversion here
    turns a 120 second rest into a 33 hour one."""
    workout, entries = sample
    messages = _decode(build_fit_workout(workout, entries))
    rests = [
        step for step in messages["workout_step_mesgs"] if step.get("intensity") == "rest"
    ]
    assert rests, "expected rest steps between sets"
    assert {step["duration_time"] for step in rests} == {120.0, 90.0}


def test_load_round_trips_in_kilograms(sample):
    workout, entries = sample
    messages = _decode(build_fit_workout(workout, entries))
    weighted = [
        step
        for step in messages["workout_step_mesgs"]
        if step.get("exercise_weight") is not None
    ]
    assert len(weighted) == 3
    assert {step["exercise_weight"] for step in weighted} == {80.0}


def test_workout_does_not_end_on_a_rest_step(sample):
    workout, entries = sample
    messages = _decode(build_fit_workout(workout, entries))
    assert messages["workout_step_mesgs"][-1]["intensity"] == "active"


def test_single_exercise_single_set(seeded_session):
    """The smallest possible workout must still produce a valid file."""
    exercise = _exercise(seeded_session, "CURL", "DUMBBELL_HAMMER_CURL")
    workout = Workout(id=2, name="Arms")
    entries = [
        (
            WorkoutExercise(
                id=1, workout_id=2, exercise_id=exercise.id, position=0,
                sets=1, reps=15, rest_seconds=60,
            ),
            exercise,
        )
    ]
    messages = _decode(
        build_fit_workout(workout, entries, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    )
    steps = messages["workout_step_mesgs"]
    assert len(steps) == 1
    assert steps[0]["duration_reps"] == 15
