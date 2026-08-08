"""Catalog seeding: identity comes from the FIT SDK, muscles from the taxonomy."""

from __future__ import annotations

import fit_tool.profile.profile_type as fit_profile
import pytest
from sqlmodel import select

from backend.app.models import Exercise
from backend.app.muscles import EquipmentType, MuscleGroup
from backend.app.seed import SKIP_CATEGORIES, build_catalog, name_enum_for, seed_exercises


def test_every_category_maps_to_a_name_enum():
    """The FIT profile's naming convention must hold for all 51 real categories.

    If a future SDK release breaks it, seeding would silently drop a whole
    category rather than fail, so it is asserted directly.
    """
    unmapped = [
        category.name
        for category in fit_profile.ExerciseCategory
        if category.name not in SKIP_CATEGORIES and name_enum_for(category.name) is None
    ]
    assert unmapped == []


def test_catalog_identity_matches_the_sdk(seeded_session):
    """Every seeded row must resolve back to a real (category, name) enum pair."""
    rows = seeded_session.exec(select(Exercise)).all()
    assert len(rows) > 1500

    for row in rows:
        category = fit_profile.ExerciseCategory[row.garmin_category]
        assert int(category.value) == row.garmin_category_value

        name_enum = name_enum_for(row.garmin_category)
        member = name_enum[row.garmin_exercise_name]
        assert int(member.value) == row.garmin_exercise_name_value


def test_no_unknown_sentinels_in_catalog(seeded_session):
    """Each FIT name enum carries an UNKNOWN member that is not an exercise."""
    rows = seeded_session.exec(
        select(Exercise).where(Exercise.garmin_exercise_name == "UNKNOWN")
    ).all()
    assert rows == []


def test_muscles_are_valid_taxonomy_members(seeded_session):
    valid = {muscle.value for muscle in MuscleGroup}
    rows = seeded_session.exec(select(Exercise)).all()

    for row in rows:
        assert set(row.primary_muscles) <= valid, row.garmin_exercise_name
        assert set(row.secondary_muscles) <= valid, row.garmin_exercise_name
        # A muscle painted as both primary and secondary would get two
        # intensities on the body map.
        assert not set(row.primary_muscles) & set(row.secondary_muscles)


def test_equipment_is_a_valid_enum_member(seeded_session):
    valid = {item.value for item in EquipmentType}
    rows = seeded_session.exec(select(Exercise)).all()
    assert {row.equipment_type for row in rows} <= valid


def test_strength_exercises_have_primary_muscles(seeded_session):
    rows = seeded_session.exec(
        select(Exercise).where(Exercise.is_strength == True)  # noqa: E712
    ).all()
    without = [row.garmin_exercise_name for row in rows if not row.primary_muscles]
    assert without == []


@pytest.mark.parametrize(
    ("category", "name", "expected_primary"),
    [
        ("SQUAT", "LEG_PRESS", "quadriceps"),
        ("SQUAT", "BARBELL_HACK_SQUAT", "quadriceps"),
        ("CALF_RAISE", "SEATED_CALF_RAISE", "calves"),
        ("HIP_STABILITY", "STANDING_HIP_ABDUCTION", "abductors"),
        ("BENCH_PRESS", "BARBELL_BENCH_PRESS", "chest"),
        ("CURL", "DUMBBELL_HAMMER_CURL", "biceps"),
        # Scoped override check: DECLINE must not fire outside the press family.
        ("CURL", "DECLINE_HAMMER_CURL", "biceps"),
        ("BENCH_PRESS", "DECLINE_DUMBBELL_BENCH_PRESS", "chest"),
    ],
)
def test_known_exercises_resolve(seeded_session, category, name, expected_primary):
    row = seeded_session.exec(
        select(Exercise).where(
            Exercise.garmin_category == category,
            Exercise.garmin_exercise_name == name,
        )
    ).one()
    assert expected_primary in row.primary_muscles


def test_seeding_is_idempotent(session):
    first = seed_exercises(session)
    second = seed_exercises(session)
    assert first == second


def test_catalog_pairs_are_unique():
    rows = build_catalog()
    pairs = [(row.garmin_category, row.garmin_exercise_name) for row in rows]
    assert len(pairs) == len(set(pairs))
