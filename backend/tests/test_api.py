"""HTTP surface: catalog browsing, workout CRUD, reordering, export, sync."""

from __future__ import annotations

import pytest
from garmin_fit_sdk import Decoder, Stream


def _find_exercise(client, category: str, name: str) -> dict:
    response = client.get(
        "/api/exercises", params={"category": category, "q": "", "limit": 200}
    )
    assert response.status_code == 200
    for item in response.json()["items"]:
        if item["garmin_exercise_name"] == name:
            return item
    raise AssertionError(f"{category}/{name} not in the catalog")


@pytest.fixture(name="ids")
def ids_fixture(client):
    squat = _find_exercise(client, "SQUAT", "BARBELL_HACK_SQUAT")
    curl = _find_exercise(client, "CURL", "DUMBBELL_HAMMER_CURL")
    return {"squat": squat["id"], "curl": curl["id"]}


# --- Catalog ---------------------------------------------------------------


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    # The educational disclaimer must be part of the API contract, not only UI copy.
    assert "professional" in response.json()["disclaimer"]


def test_catalog_is_paginated(client):
    response = client.get("/api/exercises", params={"limit": 10})
    body = response.json()
    assert response.status_code == 200
    assert len(body["items"]) == 10
    assert body["total"] > 1000


def test_catalog_search_by_name(client):
    response = client.get("/api/exercises", params={"q": "hack squat"})
    items = response.json()["items"]
    assert items
    assert all("hack squat" in item["display_name"].lower() for item in items)


def test_catalog_filter_by_muscle_does_not_match_substrings(client):
    """"abs" must not match "abductors"; the JSON needle is quoted for this."""
    response = client.get("/api/exercises", params={"muscle": "abs", "limit": 200})
    items = response.json()["items"]
    assert items
    for item in items:
        assert "abs" in item["primary_muscles"] + item["secondary_muscles"]


def test_facets_expose_the_full_taxonomy(client):
    body = client.get("/api/exercises/facets").json()
    assert len(body["muscles"]) == 19
    assert all(entry["views"] for entry in body["muscles"])
    assert {v for entry in body["muscles"] for v in entry["views"]} == {"front", "back"}
    assert "SQUAT" in body["categories"]


# --- Workout CRUD ----------------------------------------------------------


def test_create_and_read_workout(client, ids):
    payload = {
        "name": "Leg day",
        "exercises": [
            {"exercise_id": ids["squat"], "sets": 4, "reps": 8, "rest_seconds": 120, "load_kg": 90},
            {"exercise_id": ids["curl"], "sets": 3, "reps": 12, "rest_seconds": 60},
        ],
    }
    created = client.post("/api/workouts", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Leg day"
    assert [entry["position"] for entry in body["exercises"]] == [0, 1]

    fetched = client.get(f"/api/workouts/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["exercises"][0]["exercise"]["garmin_category"] == "SQUAT"


def test_defaults_are_three_by_twelve(client, ids):
    body = client.post(
        "/api/workouts",
        json={"name": "Defaults", "exercises": [{"exercise_id": ids["curl"]}]},
    ).json()
    entry = body["exercises"][0]
    assert (entry["sets"], entry["reps"]) == (3, 12)
    assert 60 <= entry["rest_seconds"] <= 90


def test_unknown_exercise_id_is_rejected(client):
    response = client.post(
        "/api/workouts",
        json={"name": "Bad", "exercises": [{"exercise_id": 999999}]},
    )
    assert response.status_code == 422


def test_blank_name_is_rejected(client):
    assert client.post("/api/workouts", json={"name": "   "}).status_code == 422


def test_update_replaces_the_exercise_list(client, ids):
    workout = client.post(
        "/api/workouts",
        json={"name": "V1", "exercises": [{"exercise_id": ids["squat"]}]},
    ).json()

    updated = client.put(
        f"/api/workouts/{workout['id']}",
        json={"name": "V2", "exercises": [{"exercise_id": ids["curl"], "sets": 5}]},
    )
    body = updated.json()
    assert body["name"] == "V2"
    assert len(body["exercises"]) == 1
    assert body["exercises"][0]["sets"] == 5


def test_delete_removes_the_workout_and_its_entries(client, ids):
    workout = client.post(
        "/api/workouts",
        json={"name": "Temp", "exercises": [{"exercise_id": ids["squat"]}]},
    ).json()

    assert client.delete(f"/api/workouts/{workout['id']}").status_code == 204
    assert client.get(f"/api/workouts/{workout['id']}").status_code == 404


def test_list_reports_exercise_counts(client, ids):
    client.post(
        "/api/workouts",
        json={
            "name": "Counted",
            "exercises": [{"exercise_id": ids["squat"]}, {"exercise_id": ids["curl"]}],
        },
    )
    rows = client.get("/api/workouts").json()
    assert any(row["exercise_count"] == 2 for row in rows)


# --- Reordering ------------------------------------------------------------


def test_reorder_applies_the_new_order(client, ids):
    workout = client.post(
        "/api/workouts",
        json={
            "name": "Reorder",
            "exercises": [{"exercise_id": ids["squat"]}, {"exercise_id": ids["curl"]}],
        },
    ).json()
    entry_ids = [entry["id"] for entry in workout["exercises"]]

    response = client.post(
        f"/api/workouts/{workout['id']}/reorder",
        json={"workout_exercise_ids": list(reversed(entry_ids))},
    )
    body = response.json()
    assert [entry["id"] for entry in body["exercises"]] == list(reversed(entry_ids))
    assert [entry["position"] for entry in body["exercises"]] == [0, 1]


def test_partial_reorder_is_rejected(client, ids):
    workout = client.post(
        "/api/workouts",
        json={
            "name": "Reorder",
            "exercises": [{"exercise_id": ids["squat"]}, {"exercise_id": ids["curl"]}],
        },
    ).json()
    first = workout["exercises"][0]["id"]

    response = client.post(
        f"/api/workouts/{workout['id']}/reorder",
        json={"workout_exercise_ids": [first]},
    )
    assert response.status_code == 422


# --- Derived data ----------------------------------------------------------


def test_muscle_load_is_normalised_and_sorted(client, ids):
    body = client.post(
        "/api/workouts",
        json={
            "name": "Heat",
            "exercises": [
                {"exercise_id": ids["squat"], "sets": 5},
                {"exercise_id": ids["curl"], "sets": 2},
            ],
        },
    ).json()

    load = body["muscle_load"]
    assert load
    assert load[0]["intensity"] == 1.0
    assert all(0.0 <= entry["intensity"] <= 1.0 for entry in load)
    assert load == sorted(load, key=lambda entry: (-entry["score"], entry["muscle"]))


def test_isolation_before_compound_warns(client, ids):
    body = client.post(
        "/api/workouts",
        json={
            "name": "Bad order",
            "exercises": [{"exercise_id": ids["curl"]}, {"exercise_id": ids["squat"]}],
        },
    ).json()
    assert any(w["code"] == "isolation_before_compound" for w in body["warnings"])


def test_compound_first_does_not_warn(client, ids):
    body = client.post(
        "/api/workouts",
        json={
            "name": "Good order",
            "exercises": [{"exercise_id": ids["squat"]}, {"exercise_id": ids["curl"]}],
        },
    ).json()
    assert body["warnings"] == []


def test_isolation_only_workout_warns(client, ids):
    body = client.post(
        "/api/workouts",
        json={"name": "Isolation only", "exercises": [{"exercise_id": ids["curl"]}]},
    ).json()
    assert any(w["code"] == "no_compound" for w in body["warnings"])


# --- Export and sync -------------------------------------------------------


def test_fit_export_downloads_a_decodable_file(client, ids):
    workout = client.post(
        "/api/workouts",
        json={"name": "Export me", "exercises": [{"exercise_id": ids["squat"], "sets": 2}]},
    ).json()

    response = client.get(f"/api/workouts/{workout['id']}/export.fit")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.ant.fit"
    assert "Export_me.fit" in response.headers["content-disposition"]

    messages, errors = Decoder(Stream.from_byte_array(response.content)).read()
    assert errors == []
    assert messages["workout_mesgs"][0]["wkt_name"] == "Export me"


def test_empty_workout_cannot_be_exported(client):
    workout = client.post("/api/workouts", json={"name": "Empty"}).json()
    assert client.get(f"/api/workouts/{workout['id']}/export.fit").status_code == 422


def test_sync_without_a_session_reports_cleanly(client, ids):
    """No stored Garmin session: the endpoint must explain, not raise."""
    workout = client.post(
        "/api/workouts",
        json={"name": "Sync", "exercises": [{"exercise_id": ids["squat"]}]},
    ).json()

    response = client.post(f"/api/workouts/{workout['id']}/sync")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert "sign in" in body["detail"]


def test_garmin_status_without_a_session(client):
    body = client.get("/api/garmin/status").json()
    assert body["authenticated"] is False


# --- Static frontend guard -------------------------------------------------


def test_unknown_api_path_is_a_404_not_the_spa(client):
    """A typo'd endpoint must fail as a missing route, not return index.html."""
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404


def test_spa_fallback_rejects_path_traversal(client):
    """`..` segments must not reach outside the build directory."""
    response = client.get("/../../etc/passwd")
    # Either the route never matches, or it falls back to the SPA. What must
    # never happen is a file from outside frontend/dist coming back.
    assert response.status_code in (200, 404)
    assert b"root:" not in response.content
