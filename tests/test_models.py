from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from parallax_line_delivery.models import (
    BriefValidationError,
    load_brief,
    load_schema,
    validate_brief,
)


ROOT = Path(__file__).resolve().parents[1]


def sample() -> dict:
    return json.loads((ROOT / "examples/brief.sample.json").read_text(encoding="utf-8"))


def schema() -> dict:
    return load_schema(ROOT / "schema/brief.schema.json")


def test_sample_conforms_to_schema() -> None:
    validate_brief(sample(), schema())


def test_dated_filename_must_match_payload(tmp_path: Path) -> None:
    path = tmp_path / "2026-08-30.json"
    path.write_text(json.dumps(sample(), ensure_ascii=False), encoding="utf-8")
    with pytest.raises(BriefValidationError, match="filename and date"):
        load_brief(path, schema())


def test_ai_theme_and_visual_are_mandatory() -> None:
    without_ai = sample()
    del without_ai["theme_ai"]
    with pytest.raises(BriefValidationError, match="theme_ai"):
        validate_brief(without_ai, schema())

    without_visual = sample()
    del without_visual["theme_a"]["visual"]
    with pytest.raises(BriefValidationError, match="visual"):
        validate_brief(without_visual, schema())


def test_visual_has_three_to_five_nodes() -> None:
    invalid = sample()
    invalid["theme_b"]["visual"]["nodes"] = invalid["theme_b"]["visual"]["nodes"][:2]
    with pytest.raises(BriefValidationError, match="too short"):
        validate_brief(invalid, schema())


def test_every_section_reference_resolves() -> None:
    invalid = copy.deepcopy(sample())
    invalid["theme_ai"]["sections"][0]["source_refs"].append("missing_source")
    with pytest.raises(BriefValidationError, match="unknown sources"):
        validate_brief(invalid, schema())


