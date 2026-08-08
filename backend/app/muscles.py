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


# Which anatomical views show each group. A muscle can appear in both: the
# trapezius wraps the neck and is visible from the front, the calf shows its
# gastrocnemius from behind and the shin from the front, and the deltoid and
# forearm are simply on both sides of the body.
#
# The frontend uses this to know whether a highlighted muscle is visible on the
# currently displayed side, and the test suite uses it to assert that every
# muscle listed here has a matching SVG path id in every view named. A muscle
# with no path is the failure that produces a map which never highlights.
MUSCLE_VIEWS: dict[MuscleGroup, tuple[str, ...]] = {
    MuscleGroup.QUADRICEPS: ("front",),
    MuscleGroup.HAMSTRINGS: ("back",),
    MuscleGroup.GLUTES: ("back",),
    MuscleGroup.ADDUCTORS: ("front",),
    MuscleGroup.ABDUCTORS: ("front",),
    MuscleGroup.CALVES: ("front", "back"),
    MuscleGroup.ERECTOR_SPINAE: ("back",),
    MuscleGroup.LATS: ("back",),
    MuscleGroup.TRAPS: ("front", "back"),
    MuscleGroup.RHOMBOIDS: ("back",),
    MuscleGroup.REAR_DELTS: ("back",),
    MuscleGroup.FRONT_DELTS: ("front",),
    MuscleGroup.SIDE_DELTS: ("front", "back"),
    MuscleGroup.CHEST: ("front",),
    MuscleGroup.BICEPS: ("front",),
    MuscleGroup.TRICEPS: ("back",),
    MuscleGroup.FOREARMS: ("front", "back"),
    MuscleGroup.ABS: ("front",),
    MuscleGroup.OBLIQUES: ("front",),
}

VIEWS: tuple[str, ...] = ("front", "back")


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
