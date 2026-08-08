"""Fixed muscle taxonomy shared by the catalog, the API and the SVG body map.

The member values are the contract with the frontend: every value here must
exist as an SVG path id in the front or back body map view, and every muscle
string stored in the database must be a member of this enum. Both directions
are asserted in the test suite, because a silent mismatch produces a body map
that simply never highlights.
"""

from __future__ import annotations

from enum import StrEnum


class MuscleGroup(StrEnum):
    """The 19 muscle groups the body map can render."""

    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    ADDUCTORS = "adductors"
    ABDUCTORS = "abductors"
    CALVES = "calves"
    ERECTOR_SPINAE = "erector_spinae"
    LATS = "lats"
    TRAPS = "traps"
    RHOMBOIDS = "rhomboids"
    REAR_DELTS = "rear_delts"
    FRONT_DELTS = "front_delts"
    SIDE_DELTS = "side_delts"
    CHEST = "chest"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS = "forearms"
    ABS = "abs"
    OBLIQUES = "obliques"


# Which anatomical view shows each group. Used by the frontend to decide whether
# a highlighted muscle is visible on the currently displayed side, and by the
# test that checks SVG path coverage.
MUSCLE_VIEW: dict[MuscleGroup, str] = {
    MuscleGroup.QUADRICEPS: "front",
    MuscleGroup.HAMSTRINGS: "back",
    MuscleGroup.GLUTES: "back",
    MuscleGroup.ADDUCTORS: "front",
    MuscleGroup.ABDUCTORS: "front",
    MuscleGroup.CALVES: "back",
    MuscleGroup.ERECTOR_SPINAE: "back",
    MuscleGroup.LATS: "back",
    MuscleGroup.TRAPS: "back",
    MuscleGroup.RHOMBOIDS: "back",
    MuscleGroup.REAR_DELTS: "back",
    MuscleGroup.FRONT_DELTS: "front",
    MuscleGroup.SIDE_DELTS: "front",
    MuscleGroup.CHEST: "front",
    MuscleGroup.BICEPS: "front",
    MuscleGroup.TRICEPS: "back",
    MuscleGroup.FOREARMS: "front",
    MuscleGroup.ABS: "front",
    MuscleGroup.OBLIQUES: "front",
}


class EquipmentType(StrEnum):
    """Equipment inferred from the FIT exercise name."""

    BARBELL = "barbell"
    DUMBBELL = "dumbbell"
    KETTLEBELL = "kettlebell"
    CABLE = "cable"
    MACHINE = "machine"
    SMITH_MACHINE = "smith_machine"
    BAND = "band"
    MEDICINE_BALL = "medicine_ball"
    STABILITY_BALL = "stability_ball"
    SUSPENSION = "suspension"
    PLATE = "plate"
    BODYWEIGHT = "bodyweight"
    OTHER = "other"
