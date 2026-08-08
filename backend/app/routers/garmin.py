"""Garmin authentication endpoints backing the settings page."""

from __future__ import annotations

from fastapi import APIRouter

from .. import garmin as garmin_client
from ..schemas import GarminLoginIn, GarminStatus, GarminTokenIn

router = APIRouter(prefix="/api/garmin", tags=["garmin"])


@router.get("/status", response_model=GarminStatus)
def garmin_status() -> GarminStatus:
    return garmin_client.status()


@router.post("/login", response_model=GarminStatus)
def garmin_login(payload: GarminLoginIn) -> GarminStatus:
    """Sign in and store only the resulting garth tokens.

    The password is used for this call and then dropped; it is never written to
    the database or to disk.
    """
    return garmin_client.login(payload.email, payload.password, payload.mfa_code)


@router.post("/token", response_model=GarminStatus)
def garmin_token(payload: GarminTokenIn) -> GarminStatus:
    """Adopt a session token issued elsewhere, so no password reaches MyoFit."""
    return garmin_client.login_with_token(payload.token)


@router.post("/logout", response_model=GarminStatus)
def garmin_logout() -> GarminStatus:
    return garmin_client.logout()
