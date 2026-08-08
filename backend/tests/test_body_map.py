"""The muscle taxonomy and the SVG figures must agree.

MUSCLE_VIEWS declares which anatomical views draw each muscle. If a muscle is
declared for a view but has no path there, the body map renders and highlights
nothing for it: no error, no warning, just a group that never changes colour.
This test is the only thing that catches that.

The figure data lives in TypeScript, so it is read as text rather than
imported. Parsing the two object literals by key is enough: what matters is
which muscle ids are present, not the path geometry.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from backend.app.muscles import MUSCLE_VIEWS, VIEWS, MuscleGroup

FIGURES = Path(__file__).resolve().parents[2] / "frontend" / "src" / "components" / "figures.ts"

# `  quadriceps:` or `  "erector_spinae":` at the start of a line inside an
# object literal.
KEY_PATTERN = re.compile(r'^\s{2}"?([a-z_]+)"?:', re.MULTILINE)


def _object_body(source: str, name: str) -> str:
    """Return the text between the braces of `export const <name> = {...}`."""
    start = source.index(f"export const {name}")
    open_brace = source.index("{", start)
    depth = 0
    for index in range(open_brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[open_brace + 1 : index]
    raise AssertionError(f"unbalanced braces in {name}")


@pytest.fixture(scope="module", name="figure_keys")
def figure_keys_fixture() -> dict[str, set[str]]:
    assert FIGURES.is_file(), f"figure source not found at {FIGURES}"
    source = FIGURES.read_text(encoding="utf-8")
    return {
        "front": set(KEY_PATTERN.findall(_object_body(source, "FRONT_MUSCLES"))),
        "back": set(KEY_PATTERN.findall(_object_body(source, "BACK_MUSCLES"))),
    }


def test_every_declared_muscle_has_a_path(figure_keys):
    missing: list[str] = []
    for muscle, views in MUSCLE_VIEWS.items():
        for view in views:
            if muscle.value not in figure_keys[view]:
                missing.append(f"{view}/{muscle.value}")
    assert missing == [], f"muscles declared but never drawn: {missing}"


def test_no_figure_path_is_outside_the_taxonomy(figure_keys):
    """A path id that is not a MuscleGroup member can never be highlighted."""
    valid = {muscle.value for muscle in MuscleGroup}
    for view in VIEWS:
        unknown = figure_keys[view] - valid
        assert unknown == set(), f"{view} draws unknown muscles: {unknown}"


def test_figures_do_not_draw_muscles_the_taxonomy_hides(figure_keys):
    """A muscle drawn in a view it does not declare would highlight in a place
    the aggregation never accounts for."""
    undeclared: list[str] = []
    for view in VIEWS:
        for drawn in figure_keys[view]:
            declared = MUSCLE_VIEWS[MuscleGroup(drawn)]
            if view not in declared:
                undeclared.append(f"{view}/{drawn}")
    assert undeclared == []


def test_all_nineteen_groups_are_reachable(figure_keys):
    drawn = figure_keys["front"] | figure_keys["back"]
    assert drawn == {muscle.value for muscle in MuscleGroup}
