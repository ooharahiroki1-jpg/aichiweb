"""Load and validate PARALLAX brief documents."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


DATE_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")
MAX_BRIEF_BYTES = 5 * 1024 * 1024
THEME_KEYS = ("theme_a", "theme_b", "theme_ai")


class BriefValidationError(ValueError):
    """Raised when a research brief cannot be safely rendered."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise BriefValidationError(f"Cannot read brief: {path.name}") from exc
    if size > MAX_BRIEF_BYTES:
        raise BriefValidationError(f"Brief exceeds {MAX_BRIEF_BYTES} bytes: {path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BriefValidationError(f"Brief is not valid UTF-8 JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise BriefValidationError(f"Brief root must be an object: {path.name}")
    return value


def _format_json_path(parts: Iterable[object]) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def load_schema(schema_path: Path) -> dict[str, Any]:
    schema = _read_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema exposes several schema-error subclasses
        raise BriefValidationError("The brief schema itself is invalid") from exc
    return schema


def validate_brief(
    data: dict[str, Any],
    schema: dict[str, Any],
    *,
    filename: str | None = None,
) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.absolute_path))
    if errors:
        details = "; ".join(
            f"{_format_json_path(error.absolute_path)}: {error.message}" for error in errors[:8]
        )
        suffix = f"; plus {len(errors) - 8} more" if len(errors) > 8 else ""
        raise BriefValidationError(f"Brief schema validation failed: {details}{suffix}")

    try:
        brief_date = date.fromisoformat(data["date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise BriefValidationError("Brief date is invalid") from exc

    if filename is not None:
        match = DATE_FILE_RE.fullmatch(filename)
        if not match:
            raise BriefValidationError("Brief filename must be YYYY-MM-DD.json")
        if match.group(1) != brief_date.isoformat():
            raise BriefValidationError("Brief filename and date field must match")

    for theme_key in THEME_KEYS:
        theme = data[theme_key]
        source_ids = [source["id"] for source in theme["sources"]]
        if len(source_ids) != len(set(source_ids)):
            raise BriefValidationError(f"{theme_key} contains duplicate source ids")
        known_ids = set(source_ids)
        for index, section in enumerate(theme["sections"]):
            unknown = set(section["source_refs"]) - known_ids
            if unknown:
                names = ", ".join(sorted(unknown))
                raise BriefValidationError(
                    f"{theme_key}.sections[{index}] references unknown sources: {names}"
                )


def load_brief(path: Path, schema: dict[str, Any]) -> dict[str, Any]:
    data = _read_json(path)
    validate_brief(data, schema, filename=path.name)
    return data


def discover_briefs(brief_dir: Path, schema: dict[str, Any]) -> list[dict[str, Any]]:
    if not brief_dir.is_dir():
        raise BriefValidationError("Brief directory does not exist")
    dated_paths = [
        path for path in brief_dir.iterdir() if path.is_file() and DATE_FILE_RE.fullmatch(path.name)
    ]
    if not dated_paths:
        raise BriefValidationError("No briefs matching briefs/YYYY-MM-DD.json were found")
    briefs = [load_brief(path, schema) for path in sorted(dated_paths)]
    dates = [brief["date"] for brief in briefs]
    if len(dates) != len(set(dates)):
        raise BriefValidationError("Brief dates must be unique")
    return briefs


def latest_brief(briefs: Iterable[dict[str, Any]]) -> dict[str, Any]:
    values = list(briefs)
    if not values:
        raise BriefValidationError("No validated briefs are available")
    return max(values, key=lambda brief: brief["date"])


