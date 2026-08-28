"""Command-line entry point for the branch-based Pages PDF build."""

from __future__ import annotations

import argparse
from pathlib import Path

from .builder import build_all


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build all PARALLAX daily briefs")
    parser.add_argument("--brief-dir", type=Path, default=Path("briefs"))
    parser.add_argument("--schema", type=Path, default=Path("schema/brief.schema.json"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("."),
        help="Existing branch-based GitHub Pages root; only parallax/ and managed robots rules change.",
    )
    parser.add_argument("--font-regular")
    parser.add_argument("--font-bold")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = build_all(
        brief_dir=args.brief_dir,
        schema_path=args.schema,
        output_root=args.output_root,
        regular_font=args.font_regular,
        bold_font=args.font_bold,
    )
    # Intentionally do not print titles, URLs, tokens, or any LINE configuration.
    print(f"Built {result['report_count']} validated PARALLAX report(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


