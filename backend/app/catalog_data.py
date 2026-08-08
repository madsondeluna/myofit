"""Muscle, equipment and movement-pattern knowledge layered on the FIT enums.

The exercise identity (category + name) is derived from the Garmin FIT SDK, never
typed by hand, so that a synced workout resolves on the watch. What the SDK does
not carry is which muscles an exercise trains. That knowledge lives here, as a
per-category baseline plus keyword overrides for names whose target differs from
their category default.
"""

from __future__ import annotations

from .muscles import EquipmentType, MuscleGroup as M

# Categories the FIT profile defines but that are not strength work. They are
# still seeded so a user can reference them, but they carry no muscle data and
# are excluded from the body map aggregation.
NON_STRENGTH_CATEGORIES: frozenset[str] = frozenset(
    {
        "CARDIO",
        "RUN",
        "RUN_INDOOR",
        "BIKE",
        "BIKE_OUTDOOR",
        "INDOOR_BIKE",
        "ELLIPTICAL",
        "INDOOR_ROW",
        "STAIR_STEPPER",
        "FLOOR_CLIMB",
        "LADDER",
        "WARM_UP",
        "POSE",
        "MOVE",
    }
)

# Baseline muscle profile per FIT exercise category.
# Shape: category -> (primary, secondary, is_compound)
CATEGORY_PROFILE: dict[str, tuple[list[M], list[M], bool]] = {
    "BENCH_PRESS": ([M.CHEST], [M.TRICEPS, M.FRONT_DELTS], True),
    "CALF_RAISE": ([M.CALVES], [], False),
    "CARRY": ([M.FOREARMS, M.TRAPS], [M.ABS, M.OBLIQUES, M.ERECTOR_SPINAE], True),
    "CHOP": ([M.OBLIQUES], [M.ABS, M.FRONT_DELTS], True),
    "CORE": ([M.ABS], [M.OBLIQUES, M.ERECTOR_SPINAE], False),
    "CRUNCH": ([M.ABS], [M.OBLIQUES], False),
    "CURL": ([M.BICEPS], [M.FOREARMS], False),
    "DEADLIFT": ([M.HAMSTRINGS, M.GLUTES, M.ERECTOR_SPINAE], [M.TRAPS, M.FOREARMS, M.LATS], True),
    "FLYE": ([M.CHEST], [M.FRONT_DELTS], False),
    "HIP_RAISE": ([M.GLUTES], [M.HAMSTRINGS, M.ERECTOR_SPINAE], False),
    "HIP_STABILITY": ([M.ABDUCTORS, M.GLUTES], [M.ADDUCTORS], False),
    "HIP_SWING": ([M.GLUTES, M.HAMSTRINGS], [M.ERECTOR_SPINAE, M.ABS], True),
    "HYPEREXTENSION": ([M.ERECTOR_SPINAE], [M.GLUTES, M.HAMSTRINGS], False),
    "LATERAL_RAISE": ([M.SIDE_DELTS], [M.TRAPS, M.FRONT_DELTS], False),
    "LEG_CURL": ([M.HAMSTRINGS], [M.CALVES], False),
    "LEG_RAISE": ([M.ABS], [M.QUADRICEPS, M.OBLIQUES], False),
    "LUNGE": ([M.QUADRICEPS, M.GLUTES], [M.HAMSTRINGS, M.ADDUCTORS, M.CALVES], True),
    "OLYMPIC_LIFT": (
        [M.QUADRICEPS, M.GLUTES, M.TRAPS],
        [M.HAMSTRINGS, M.ERECTOR_SPINAE, M.SIDE_DELTS, M.CALVES],
        True,
    ),
    "PLANK": ([M.ABS], [M.OBLIQUES, M.FRONT_DELTS, M.ERECTOR_SPINAE], False),
    "PLYO": ([M.QUADRICEPS, M.GLUTES], [M.CALVES, M.HAMSTRINGS], True),
    "PULL_UP": ([M.LATS], [M.BICEPS, M.RHOMBOIDS, M.FOREARMS], True),
    "PUSH_UP": ([M.CHEST], [M.TRICEPS, M.FRONT_DELTS, M.ABS], True),
    "ROW": ([M.LATS, M.RHOMBOIDS], [M.BICEPS, M.REAR_DELTS, M.ERECTOR_SPINAE], True),
    "SHOULDER_PRESS": ([M.FRONT_DELTS], [M.SIDE_DELTS, M.TRICEPS, M.TRAPS], True),
    "SHOULDER_STABILITY": ([M.REAR_DELTS], [M.SIDE_DELTS, M.RHOMBOIDS], False),
    "SHRUG": ([M.TRAPS], [M.FOREARMS, M.RHOMBOIDS], False),
    "SIT_UP": ([M.ABS], [M.OBLIQUES], False),
    "SQUAT": ([M.QUADRICEPS, M.GLUTES], [M.HAMSTRINGS, M.ADDUCTORS, M.ERECTOR_SPINAE], True),
    "TOTAL_BODY": (
        [M.QUADRICEPS, M.GLUTES, M.CHEST],
        [M.ABS, M.FRONT_DELTS, M.HAMSTRINGS, M.TRICEPS],
        True,
    ),
    "TRICEPS_EXTENSION": ([M.TRICEPS], [], False),
    "BANDED_EXERCISES": ([M.ABDUCTORS, M.GLUTES], [M.ADDUCTORS], False),
    "BATTLE_ROPE": ([M.FRONT_DELTS, M.FOREARMS], [M.ABS, M.SIDE_DELTS], True),
    "SANDBAG": ([M.QUADRICEPS, M.GLUTES], [M.ERECTOR_SPINAE, M.ABS, M.TRAPS], True),
    "SLED": ([M.QUADRICEPS, M.GLUTES], [M.CALVES, M.HAMSTRINGS], True),
    "SLEDGE_HAMMER": ([M.OBLIQUES, M.LATS], [M.ABS, M.FOREARMS], True),
    "SUSPENSION": ([M.LATS, M.ABS], [M.BICEPS, M.CHEST, M.RHOMBOIDS], True),
    "TIRE": ([M.QUADRICEPS, M.GLUTES, M.ERECTOR_SPINAE], [M.TRAPS, M.HAMSTRINGS], True),
}

# Keyword overrides, checked against the FIT exercise name in order. The first
# match wins, so more specific tokens must come first. These exist for names
# whose target diverges from the category baseline: LEG_PRESS lives under the
# SQUAT category but is not a spinal-loaded squat, CLOSE_GRIP bench shifts the
# emphasis to triceps, and so on.
#
# Each entry is scoped to the categories it may fire in. Scoping is not
# cosmetic: DECLINE_HAMMER_CURL is a CURL, and an unscoped "DECLINE" rule would
# otherwise paint it as chest work.
# Shape: (name substring, categories or None for any, primary, secondary,
#         is_compound override or None)

# Category groups the overrides are scoped to.
_LEGS = frozenset({"SQUAT", "LUNGE", "PLYO", "LEG_CURL", "TOTAL_BODY"})
_HINGE = frozenset({"DEADLIFT", "HYPEREXTENSION", "HIP_SWING", "LEG_CURL"})
_PRESS = frozenset({"BENCH_PRESS", "SHOULDER_PRESS", "PUSH_UP", "TRICEPS_EXTENSION", "FLYE"})
_PULL = frozenset({"ROW", "PULL_UP", "SHRUG", "SUSPENSION"})
_DELTS = frozenset({"LATERAL_RAISE", "SHOULDER_STABILITY", "SHOULDER_PRESS"})
_FLYE = frozenset({"FLYE"})
_ARMS = frozenset({"CURL", "TRICEPS_EXTENSION"})
_CORE = frozenset({"CORE", "CRUNCH", "SIT_UP", "PLANK", "LEG_RAISE", "CHOP", "HYPEREXTENSION"})
_HIP = frozenset({"HIP_STABILITY", "HIP_RAISE", "BANDED_EXERCISES", "SQUAT", "LUNGE"})

NAME_OVERRIDES: list[tuple[str, frozenset[str] | None, list[M], list[M], bool | None]] = [
    # --- Squat and lunge outliers ------------------------------------------
    ("LEG_PRESS", _LEGS, [M.QUADRICEPS, M.GLUTES], [M.HAMSTRINGS, M.ADDUCTORS], True),
    ("HACK_SQUAT", _LEGS, [M.QUADRICEPS], [M.GLUTES, M.HAMSTRINGS], True),
    ("SISSY_SQUAT", _LEGS, [M.QUADRICEPS], [], False),
    ("SUMO_SQUAT", _LEGS, [M.ADDUCTORS, M.GLUTES], [M.QUADRICEPS, M.HAMSTRINGS], True),
    ("PLIE", _LEGS, [M.ADDUCTORS, M.GLUTES], [M.QUADRICEPS, M.CALVES], True),
    ("FRONT_SQUAT", _LEGS, [M.QUADRICEPS], [M.GLUTES, M.ABS, M.ERECTOR_SPINAE], True),
    ("OVERHEAD_SQUAT", _LEGS, [M.QUADRICEPS, M.GLUTES], [M.FRONT_DELTS, M.ABS, M.ERECTOR_SPINAE], True),
    ("STEP_UP", _LEGS, [M.QUADRICEPS, M.GLUTES], [M.HAMSTRINGS, M.CALVES], True),
    ("LEG_EXTENSION", _LEGS, [M.QUADRICEPS], [], False),
    # --- Hinge outliers -----------------------------------------------------
    ("ROMANIAN", _HINGE, [M.HAMSTRINGS, M.GLUTES], [M.ERECTOR_SPINAE, M.FOREARMS], True),
    ("STIFF_LEG", _HINGE, [M.HAMSTRINGS], [M.GLUTES, M.ERECTOR_SPINAE], True),
    ("SUMO_DEADLIFT", _HINGE, [M.GLUTES, M.ADDUCTORS, M.QUADRICEPS], [M.ERECTOR_SPINAE, M.TRAPS], True),
    ("GOOD_MORNING", _HINGE, [M.HAMSTRINGS, M.ERECTOR_SPINAE], [M.GLUTES], True),
    ("NORDIC", _HINGE | _LEGS, [M.HAMSTRINGS], [M.GLUTES, M.CALVES], False),
    # --- Horizontal and vertical press outliers ----------------------------
    ("CLOSE_GRIP", _PRESS, [M.TRICEPS], [M.CHEST, M.FRONT_DELTS], True),
    ("DECLINE", _PRESS, [M.CHEST], [M.TRICEPS], True),
    ("INCLINE", _PRESS, [M.CHEST, M.FRONT_DELTS], [M.TRICEPS], True),
    ("PULLOVER", _PRESS | _PULL, [M.LATS, M.CHEST], [M.TRICEPS, M.ABS], False),
    ("DIP", _PRESS, [M.TRICEPS, M.CHEST], [M.FRONT_DELTS], True),
    ("ARNOLD", _PRESS, [M.FRONT_DELTS, M.SIDE_DELTS], [M.TRICEPS, M.TRAPS], True),
    # --- Pull outliers ------------------------------------------------------
    ("CHIN_UP", _PULL, [M.BICEPS, M.LATS], [M.RHOMBOIDS, M.FOREARMS], True),
    ("FACE_PULL", _PULL | _DELTS, [M.REAR_DELTS], [M.RHOMBOIDS, M.TRAPS], False),
    ("UPRIGHT_ROW", _PULL | _DELTS, [M.SIDE_DELTS, M.TRAPS], [M.BICEPS, M.FOREARMS], True),
    ("REVERSE_FLY", _PULL | _DELTS | _FLYE, [M.REAR_DELTS], [M.RHOMBOIDS, M.TRAPS], False),
    ("REAR_DELT", _PULL | _DELTS | _FLYE, [M.REAR_DELTS], [M.RHOMBOIDS], False),
    ("FRONT_RAISE", _DELTS, [M.FRONT_DELTS], [M.SIDE_DELTS], False),
    # --- Arm outliers -------------------------------------------------------
    ("HAMMER_CURL", _ARMS, [M.BICEPS, M.FOREARMS], [], False),
    ("REVERSE_CURL", _ARMS, [M.FOREARMS], [M.BICEPS], False),
    ("WRIST_CURL", _ARMS, [M.FOREARMS], [], False),
    ("WRIST_EXTENSION", _ARMS, [M.FOREARMS], [], False),
    # --- Core outliers ------------------------------------------------------
    ("SIDE_PLANK", _CORE, [M.OBLIQUES], [M.ABS, M.SIDE_DELTS], False),
    ("SIDE_BEND", _CORE, [M.OBLIQUES], [M.ABS], False),
    ("RUSSIAN_TWIST", _CORE, [M.OBLIQUES], [M.ABS], False),
    ("WOODCHOP", _CORE, [M.OBLIQUES], [M.ABS, M.FRONT_DELTS], True),
    ("BIRD_DOG", _CORE, [M.ERECTOR_SPINAE], [M.GLUTES, M.ABS], False),
    ("SUPERMAN", _CORE, [M.ERECTOR_SPINAE], [M.GLUTES, M.REAR_DELTS], False),
    # --- Hip outliers -------------------------------------------------------
    ("ABDUCTION", _HIP, [M.ABDUCTORS], [M.GLUTES], False),
    ("ADDUCTION", _HIP, [M.ADDUCTORS], [], False),
    ("CLAM", _HIP, [M.ABDUCTORS, M.GLUTES], [], False),
    ("GLUTE_BRIDGE", _HIP, [M.GLUTES], [M.HAMSTRINGS], False),
    ("HIP_THRUST", _HIP, [M.GLUTES], [M.HAMSTRINGS, M.QUADRICEPS], True),
]

# Equipment inferred from tokens in the FIT exercise name. Order matters: the
# first token found wins, so specific compounds precede their components
# (SMITH_MACHINE before MACHINE, MEDICINE_BALL before BALL).
EQUIPMENT_KEYWORDS: list[tuple[str, EquipmentType]] = [
    ("SMITH", EquipmentType.SMITH_MACHINE),
    ("MEDICINE_BALL", EquipmentType.MEDICINE_BALL),
    ("STABILITY_BALL", EquipmentType.STABILITY_BALL),
    ("SWISS_BALL", EquipmentType.STABILITY_BALL),
    ("EXERCISE_BALL", EquipmentType.STABILITY_BALL),
    ("BOSU", EquipmentType.STABILITY_BALL),
    ("KETTLEBELL", EquipmentType.KETTLEBELL),
    ("BARBELL", EquipmentType.BARBELL),
    ("EZ_BAR", EquipmentType.BARBELL),
    ("BODY_BAR", EquipmentType.BARBELL),
    ("DUMBBELL", EquipmentType.DUMBBELL),
    ("CABLE", EquipmentType.CABLE),
    ("PULLEY", EquipmentType.CABLE),
    ("SUSPENSION", EquipmentType.SUSPENSION),
    ("TRX", EquipmentType.SUSPENSION),
    ("BAND", EquipmentType.BAND),
    ("TUBING", EquipmentType.BAND),
    ("MACHINE", EquipmentType.MACHINE),
    ("PLATE", EquipmentType.PLATE),
    ("WEIGHT_PLATE", EquipmentType.PLATE),
    ("BODY_WEIGHT", EquipmentType.BODYWEIGHT),
    ("BODYWEIGHT", EquipmentType.BODYWEIGHT),
]

# Names that are machine work even though they carry no equipment token. Checked
# after EQUIPMENT_KEYWORDS so that BARBELL_HACK_SQUAT still reads as a barbell.
MACHINE_NAME_TOKENS: frozenset[str] = frozenset(
    {
        "LEG_PRESS",
        "LEG_EXTENSION",
        "HACK_SQUAT",
        "PEC_DECK",
        "PULLDOWN",
        "LAT_PULL",
        "HAMMERSTRENGTH",
        "SLED_",
        "ASSISTED",
    }
)

# Category-level equipment default when the name carries no equipment token.
CATEGORY_EQUIPMENT_DEFAULT: dict[str, EquipmentType] = {
    "BENCH_PRESS": EquipmentType.BARBELL,
    "DEADLIFT": EquipmentType.BARBELL,
    "OLYMPIC_LIFT": EquipmentType.BARBELL,
    "SHRUG": EquipmentType.BARBELL,
    "ROW": EquipmentType.BARBELL,
    "LEG_CURL": EquipmentType.MACHINE,
    "BANDED_EXERCISES": EquipmentType.BAND,
    "SUSPENSION": EquipmentType.SUSPENSION,
    "BATTLE_ROPE": EquipmentType.OTHER,
    "SANDBAG": EquipmentType.OTHER,
    "SLED": EquipmentType.OTHER,
    "SLEDGE_HAMMER": EquipmentType.OTHER,
    "TIRE": EquipmentType.OTHER,
}
