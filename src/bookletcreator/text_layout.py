from __future__ import annotations

from dataclasses import dataclass
from html import escape
from io import BytesIO
import re

from reportlab.lib.pagesizes import A4, A5, LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


PAGE_SIZES = {
    "A5": A5,
    "A4": A4,
    "LETTER": LETTER,
    "HALF_LETTER": (396.0, 612.0),
    "6X9": (432.0, 648.0),
}

SIZE_UNITS = {
    "PT": 1.0,
    "IN": 72.0,
    "CM": 72.0 / 2.54,
    "MM": 72.0 / 25.4,
}


@dataclass(frozen=True)
class TextLayoutOptions:
    page_size: str
    body_font_size: float
    margin: float
    line_spacing: float
    custom_width: float | None = None
    custom_height: float | None = None
    custom_unit: str = "PT"


def convert_dimension_to_points(value: float, unit: str) -> float:
    normalized_unit = unit.upper()
    if normalized_unit not in SIZE_UNITS:
        raise ValueError(f"Unsupported size unit: {unit}")
    return value * SIZE_UNITS[normalized_unit]


def resolve_page_size(
    page_size: str,
    custom_width: float | None = None,
    custom_height: float | None = None,
    custom_unit: str = "PT",
) -> tuple[float, float]:
    if page_size == "CUSTOM":
        if custom_width is None or custom_height is None:
            raise ValueError("Custom page size requires both width and height.")
        if custom_width <= 0 or custom_height <= 0:
            raise ValueError("Custom page width and height must be greater than zero.")
        return (
            convert_dimension_to_points(custom_width, custom_unit),
            convert_dimension_to_points(custom_height, custom_unit),
        )

    if page_size not in PAGE_SIZES:
        raise ValueError(f"Unsupported text page size: {page_size}")

    return PAGE_SIZES[page_size]


def _paragraphs_from_text(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise ValueError("Input text file is empty.")

    blocks = re.split(r"\n\s*\n", normalized)
    paragraphs: list[str] = []
    for block in blocks:
        cleaned = " ".join(line.strip() for line in block.splitlines() if line.strip())
        if cleaned:
            paragraphs.append(cleaned)

    if not paragraphs:
        raise ValueError("Input text file does not contain any printable text.")

    return paragraphs


def render_text_to_pdf_bytes(text: str, options: TextLayoutOptions) -> bytes:
    if options.body_font_size <= 0:
        raise ValueError("--body-font-size must be greater than zero.")
    if options.margin < 0:
        raise ValueError("--text-margin must be zero or positive.")
    if options.line_spacing <= 0:
        raise ValueError("--line-spacing must be greater than zero.")

    page_size = resolve_page_size(
        options.page_size,
        custom_width=options.custom_width,
        custom_height=options.custom_height,
        custom_unit=options.custom_unit,
    )
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=options.margin,
        rightMargin=options.margin,
        topMargin=options.margin,
        bottomMargin=options.margin,
    )

    body_style = ParagraphStyle(
        name="BookBody",
        fontName="Times-Roman",
        fontSize=options.body_font_size,
        leading=options.line_spacing,
        spaceAfter=0,
    )

    story = []
    for paragraph in _paragraphs_from_text(text):
        story.append(Paragraph(escape(paragraph), body_style))
        story.append(Spacer(1, options.body_font_size * 0.6))

    doc.build(story)
    return buffer.getvalue()
