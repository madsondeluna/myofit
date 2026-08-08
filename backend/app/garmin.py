"""Garmin Connect integration.

This talks to Garmin's internal workout-service through the `garminconnect`
library, which is an unofficial client: Garmin publishes no contract for these
endpoints and can change them without notice. Every call here is wrapped so a
change upstream surfaces as a readable message instead of a traceback.

Credentials are never persisted. The login exchanges them for OAuth tokens,
and only those tokens are written to disk, in the directory named by
GARMINTOKENS (default ./.garth, which is gitignored).

Tokens are saved through `client.client.dump(...)`. The outer object is the
garminconnect facade and the inner one is its HTTP client, which owns the
token store. garminconnect 0.3.9 no longer exposes a `.garth` attribute, and
reaching for one raises only after a successful authentication, so the error
surfaces as a credential failure for a login that in fact worked.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from .models import Exercise, Workout, WorkoutExercise
from .schemas import GarminStatus, SyncResult

logger = logging.getLogger(__name__)

DEFAULT_TOKEN_DIR = Path(os.getenv("GARMINTOKENS", ".garth")).expanduser()

# Garmin's sport id for strength training, as used by the workout-service JSON.
STRENGTH_SPORT_TYPE = {"sportTypeId": 5, "sportTypeKey": "strength_training"}

# One block per exercise occupies three step orders: the repeat group, the
# exercise step and the rest step.
STEP_ORDERS_PER_BLOCK = 3


class GarminUnavailable(RuntimeError):
    """Raised when the unofficial API cannot be reached or has changed shape."""


def _client(token_dir: Path | None = None):
    """Return a Garmin client restored from stored tokens, or None if absent.

    Imported lazily so that neither the test suite nor a Render boot without
    credentials pays the import cost or fails when the library is missing.
    """
    directory = token_dir or DEFAULT_TOKEN_DIR
    if not directory.exists():
        return None

    try:
        from garminconnect import Garmin
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise GarminUnavailable(f"garminconnect is not installed: {exc}") from exc

    try:
        client = Garmin()
        client.login(tokenstore=str(directory))
        return client
    except Exception as exc:
        # Expired or malformed tokens land here. Treat as "not authenticated"
        # rather than an error, so the UI offers a fresh login.
        logger.info("Stored Garmin session could not be resumed: %s", exc)
        return None


def status(token_dir: Path | None = None) -> GarminStatus:
    try:
        client = _client(token_dir)
    except GarminUnavailable as exc:
        return GarminStatus(authenticated=False, detail=str(exc))

    if client is None:
        return GarminStatus(
            authenticated=False, detail="no stored session; sign in on the settings page"
        )

    try:
        name = client.get_full_name()
    except Exception as exc:
        return GarminStatus(authenticated=False, detail=f"session rejected by Garmin: {exc}")

    return GarminStatus(authenticated=True, profile_name=name)


# --- Pending two-factor logins ---------------------------------------------
# Garmin issues its verification code against one specific login attempt, so the
# second request has to resume *that* attempt. HTTP gives us no continuity
# between the two calls, and constructing a fresh client would discard the state
# the code was issued for. The attempt is therefore parked here, keyed by email,
# between the two requests.
#
# In-process and single-node by design: MyoFit is a personal, single-user app.
# A multi-worker deploy would need this in shared storage.
_PENDING_MFA: dict[str, tuple[object, dict, float]] = {}

# Garmin's codes are short lived; anything older than this is not worth keeping.
PENDING_MFA_TTL_SECONDS = 300


def _drop_expired_mfa(now: float) -> None:
    for key, (_client, _state, created) in list(_PENDING_MFA.items()):
        if now - created > PENDING_MFA_TTL_SECONDS:
            del _PENDING_MFA[key]


def login(email: str, password: str, mfa_code: str | None = None,
          token_dir: Path | None = None) -> GarminStatus:
    """Exchange credentials for garth tokens and persist only the tokens."""
    directory = token_dir or DEFAULT_TOKEN_DIR
    directory.mkdir(parents=True, exist_ok=True)

    try:
        from garminconnect import Garmin
    except ImportError as exc:
        return GarminStatus(authenticated=False, detail=f"garminconnect is not installed: {exc}")

    now = time.monotonic()
    _drop_expired_mfa(now)
    key = email.strip().lower()

    # Second leg: a code was supplied and a parked attempt is waiting for it.
    if mfa_code and key in _PENDING_MFA:
        client, state, _created = _PENDING_MFA.pop(key)
        try:
            client.resume_login(state, mfa_code.strip())
            client.client.dump(str(directory))
        except Exception as exc:
            return GarminStatus(authenticated=False, detail=f"verification failed: {exc}")
        return GarminStatus(authenticated=True, profile_name=_full_name(client))

    try:
        # return_on_mfa is always set: it makes the library hand back the
        # pending state instead of blocking on an interactive prompt, which
        # would hang the worker serving the request.
        client = Garmin(email=email, password=password, return_on_mfa=True)
        result = client.login()

        # A pending second factor comes back as ("needs_mfa", client_state).
        if isinstance(result, tuple) and result and result[0] == "needs_mfa":
            _PENDING_MFA[key] = (client, result[1], now)
            return GarminStatus(
                authenticated=False,
                detail="mfa_required: resubmit with the code Garmin sent you",
            )

        client.client.dump(str(directory))
    except Exception as exc:
        return GarminStatus(authenticated=False, detail=f"login failed: {exc}")

    return GarminStatus(authenticated=True, profile_name=_full_name(client))


def login_with_token(token_blob: str, token_dir: Path | None = None) -> GarminStatus:
    """Adopt a session token that was issued somewhere else.

    Garmin has no consumer OAuth a third-party app can redirect to: the only
    way in is the SSO login the mobile app performs, which takes an email and
    a password. This is the path for someone who would rather not type those
    into MyoFit. They authenticate wherever they already trust, and paste the
    resulting token here; MyoFit stores it exactly as it stores one it
    obtained itself, and never sees the password.
    """
    directory = token_dir or DEFAULT_TOKEN_DIR
    directory.mkdir(parents=True, exist_ok=True)

    blob = token_blob.strip()
    # The library distinguishes a token blob from a path purely by length.
    if len(blob) <= 512:
        return GarminStatus(
            authenticated=False,
            detail="that does not look like a Garmin token; paste the whole value",
        )

    try:
        from garminconnect import Garmin
    except ImportError as exc:
        return GarminStatus(authenticated=False, detail=f"garminconnect is not installed: {exc}")

    try:
        client = Garmin()
        client.login(tokenstore=blob)
        client.client.dump(str(directory))
    except Exception as exc:
        return GarminStatus(authenticated=False, detail=f"token rejected: {exc}")

    return GarminStatus(authenticated=True, profile_name=_full_name(client))


def _full_name(client) -> str | None:
    try:
        return client.get_full_name()
    except Exception:
        # The session is valid even when the profile call fails; the name is
        # cosmetic and must not turn a successful login into a failure.
        return None


def logout(token_dir: Path | None = None) -> GarminStatus:
    """Delete the stored tokens. The Garmin session itself is left alone."""
    directory = token_dir or DEFAULT_TOKEN_DIR
    if directory.exists():
        for item in directory.iterdir():
            if item.is_file():
                item.unlink()
    _PENDING_MFA.clear()
    return GarminStatus(authenticated=False, detail="stored session removed")


def build_payload(workout: Workout, entries: list[tuple[WorkoutExercise, Exercise]]) -> dict:
    """Build the workout-service JSON for a strength workout.

    The category and exerciseName values are the FIT SDK enum member names
    carried through from seeding, which is what makes the workout resolve to
    the right movement on the watch.
    """
    try:
        from garminconnect.workout import (
            StrengthWorkout,
            WorkoutSegment,
            create_strength_set,
        )
    except ImportError as exc:
        raise GarminUnavailable(
            f"garminconnect.workout is unavailable: {exc}"
        ) from exc

    steps = []
    step_order = 1
    for workout_exercise, exercise in entries:
        steps.append(
            create_strength_set(
                exercise.garmin_category,
                step_order=step_order,
                sets=max(1, workout_exercise.sets),
                reps=workout_exercise.reps,
                rest_seconds=workout_exercise.rest_seconds,
                exercise_name=exercise.garmin_exercise_name,
                weight_kg=workout_exercise.load_kg,
            )
        )
        step_order += STEP_ORDERS_PER_BLOCK

    payload = StrengthWorkout(
        workoutName=workout.name[:80],
        estimatedDurationInSecs=0,
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType=dict(STRENGTH_SPORT_TYPE),
                workoutSteps=steps,
            )
        ],
    )
    return payload.to_dict()


def push_workout(
    workout: Workout,
    entries: list[tuple[WorkoutExercise, Exercise]],
    token_dir: Path | None = None,
) -> SyncResult:
    try:
        client = _client(token_dir)
    except GarminUnavailable as exc:
        return SyncResult(ok=False, detail=str(exc))

    if client is None:
        return SyncResult(
            ok=False, detail="not signed in to Garmin; sign in on the settings page"
        )

    try:
        payload = build_payload(workout, entries)
    except GarminUnavailable as exc:
        return SyncResult(ok=False, detail=str(exc))

    try:
        response = client.upload_workout(payload)
    except Exception as exc:
        # Covers auth expiry, rate limiting and any endpoint change. The user
        # still has the .FIT export as a fallback.
        return SyncResult(
            ok=False,
            detail=(
                f"Garmin rejected the upload: {exc}. This API is unofficial and "
                "may have changed; the .FIT export is unaffected."
            ),
        )

    workout_id = None
    if isinstance(response, dict):
        workout_id = response.get("workoutId") or response.get("workoutid")
    if workout_id is None:
        return SyncResult(
            ok=False,
            detail=f"upload returned an unexpected response shape: {response!r}",
        )

    return SyncResult(ok=True, garmin_workout_id=str(workout_id))
