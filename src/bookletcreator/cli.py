from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional

try:
    from pypdf import PdfReader, PdfWriter, Transformation
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency 'pypdf'. Install with: python -m pip install pypdf"
    ) from exc


PAPER_SIZES = {
    "A4": (595.28, 841.89),
    "LETTER": (612.0, 792.0),
}


@dataclass(frozen=True)
class NumberingOptions:
    enabled: bool
    start_number: int
    font_size: float
    bottom_margin: float


@dataclass(frozen=True)
class LayoutOptions:
    panel_width: float
    panel_height: float
    inner_margin: float


@dataclass(frozen=True)
class ConversionResult:
    output_path: Path
    input_pages: int
    output_spreads: int
    added_blanks: int
    paper_mode: str


DASH_TRANSLATION = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2212": "-",
    }
)


def normalize_cli_args(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    for token in argv:
        fixed = token.translate(DASH_TRANSLATION)
        while fixed.startswith("---"):
            fixed = fixed[1:]
        normalized.append(fixed)
    return normalized


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a PDF into booklet-imposed spreads for duplex printing."
    )
    parser.add_argument("input_pdf", type=Path, help="Path to the source PDF.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output PDF path. Defaults to <input>_booklet.pdf",
    )
    parser.add_argument(
        "--add-page-numbers",
        action="store_true",
        help="Overlay page numbers at the bottom of each booklet panel.",
    )
    parser.add_argument(
        "--start-number",
        type=int,
        default=1,
        help="Starting page number when --add-page-numbers is used (default: 1).",
    )
    parser.add_argument(
        "--font-size",
        type=float,
        default=11,
        help="Page number font size (default: 11).",
    )
    parser.add_argument(
        "--bottom-margin",
        type=float,
        default=18,
        help="Bottom margin in PDF points for page numbers (default: 18).",
    )
    parser.add_argument(
        "--paper-size",
        type=str.upper,
        choices=["AUTO", *PAPER_SIZES.keys()],
        default="AUTO",
        help="Target single-page paper size for each booklet panel (default: AUTO).",
    )
    parser.add_argument(
        "--inner-margin",
        type=float,
        default=0,
        help="Gap between the two panels in each spread (points, default: 0).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show booklet plan without writing an output file.",
    )
    parser.add_argument(
        "--show-map",
        action="store_true",
        help="Print page mapping for each spread.",
    )
    return parser.parse_args(argv)


def ensure_reportlab() -> None:
    try:
        from reportlab.pdfgen import canvas  # noqa: F401
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "--add-page-numbers requires reportlab. Install with: python -m pip install reportlab"
        ) from exc


def build_number_overlay(
    spread_width: float,
    spread_height: float,
    panel_width: float,
    left_number: Optional[int],
    right_number: Optional[int],
    font_size: float,
    bottom_margin: float,
):
    from reportlab.pdfgen import canvas

    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(spread_width, spread_height))
    c.setFont("Helvetica", font_size)

    if left_number is not None:
        c.drawCentredString(panel_width / 2, bottom_margin, str(left_number))
    if right_number is not None:
        c.drawCentredString(panel_width + (panel_width / 2), bottom_margin, str(right_number))

    c.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]


def page_size_key(page) -> tuple[float, float]:
    box = page.mediabox
    return float(box.width), float(box.height)


def number_for_index(page_index: int, original_count: int, start_number: int) -> Optional[int]:
    if page_index >= original_count:
        return None
    return start_number + page_index


def spread_pairs(padded_count: int) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for sheet_idx in range(padded_count // 4):
        left_outer = padded_count - 1 - (2 * sheet_idx)
        right_outer = 2 * sheet_idx
        left_inner = 2 * sheet_idx + 1
        right_inner = padded_count - 2 - (2 * sheet_idx)
        pairs.extend([(left_outer, right_outer), (left_inner, right_inner)])
    return pairs


def place_page_on_panel(target_page, source_page, panel_x: float, panel_width: float, panel_height: float) -> None:
    src_w, src_h = page_size_key(source_page)
    scale = min(panel_width / src_w, panel_height / src_h)
    new_w = src_w * scale
    new_h = src_h * scale

    dx = panel_x + (panel_width - new_w) / 2
    dy = (panel_height - new_h) / 2

    transform = Transformation().scale(scale, scale).translate(tx=dx, ty=dy)
    target_page.merge_transformed_page(source_page, transform)


def build_layout(first_size: tuple[float, float], paper_size: str, inner_margin: float) -> LayoutOptions:
    if inner_margin < 0:
        raise ValueError("--inner-margin must be zero or positive.")

    if paper_size == "AUTO":
        panel_w, panel_h = first_size
    else:
        panel_w, panel_h = PAPER_SIZES[paper_size]

    return LayoutOptions(panel_width=panel_w, panel_height=panel_h, inner_margin=inner_margin)


def impose_booklet(
    reader: PdfReader,
    numbering: NumberingOptions,
    layout: LayoutOptions,
    show_map: bool = False,
) -> tuple[PdfWriter, int, int]:
    first_size = page_size_key(reader.pages[0])
    mixed_sizes = [i + 1 for i, p in enumerate(reader.pages) if page_size_key(p) != first_size]
    if mixed_sizes:
        sample = ", ".join(map(str, mixed_sizes[:10]))
        raise ValueError(
            "All pages must have the same size for booklet imposition. "
            f"Mismatched pages include: {sample}"
        )

    original_count = len(reader.pages)
    padded_count = ((original_count + 3) // 4) * 4
    pages = list(reader.pages)

    spread_width = (layout.panel_width * 2) + layout.inner_margin
    spread_height = layout.panel_height

    writer = PdfWriter()
    pairs = spread_pairs(padded_count)

    if show_map:
        print("Spread map (left, right):")

    for spread_num, (left_idx, right_idx) in enumerate(pairs, start=1):
        spread_page = writer.add_blank_page(width=spread_width, height=spread_height)

        if show_map:
            left_label = "blank" if left_idx >= original_count else str(left_idx + 1)
            right_label = "blank" if right_idx >= original_count else str(right_idx + 1)
            print(f"  Spread {spread_num}: {left_label}, {right_label}")

        if left_idx < original_count:
            place_page_on_panel(
                spread_page,
                pages[left_idx],
                panel_x=0,
                panel_width=layout.panel_width,
                panel_height=layout.panel_height,
            )
        if right_idx < original_count:
            place_page_on_panel(
                spread_page,
                pages[right_idx],
                panel_x=layout.panel_width + layout.inner_margin,
                panel_width=layout.panel_width,
                panel_height=layout.panel_height,
            )

        if numbering.enabled:
            overlay = build_number_overlay(
                spread_width=spread_width,
                spread_height=spread_height,
                panel_width=layout.panel_width,
                left_number=number_for_index(left_idx, original_count, numbering.start_number),
                right_number=number_for_index(right_idx, original_count, numbering.start_number),
                font_size=numbering.font_size,
                bottom_margin=numbering.bottom_margin,
            )
            spread_page.merge_page(overlay)

    return writer, original_count, padded_count


def convert_booklet(
    input_pdf: Path,
    output_pdf: Optional[Path] = None,
    add_page_numbers: bool = False,
    start_number: int = 1,
    font_size: float = 11,
    bottom_margin: float = 18,
    paper_size: str = "AUTO",
    inner_margin: float = 0,
    show_map: bool = False,
    dry_run: bool = False,
) -> ConversionResult:
    input_pdf = Path(input_pdf)
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

    reader = PdfReader(str(input_pdf))
    if not reader.pages:
        raise ValueError("Input PDF has no pages.")

    if add_page_numbers:
        ensure_reportlab()

    numbering = NumberingOptions(
        enabled=add_page_numbers,
        start_number=start_number,
        font_size=font_size,
        bottom_margin=bottom_margin,
    )
    layout = build_layout(page_size_key(reader.pages[0]), paper_size, inner_margin)

    writer, original_count, padded_count = impose_booklet(reader, numbering, layout, show_map)

    output_path = Path(output_pdf) if output_pdf else input_pdf.with_name(f"{input_pdf.stem}_booklet.pdf")

    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as f:
            writer.write(f)

    return ConversionResult(
        output_path=output_path,
        input_pages=original_count,
        output_spreads=len(writer.pages),
        added_blanks=padded_count - original_count,
        paper_mode=paper_size,
    )


def run(argv: Optional[list[str]] = None) -> int:
    normalized_argv = normalize_cli_args(argv or sys.argv[1:])
    args = parse_args(normalized_argv)

    result = convert_booklet(
        input_pdf=args.input_pdf,
        output_pdf=args.output,
        add_page_numbers=args.add_page_numbers,
        start_number=args.start_number,
        font_size=args.font_size,
        bottom_margin=args.bottom_margin,
        paper_size=args.paper_size,
        inner_margin=args.inner_margin,
        show_map=args.show_map,
        dry_run=args.dry_run,
    )

    print(f"Input pages: {result.input_pages}")
    print(f"Output spread pages: {result.output_spreads}")
    if result.added_blanks:
        print(f"Added blank pages for booklet layout: {result.added_blanks}")
    print(f"Paper mode: {result.paper_mode}")
    print("Print tip: duplex, flip on short edge.")

    if args.dry_run:
        print("Dry run enabled: no output file written.")
        return 0

    print(f"Booklet created: {result.output_path}")
    return 0


def main() -> None:
    try:
        raise SystemExit(run())
    except BrokenPipeError:  # pragma: no cover
        raise SystemExit(1)


if __name__ == "__main__":
    main()
