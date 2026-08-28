"""Build all validated briefs into the existing branch-based Pages site."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from .models import discover_briefs, latest_brief, load_schema
from .pdf import build_pdf


PARALLAX_DIR = "parallax"
REPORT_DIR = "reports"
ROBOTS_MARKER = "# 7AM PARALLAX managed rule"


def _write_if_changed(path: Path, content: str) -> None:
    encoded = content.encode("utf-8")
    if path.is_file() and path.read_bytes() == encoded:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)


def _write_private_index(output_root: Path) -> None:
    index = """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive,nosnippet">
  <title>7AM PARALLAX</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; }
    body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #0b1830; color: #dbe5f7; }
    main { max-width: 34rem; padding: 3rem; }
    p { color: #9caac2; line-height: 1.8; }
  </style>
</head>
<body><main><h1>7AM PARALLAX</h1><p>Private delivery endpoint. Reports are available only from the link sent to you.</p></main></body>
</html>
"""
    _write_if_changed(output_root / PARALLAX_DIR / "index.html", index)


def _merge_robots(output_root: Path) -> None:
    robots_path = output_root / "robots.txt"
    existing = robots_path.read_text(encoding="utf-8") if robots_path.is_file() else ""
    if ROBOTS_MARKER in existing:
        return
    separator = "" if not existing else ("" if existing.endswith("\n") else "\n") + "\n"
    managed = (
        f"{ROBOTS_MARKER}\n"
        "User-agent: *\n"
        "Disallow: /aichiweb/parallax/\n"
    )
    _write_if_changed(robots_path, existing + separator + managed)


def build_all(
    *,
    brief_dir: Path,
    schema_path: Path,
    output_root: Path,
    regular_font: str | None = None,
    bold_font: str | None = None,
) -> dict[str, Any]:
    schema = load_schema(schema_path)
    briefs = discover_briefs(brief_dir, schema)
    report_dir = output_root / PARALLAX_DIR / REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)

    expected_names: set[str] = set()
    for brief in briefs:
        filename = f"{brief['date']}.pdf"
        expected_names.add(filename)
        destination = report_dir / filename
        handle, temporary_name = tempfile.mkstemp(prefix=".parallax-", suffix=".pdf", dir=report_dir)
        os.close(handle)
        temporary = Path(temporary_name)
        try:
            build_pdf(
                brief,
                temporary,
                regular_font=regular_font,
                bold_font=bold_font,
            )
            if destination.is_file() and destination.read_bytes() == temporary.read_bytes():
                temporary.unlink()
            else:
                os.replace(temporary, destination)
        finally:
            if temporary.exists():
                temporary.unlink()

    # The directory is dedicated to generated reports, so removed briefs remove stale PDFs.
    for existing in report_dir.glob("*.pdf"):
        if existing.name not in expected_names:
            existing.unlink()

    _write_private_index(output_root)
    _merge_robots(output_root)
    latest = latest_brief(briefs)
    return {
        "report_count": len(briefs),
        "latest_date": latest["date"],
        "latest_titles": [
            latest["theme_a"]["title"],
            latest["theme_b"]["title"],
            latest["theme_ai"]["title"],
        ],
    }


