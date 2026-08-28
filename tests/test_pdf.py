from __future__ import annotations

import json
from pathlib import Path

import pytest
from pypdf import PdfReader

from parallax_line_delivery.pdf import (
    BOLD_FONT_CANDIDATES,
    REGULAR_FONT_CANDIDATES,
    build_pdf,
)


ROOT = Path(__file__).resolve().parents[1]


def _first_font(candidates: tuple[str, ...]) -> str | None:
    return next((candidate for candidate in candidates if Path(candidate).is_file()), None)


def _uris(reader: PdfReader) -> set[str]:
    found: set[str] = set()
    for page in reader.pages:
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            action = annotation.get("/A")
            if action and action.get("/URI"):
                found.add(str(action["/URI"]))
    return found


@pytest.mark.pdf
def test_pdf_is_a4_deterministic_and_keeps_all_source_links(tmp_path: Path) -> None:
    regular = _first_font(REGULAR_FONT_CANDIDATES)
    bold = _first_font(BOLD_FONT_CANDIDATES)
    if not regular or not bold:
        pytest.skip("Noto CJK is installed in CI by the delivery workflow")

    brief = json.loads((ROOT / "examples/brief.sample.json").read_text(encoding="utf-8"))
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    build_pdf(brief, first, regular_font=regular, bold_font=bold)
    build_pdf(brief, second, regular_font=regular, bold_font=bold)

    assert first.read_bytes() == second.read_bytes()
    reader = PdfReader(first)
    assert len(reader.pages) >= 4
    width = float(reader.pages[0].mediabox.width)
    height = float(reader.pages[0].mediabox.height)
    assert width == pytest.approx(595.28, abs=1)
    assert height == pytest.approx(841.89, abs=1)
    expected_urls = {
        source["url"]
        for key in ("theme_a", "theme_b", "theme_ai")
        for source in brief[key]["sources"]
    }
    assert expected_urls <= _uris(reader)


