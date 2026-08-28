from __future__ import annotations

import json
from pathlib import Path

from parallax_line_delivery import builder


ROOT = Path(__file__).resolve().parents[1]


def test_build_preserves_existing_site_and_only_manages_parallax(
    tmp_path: Path, monkeypatch
) -> None:
    brief_dir = tmp_path / "briefs"
    brief_dir.mkdir()
    brief = json.loads((ROOT / "examples/brief.sample.json").read_text(encoding="utf-8"))
    (brief_dir / "2026-08-29.json").write_text(
        json.dumps(brief, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "index.html").write_text("existing homepage", encoding="utf-8")
    (tmp_path / "robots.txt").write_text("User-agent: FriendlyBot\nAllow: /\n", encoding="utf-8")

    def fake_pdf(_brief: dict, output: Path, **_kwargs) -> None:
        output.write_bytes(b"%PDF-1.4 fake deterministic fixture")

    monkeypatch.setattr(builder, "build_pdf", fake_pdf)
    result = builder.build_all(
        brief_dir=brief_dir,
        schema_path=ROOT / "schema/brief.schema.json",
        output_root=tmp_path,
    )

    assert (tmp_path / "index.html").read_text(encoding="utf-8") == "existing homepage"
    assert (tmp_path / "parallax/reports/2026-08-29.pdf").is_file()
    assert "noindex,nofollow" in (tmp_path / "parallax/index.html").read_text(encoding="utf-8")
    robots = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert "User-agent: FriendlyBot" in robots
    assert "Disallow: /aichiweb/parallax/" in robots
    assert result["latest_date"] == "2026-08-29"
    assert result["latest_titles"] == [
        brief["theme_a"]["title"],
        brief["theme_b"]["title"],
        brief["theme_ai"]["title"],
    ]


def test_stale_generated_pdf_is_removed(tmp_path: Path, monkeypatch) -> None:
    brief_dir = tmp_path / "briefs"
    brief_dir.mkdir()
    brief = json.loads((ROOT / "examples/brief.sample.json").read_text(encoding="utf-8"))
    (brief_dir / "2026-08-29.json").write_text(
        json.dumps(brief, ensure_ascii=False), encoding="utf-8"
    )
    reports = tmp_path / "parallax/reports"
    reports.mkdir(parents=True)
    stale = reports / "2026-08-28.pdf"
    stale.write_bytes(b"old")

    monkeypatch.setattr(
        builder,
        "build_pdf",
        lambda _brief, output, **_kwargs: output.write_bytes(b"%PDF-1.4 new"),
    )
    builder.build_all(
        brief_dir=brief_dir,
        schema_path=ROOT / "schema/brief.schema.json",
        output_root=tmp_path,
    )
    assert not stale.exists()


