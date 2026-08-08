"""Catalog seeding, derived from the Garmin FIT SDK exercise enums.

The FIT profile models strength exercises as a two-level enum: one
ExerciseCategory (53 members) plus a *separate* name enum per category, so the
identity of an exercise is the pair (category value, name value). Name values
are only unique within their category: value 0 is LEG_PRESS under SQUAT and
BENCH_PRESS under BENCH_PRESS.

Nothing here types an exercise string by hand. The enum members are walked, and
the local knowledge in catalog_data.py only decorates them with muscles,
equipment and the compound flag.
"""

from __future__ import annotations

import fit_tool.profile.profile_type as fit_profile
from sqlmodel import Session, select

from .catalog_data import (
    CATEGORY_EQUIPMENT_DEFAULT,
    CATEGORY_PROFILE,
    EQUIPMENT_KEYWORDS,
    MACHINE_NAME_TOKENS,
    NAME_OVERRIDES,
    NON_STRENGTH_CATEGORIES,
)
from .models import Exercise
from .muscles import EquipmentType, MuscleGroup

# Categories carrying no exercise-name enum of their own.
SKIP_CATEGORIES: frozenset[str] = frozenset({"UNKNOWN", "CARDIO_SENSORS"})

# Tokens that read as noise in a display name once the rest is title-cased.
_DISPLAY_FIXUPS: dict[str, str] = {
    "Ez": "EZ",
    "Trx": "TRX",
    "Bosu": "BOSU",
    "V": "V",
    "T": "T",
    "Iso": "ISO",
    "Rdl": "RDL",
}


def name_enum_for(category_name: str):
    """Return the ExerciseName enum class matching a category member name.

    The FIT profile follows a strict convention: HIP_STABILITY maps to
    HipStabilityExerciseName. 51 of the 53 categories resolve this way; the two
    that do not are in SKIP_CATEGORIES.
    """
    class_name = "".join(part.capitalize() for part in category_name.split("_")) + "ExerciseName"
    return getattr(fit_profile, class_name, None)


def humanize(enum_member_name: str) -> str:
    """SEATED_CALF_RAISE -> Seated Calf Raise."""
    words = [_DISPLAY_FIXUPS.get(w.capitalize(), w.capitalize()) for w in enum_member_name.split("_")]
    return " ".join(words)


def infer_equipment(exercise_name: str, category_name: str) -> EquipmentType:
    # Explicit equipment token in the name wins over everything else.
    for token, equipment in EQUIPMENT_KEYWORDS:
        if token in exercise_name:
            return equipment
    # Then names that are machine work without saying so.
    for token in MACHINE_NAME_TOKENS:
        if token in exercise_name:
            return EquipmentType.MACHINE
    return CATEGORY_EQUIPMENT_DEFAULT.get(category_name, EquipmentType.BODYWEIGHT)


def resolve_muscles(
    category_name: str, exercise_name: str
) -> tuple[list[MuscleGroup], list[MuscleGroup], bool]:
    """Muscle profile for one exercise: category baseline, then keyword override.

    Returns (primary, secondary, is_compound). Non-strength categories return
    empty lists so they never contribute to the body map heat aggregation.
    """
    if category_name in NON_STRENGTH_CATEGORIES:
        return [], [], False

    primary, secondary, is_compound = CATEGORY_PROFILE.get(
        category_name, ([], [], False)
    )

    # First matching keyword wins; NAME_OVERRIDES is ordered most-specific
    # first. The category scope stops a token from firing outside the movement
    # family it was written for.
    for token, categories, override_primary, override_secondary, override_compound in NAME_OVERRIDES:
        if token in exercise_name and (categories is None or category_name in categories):
            primary = override_primary
            secondary = override_secondary
            if override_compound is not None:
                is_compound = override_compound
            break

    # A muscle can never be both primary and secondary for the same exercise;
    # the body map would then paint it with two intensities.
    secondary = [m for m in secondary if m not in primary]
    return list(primary), list(secondary), is_compound


def build_catalog() -> list[Exercise]:
    """Walk every category/name pair in the FIT profile into Exercise rows."""
    rows: list[Exercise] = []

    for category in fit_profile.ExerciseCategory:
        if category.name in SKIP_CATEGORIES:
            continue
        name_enum = name_enum_for(category.name)
        if name_enum is None:
            continue

        is_strength = category.name not in NON_STRENGTH_CATEGORIES

        for exercise in name_enum:
            # Every name enum carries an UNKNOWN sentinel that is not a real
            # exercise and must not reach the catalog.
            if exercise.name == "UNKNOWN":
                continue

            primary, secondary, is_compound = resolve_muscles(category.name, exercise.name)
            rows.append(
                Exercise(
                    garmin_category=category.name,
                    garmin_category_value=int(category.value),
                    garmin_exercise_name=exercise.name,
                    garmin_exercise_name_value=int(exercise.value),
                    display_name=humanize(exercise.name),
                    primary_muscles=[m.value for m in primary],
                    secondary_muscles=[m.value for m in secondary],
                    equipment_type=infer_equipment(exercise.name, category.name).value,
                    is_compound=is_compound,
                    is_strength=is_strength,
                )
            )

    return rows


def seed_exercises(session: Session, *, force: bool = False) -> int:
    """Insert the catalog if empty. Returns the number of rows now present."""
    existing = session.exec(select(Exercise)).first()
    if existing is not None and not force:
        return len(session.exec(select(Exercise)).all())

    if force:
        for row in session.exec(select(Exercise)).all():
            session.delete(row)
        session.commit()

    rows = build_catalog()
    session.add_all(rows)
    session.commit()
    return len(rows)
