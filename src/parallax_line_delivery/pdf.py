"""Polished Japanese A4 PDF rendering for PARALLAX briefs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable
from xml.sax.saxutils import escape, quoteattr

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


INK = HexColor("#111827")
MUTED = HexColor("#657084")
PAPER = HexColor("#F6F3EC")
WHITE = colors.white
NAVY = HexColor("#0B1830")
BLUE = HexColor("#3268F2")
CYAN = HexColor("#62D6E8")
GOLD = HexColor("#D7A545")
SOFT_BLUE = HexColor("#E9EFFF")
SOFT_GOLD = HexColor("#F6EDDA")
RULE = HexColor("#D8DCE4")

FONT_REGULAR = "ParallaxNotoJP"
FONT_BOLD = "ParallaxNotoJP-Bold"
_FONTS_REGISTERED = False

REGULAR_FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansJP-Regular.otf",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
)
BOLD_FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansJP-Bold.otf",
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
)


class FontSetupError(RuntimeError):
    """Raised when an embeddable Japanese font is unavailable."""


def _first_existing(explicit: str | None, candidates: Iterable[str]) -> Path:
    if explicit:
        path = Path(explicit)
        if path.is_file():
            return path
        raise FontSetupError("Configured Japanese font file was not found")
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return path
    raise FontSetupError("Noto Sans CJK is required; install fonts-noto-cjk or set font paths")


def register_japanese_fonts(
    regular_path: str | None = None,
    bold_path: str | None = None,
) -> None:
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    regular = _first_existing(
        regular_path or os.environ.get("PARALLAX_FONT_REGULAR"), REGULAR_FONT_CANDIDATES
    )
    bold = _first_existing(
        bold_path or os.environ.get("PARALLAX_FONT_BOLD"), BOLD_FONT_CANDIDATES
    )
    # Noto CJK packages commonly ship TTC collections. Subfont zero is the JP face.
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(regular), subfontIndex=0))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold), subfontIndex=0))
    _FONTS_REGISTERED = True


def _safe_text(value: object) -> str:
    return escape(str(value)).replace("\n", "<br/>")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "eyebrow": ParagraphStyle(
            "ParallaxEyebrow",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=8,
            leading=11,
            textColor=BLUE,
            spaceAfter=3 * mm,
            wordWrap="CJK",
        ),
        "cover_title": ParagraphStyle(
            "ParallaxCoverTitle",
            parent=base["Title"],
            fontName=FONT_BOLD,
            fontSize=29,
            leading=36,
            textColor=WHITE,
            alignment=TA_LEFT,
            wordWrap="CJK",
        ),
        "cover_deck": ParagraphStyle(
            "ParallaxCoverDeck",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=11,
            leading=19,
            textColor=HexColor("#CFD8EA"),
            wordWrap="CJK",
        ),
        "theme_title": ParagraphStyle(
            "ParallaxThemeTitle",
            parent=base["Heading1"],
            fontName=FONT_BOLD,
            fontSize=20,
            leading=28,
            textColor=INK,
            spaceAfter=3 * mm,
            wordWrap="CJK",
        ),
        "subtitle": ParagraphStyle(
            "ParallaxSubtitle",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=16,
            textColor=MUTED,
            spaceAfter=6 * mm,
            wordWrap="CJK",
        ),
        "abstract": ParagraphStyle(
            "ParallaxAbstract",
            parent=base["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=10.5,
            leading=18,
            textColor=INK,
            wordWrap="CJK",
        ),
        "section": ParagraphStyle(
            "ParallaxSection",
            parent=base["Heading2"],
            fontName=FONT_BOLD,
            fontSize=13,
            leading=19,
            textColor=NAVY,
            spaceBefore=6 * mm,
            spaceAfter=2.5 * mm,
            keepWithNext=True,
            wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "ParallaxBody",
            parent=base["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=9.3,
            leading=16.5,
            textColor=INK,
            spaceAfter=3 * mm,
            wordWrap="CJK",
            splitLongWords=True,
        ),
        "source_refs": ParagraphStyle(
            "ParallaxSourceRefs",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=7.5,
            leading=11,
            textColor=BLUE,
            wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "ParallaxSmall",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=7.5,
            leading=11.5,
            textColor=MUTED,
            wordWrap="CJK",
        ),
        "small_bold": ParagraphStyle(
            "ParallaxSmallBold",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=8,
            leading=12,
            textColor=INK,
            wordWrap="CJK",
        ),
        "visual_value": ParagraphStyle(
            "ParallaxVisualValue",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=12,
            leading=16,
            textColor=NAVY,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "visual_label": ParagraphStyle(
            "ParallaxVisualLabel",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=7,
            leading=10,
            textColor=BLUE,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "visual_detail": ParagraphStyle(
            "ParallaxVisualDetail",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=7,
            leading=10.5,
            textColor=MUTED,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "center": ParagraphStyle(
            "ParallaxCenter",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=9,
            leading=13,
            textColor=WHITE,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
    }


class AccentRule(Flowable):
    def __init__(self, width: float, color: colors.Color = BLUE):
        super().__init__()
        self.width = width
        self.height = 2
        self.color = color

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(2)
        self.canv.line(0, 0, self.width, 0)


class ParallaxDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, *, report_date: str, **kwargs: Any):
        super().__init__(filename, pagesize=A4, **kwargs)
        self.report_date = report_date
        frame = Frame(
            20 * mm,
            19 * mm,
            A4[0] - 40 * mm,
            A4[1] - 39 * mm,
            id="body",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(
            [PageTemplate(id="parallax", frames=[frame], onPage=self._draw_page)]
        )

    def _draw_page(self, canvas: Any, doc: Any) -> None:
        width, height = A4
        canvas.saveState()
        canvas.setFillColor(PAPER)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        if doc.page == 1:
            canvas.setFillColor(NAVY)
            canvas.rect(0, 0, width, height, fill=1, stroke=0)
            canvas.setFillColor(BLUE)
            canvas.circle(width - 20 * mm, height - 18 * mm, 42 * mm, fill=1, stroke=0)
            canvas.setFillColor(CYAN)
            canvas.circle(width - 5 * mm, height - 9 * mm, 18 * mm, fill=1, stroke=0)
        else:
            canvas.setStrokeColor(RULE)
            canvas.setLineWidth(0.5)
            canvas.line(20 * mm, height - 13 * mm, width - 20 * mm, height - 13 * mm)
            canvas.setFont(FONT_BOLD, 7)
            canvas.setFillColor(MUTED)
            canvas.drawString(20 * mm, height - 10 * mm, "7AM PARALLAX / DEEP RESEARCH")
            canvas.setFont(FONT_REGULAR, 7)
            canvas.drawRightString(width - 20 * mm, height - 10 * mm, self.report_date)
            canvas.setStrokeColor(RULE)
            canvas.line(20 * mm, 13 * mm, width - 20 * mm, 13 * mm)
            canvas.setFont(FONT_REGULAR, 7)
            canvas.drawRightString(width - 20 * mm, 8.5 * mm, f"{doc.page:02d}")
        canvas.restoreState()


def _cover_story(brief: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Flowable]:
    themes = (brief["theme_a"], brief["theme_b"], brief["theme_ai"])
    cards = []
    for label, theme in zip(("A / NOW", "B / TIMELESS", "AI / DAILY"), themes):
        cards.append(
            [
                Paragraph(_safe_text(label), styles["center"]),
                Spacer(1, 2 * mm),
                Paragraph(_safe_text(theme["title"]), styles["small"]),
            ]
        )
    card_table = Table(
        [[Table([[item] for item in card], colWidths=[47 * mm]) for card in cards]],
        colWidths=[50 * mm, 50 * mm, 50 * mm],
        hAlign="LEFT",
    )
    card_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#142542")),
                ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#32425D")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#32425D")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ]
        )
    )
    return [
        Spacer(1, 35 * mm),
        Paragraph(f"ISSUE / {_safe_text(brief['date'])}", styles["eyebrow"]),
        Paragraph(_safe_text(brief["report_title"]), styles["cover_title"]),
        Spacer(1, 6 * mm),
        AccentRule(42 * mm, CYAN),
        Spacer(1, 7 * mm),
        Paragraph(_safe_text(brief["deck"]), styles["cover_deck"]),
        Spacer(1, 28 * mm),
        card_table,
        Spacer(1, 18 * mm),
        Paragraph("THREE THEMES. ONE WIDER VIEW.", styles["eyebrow"]),
        PageBreak(),
    ]


def _key_point_table(theme: dict[str, Any], styles: dict[str, ParagraphStyle]) -> Table:
    rows = []
    for index, point in enumerate(theme["key_points"], start=1):
        rows.append(
            [
                Paragraph(f"{index:02d}", styles["small_bold"]),
                Paragraph(_safe_text(point), styles["body"]),
            ]
        )
    table = Table(rows, colWidths=[12 * mm, 138 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )
    return table


def _visual_panel(theme: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Flowable]:
    visual = theme["visual"]
    node_cells = []
    for node in visual["nodes"]:
        cell = Table(
            [
                [Paragraph(_safe_text(node["label"]), styles["visual_label"])],
                [Paragraph(_safe_text(node["value"]), styles["visual_value"])],
                [Paragraph(_safe_text(node["detail"]), styles["visual_detail"])],
            ],
            colWidths=[46 * mm],
        )
        cell.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                    ("BOX", (0, 0), (-1, -1), 0.6, RULE),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.4 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4 * mm),
                ]
            )
        )
        node_cells.append(cell)
    rows: list[list[object]] = []
    for start in range(0, len(node_cells), 3):
        row: list[object] = list(node_cells[start : start + 3])
        while len(row) < 3:
            row.append("")
        rows.append(row)
    grid = Table(rows, colWidths=[50 * mm, 50 * mm, 50 * mm], hAlign="LEFT")
    grid.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )
    return [
        Paragraph(_safe_text(visual["title"]), styles["section"]),
        grid,
        Paragraph(_safe_text(visual["caption"]), styles["small"]),
    ]


def _source_paragraph(source: dict[str, Any], styles: dict[str, ParagraphStyle]) -> Paragraph:
    published = f" / {escape(source['published_at'])}" if source.get("published_at") else ""
    label = (
        f"<b>[{escape(source['id'])}] {escape(source['publisher'])}{published}</b><br/>"
        f"{escape(source['title'])}<br/>"
        f"<link href={quoteattr(source['url'])} color='#3268F2'>{escape(source['url'])}</link>"
    )
    return Paragraph(label, styles["small"])


def _theme_story(
    theme: dict[str, Any],
    styles: dict[str, ParagraphStyle],
) -> list[Flowable]:
    label_map = {"now": "THEME A / NOW", "timeless": "THEME B / TIMELESS", "ai": "THEME AI / DAILY"}
    accent = GOLD if theme["kind"] == "timeless" else BLUE
    abstract_box = Table(
        [[Paragraph(_safe_text(theme["abstract"]), styles["abstract"])]],
        colWidths=[150 * mm],
        hAlign="LEFT",
    )
    abstract_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT_GOLD if accent == GOLD else SOFT_BLUE),
                ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
                ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
            ]
        )
    )
    story: list[Flowable] = [
        Paragraph(label_map[theme["kind"]], styles["eyebrow"]),
        Paragraph(_safe_text(theme["title"]), styles["theme_title"]),
        Paragraph(_safe_text(theme["subtitle"]), styles["subtitle"]),
        abstract_box,
        *_visual_panel(theme, styles),
        Paragraph("3つの焦点", styles["section"]),
        _key_point_table(theme, styles),
    ]
    if theme.get("angles"):
        angles = "  /  ".join(str(angle).replace("_", " ").upper() for angle in theme["angles"])
        story.extend(
            [
                Spacer(1, 3 * mm),
                Paragraph(f"AI LENSES / {_safe_text(angles)}", styles["source_refs"]),
            ]
        )
    for section in theme["sections"]:
        refs = "  ".join(f"[{ref}]" for ref in section["source_refs"])
        story.extend(
            [
                Paragraph(_safe_text(section["heading"]), styles["section"]),
                Paragraph(_safe_text(section["body"]), styles["body"]),
                Paragraph(f"EVIDENCE  {_safe_text(refs)}", styles["source_refs"]),
            ]
        )
    questions = [
        [Paragraph(f"Q{index}", styles["small_bold"]), Paragraph(_safe_text(question), styles["body"])]
        for index, question in enumerate(theme["reflection_questions"], start=1)
    ]
    question_table = Table(questions, colWidths=[13 * mm, 137 * mm], hAlign="LEFT")
    question_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#EEF0F4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )
    story.extend([Paragraph("視点を広げる問い", styles["section"]), question_table])
    source_items: list[Flowable] = [Paragraph("SOURCES / 調査元", styles["section"])]
    for source in theme["sources"]:
        source_items.extend([_source_paragraph(source, styles), Spacer(1, 2.5 * mm)])
    story.extend([KeepTogether(source_items)])
    return story


def build_pdf(
    brief: dict[str, Any],
    output_path: Path,
    *,
    regular_font: str | None = None,
    bold_font: str | None = None,
) -> None:
    """Render one validated brief. All source URLs remain clickable in the PDF."""
    register_japanese_fonts(regular_font, bold_font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    doc = ParallaxDocTemplate(
        str(output_path),
        report_date=brief["date"],
        title=brief["report_title"],
        author="7AM PARALLAX",
        subject="Japanese daily deep-research brief",
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=19 * mm,
        bottomMargin=19 * mm,
    )
    story: list[Flowable] = _cover_story(brief, styles)
    for index, key in enumerate(("theme_a", "theme_b", "theme_ai")):
        if index:
            story.append(PageBreak())
        story.extend(_theme_story(brief[key], styles))
    def invariant_canvas(*args: Any, **kwargs: Any) -> pdf_canvas.Canvas:
        kwargs["invariant"] = 1
        return pdf_canvas.Canvas(*args, **kwargs)

    doc.build(story, canvasmaker=invariant_canvas)

