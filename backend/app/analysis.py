"""Derived workout data: muscle aggregation for the heat map, and the ordering
heuristic that produces builder warnings.
"""

from __future__ import annotations

from .models import Exercise, WorkoutExercise
from .muscles import MuscleGroup
from .schemas import MuscleLoad, ValidationWarning

# Relative weight of a secondary muscle against a primary one. A secondary hit
# is real work but not the target of the movement, so it counts half.
SECONDARY_WEIGHT = 0.5


def aggregate_muscle_load(
    entries: list[tuple[WorkoutExercise, Exercise]],
) -> list[MuscleLoad]:
    """Combined muscle work across a workout, for the body map heat rendering.

    Score for a muscle is the sum over exercises that hit it of
    `sets * weight`, where weight is 1.0 as a primary target and 0.5 as a
    secondary one. Scaling by sets is what makes 5x5 squats outweigh a single
    set of calf raises, which is the behaviour the heat map needs.
    """
    scores: dict[str, float] = {}
    primary_counts: dict[str, int] = {}
    secondary_counts: dict[str, int] = {}

    for workout_exercise, exercise in entries:
        # Non-strength entries (cardio, warm-up, poses) carry no muscle data
        # and must not dilute the map.
        if not exercise.is_strength:
            continue
        sets = max(1, workout_exercise.sets)

        for muscle in exercise.primary_muscles or []:
            scores[muscle] = scores.get(muscle, 0.0) + sets
            primary_counts[muscle] = primary_counts.get(muscle, 0) + 1

        for muscle in exercise.secondary_muscles or []:
            scores[muscle] = scores.get(muscle, 0.0) + sets * SECONDARY_WEIGHT
            secondary_counts[muscle] = secondary_counts.get(muscle, 0) + 1

    if not scores:
        return []

    peak = max(scores.values())
    result = [
        MuscleLoad(
            muscle=muscle,
            score=round(score, 2),
            primary_count=primary_counts.get(muscle, 0),
            secondary_count=secondary_counts.get(muscle, 0),
            # Normalised against the hardest-worked muscle so the map always
            # uses its full colour range regardless of workout size.
            intensity=round(score / peak, 4) if peak else 0.0,
        )
        for muscle, score in scores.items()
    ]
    # Heaviest first, then alphabetical so the order is stable across requests.
    result.sort(key=lambda item: (-item.score, item.muscle))
    return result


def validate_ordering(
    entries: list[tuple[WorkoutExercise, Exercise]],
) -> list[ValidationWarning]:
    """Ordering heuristics over the is_compound flag.

    Two warnings, both advisory: the API never rejects a workout for them.
    """
    warnings: list[ValidationWarning] = []
    strength = [(we, ex) for we, ex in entries if ex.is_strength]

    if not strength:
        return warnings

    compound_positions = [we.position for we, ex in strength if ex.is_compound]
    isolation_entries = [(we, ex) for we, ex in strength if not ex.is_compound]

    if not compound_positions and isolation_entries:
        warnings.append(
            ValidationWarning(
                code="no_compound",
                message=(
                    "This workout has only isolation movements. Consider opening "
                    "with a compound lift."
                ),
            )
        )
        return warnings

    # Flag each isolation movement that sits before the last compound lift:
    # fatiguing a small muscle first limits the load on the compound that
    # follows it.
    if compound_positions:
        last_compound = max(compound_positions)
        for workout_exercise, exercise in isolation_entries:
            if workout_exercise.position < last_compound:
                warnings.append(
                    ValidationWarning(
                        code="isolation_before_compound",
                        message=(
                            f"{exercise.display_name} is an isolation movement placed "
                            "before a compound lift."
                        ),
                        exercise_position=workout_exercise.position,
                    )
                )

    return warnings


def known_muscles() -> list[str]:
    return [muscle.value for muscle in MuscleGroup]
