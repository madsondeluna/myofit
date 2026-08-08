"""FIT workout file export.

Produces a .FIT workout the user can copy into GARMIN/Workouts over USB. This
is the fallback path for when the unofficial Connect API is unavailable.

Step model: every set is emitted as its own step, followed by a rest step. The
FIT profile also allows a REPEAT_UNTIL_STEPS_CMPLT step that loops back over a
range, which is what Garmin Connect itself exports. Explicit expansion is used
here instead because the repeat step encodes its loop target as a raw message
index, and a wrong index produces a file that decodes without error but runs
the wrong number of sets. Expanded steps cannot fail that way, and the round
trip test can assert set-for-set that what was written is what comes back.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.workout_message import WorkoutMessage
from fit_tool.profile.messages.workout_step_message import WorkoutStepMessage
from fit_tool.profile.profile_type import (
    FileType,
    FitBaseUnit,
    Intensity,
    Sport,
    SubSport,
    WorkoutStepDuration,
    WorkoutStepTarget,
)

from .models import Exercise, Workout, WorkoutExercise

# Garmin reserves manufacturer id 1 for itself; 255 is the "development" slot
# used by third-party tools writing files for personal use.
DEVELOPMENT_MANUFACTURER = 255

# FIT stores workout step weight in grams even though the field is named
# exercise_weight. fit-tool applies the scale factor for us, so the value is
# passed in kilograms.
MAX_STEP_NAME = 30


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_fit_workout(
    workout: Workout,
    entries: list[tuple[WorkoutExercise, Exercise]],
    *,
    created_at: datetime | None = None,
) -> bytes:
    """Encode a workout to FIT bytes.

    `entries` must already be ordered by position; the caller owns ordering so
    this function stays free of database access.
    """
    builder = FitFileBuilder(auto_define=True)

    # --- File identity ----------------------------------------------------
    file_id = FileIdMessage()
    file_id.type = FileType.WORKOUT
    file_id.manufacturer = DEVELOPMENT_MANUFACTURER
    file_id.product = 0
    file_id.serial_number = 0x12345678
    stamp = created_at or datetime.now(timezone.utc)
    # fit-tool takes milliseconds since the Unix epoch and converts to the FIT
    # epoch internally.
    file_id.time_created = round(stamp.timestamp() * 1000)
    builder.add(file_id)

    # --- Steps ------------------------------------------------------------
    # Built before the workout message because that message must declare the
    # final step count.
    steps: list[WorkoutStepMessage] = []
    index = 0

    for workout_exercise, exercise in entries:
        for set_number in range(1, max(1, workout_exercise.sets) + 1):
            step = WorkoutStepMessage()
            step.message_index = index
            step.workout_step_name = _truncate(
                f"{exercise.display_name} {set_number}/{workout_exercise.sets}",
                MAX_STEP_NAME,
            )
            step.intensity = Intensity.ACTIVE
            step.duration_type = WorkoutStepDuration.REPS
            step.duration_value = workout_exercise.reps
            step.target_type = WorkoutStepTarget.OPEN
            step.target_value = 0
            # The pair that makes the watch resolve the movement and log it as
            # the right exercise. Both come from the FIT SDK enums via seeding.
            step.exercise_category = exercise.garmin_category_value
            step.exercise_name = exercise.garmin_exercise_name_value
            if workout_exercise.load_kg:
                step.exercise_weight = workout_exercise.load_kg
                step.weight_display_unit = FitBaseUnit.KILOGRAM
            steps.append(step)
            index += 1

            # A rest step after every set except the last one of the last
            # exercise, where it would leave the workout ending on a timer.
            is_final_set = (
                workout_exercise is entries[-1][0]
                and set_number == max(1, workout_exercise.sets)
            )
            if workout_exercise.rest_seconds > 0 and not is_final_set:
                rest = WorkoutStepMessage()
                rest.message_index = index
                rest.workout_step_name = "Rest"
                rest.intensity = Intensity.REST
                rest.duration_type = WorkoutStepDuration.TIME
                # Seconds. fit-tool applies the FIT scale factor of 1000 on
                # write, so passing milliseconds here yields a rest a thousand
                # times too long.
                rest.duration_value = workout_exercise.rest_seconds
                rest.target_type = WorkoutStepTarget.OPEN
                rest.target_value = 0
                steps.append(rest)
                index += 1

    # --- Workout header ---------------------------------------------------
    workout_message = WorkoutMessage()
    workout_message.workout_name = _truncate(workout.name, 60)
    workout_message.sport = Sport.TRAINING
    workout_message.sub_sport = SubSport.STRENGTH_TRAINING
    workout_message.num_valid_steps = len(steps)
    builder.add(workout_message)

    for step in steps:
        builder.add(step)

    return bytes(builder.build().to_bytes())
