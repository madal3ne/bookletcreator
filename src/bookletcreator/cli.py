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

from .text_layout import (
    PAGE_SIZES,
    SIZE_UNITS,
    TextLayoutOptions,
    render_text_to_pdf_bytes,
    resolve_page_size,
)

PAPER_SIZES = PAGE_SIZES
SHEET_LAYOUTS = ("BOOKLET", "FOUR_UP")
FOUR_UP_PARTIAL_STRATEGIES = ("BLANK_BACK", "SPLIT_ACROSS_SIDES")


@dataclass(frozen=True)
class NumberingOptions:
    enabled: bool
    start_number: int
    skip_pages: int
    font_size: float
    bottom_margin: float


@dataclass(frozen=True)
class LayoutOptions:
    panel_width: float
    panel_height: float
    inner_margin: float
    sheet_layout: str
    four_up_partial_strategy: str


@dataclass(frozen=True)
class ConversionResult:
    output_path: Path
    input_pages: int
    output_spreads: int
    added_blanks: int
    paper_mode: str
    signature_index: int
    signature_count: int


@dataclass(frozen=True)
class CombinedResult:
    output_path: Path


@dataclass(frozen=True)
class SourceDocument:
    reader: PdfReader
    source_label: str


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
        description="Convert a PDF or text file into booklet-imposed spreads for duplex printing."
    )
    parser.add_argument("input_pdf", type=Path, help="Path to the source PDF or text file.")
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
        "--skip-numbering-pages",
        type=int,
        default=0,
        help="Do not number the first N source pages, useful for covers (default: 0).",
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
        choices=["AUTO", "CUSTOM", *PAPER_SIZES.keys()],
        default="AUTO",
        help="Target single-page paper size for each booklet panel (default: AUTO).",
    )
    parser.add_argument(
        "--paper-width",
        type=float,
        help="Custom booklet panel width in PDF points when --paper-size CUSTOM is used.",
    )
    parser.add_argument(
        "--paper-height",
        type=float,
        help="Custom booklet panel height in PDF points when --paper-size CUSTOM is used.",
    )
    parser.add_argument(
        "--paper-unit",
        type=str.upper,
        choices=list(SIZE_UNITS.keys()),
        default="PT",
        help="Unit for custom booklet dimensions: PT, IN, CM, or MM (default: PT).",
    )
    parser.add_argument(
        "--text-page-size",
        type=str.upper,
        choices=["CUSTOM", *PAPER_SIZES.keys()],
        default="A5",
        help="Page size to use when the input is a text file (default: A5).",
    )
    parser.add_argument(
        "--text-page-width",
        type=float,
        help="Custom text page width in PDF points when --text-page-size CUSTOM is used.",
    )
    parser.add_argument(
        "--text-page-height",
        type=float,
        help="Custom text page height in PDF points when --text-page-size CUSTOM is used.",
    )
    parser.add_argument(
        "--text-page-unit",
        type=str.upper,
        choices=list(SIZE_UNITS.keys()),
        default="PT",
        help="Unit for custom text-page dimensions: PT, IN, CM, or MM (default: PT).",
    )
    parser.add_argument(
        "--body-font-size",
        type=float,
        default=12,
        help="Body font size when the input is a text file (default: 12).",
    )
    parser.add_argument(
        "--text-margin",
        type=float,
        default=54,
        help="Margin in PDF points for text-file layout (default: 54).",
    )
    parser.add_argument(
        "--line-spacing",
        type=float,
        default=16,
        help="Line spacing in PDF points for text-file layout (default: 16).",
    )
    parser.add_argument(
        "--inner-margin",
        type=float,
        default=0,
        help="Gap between the two panels in each spread (points, default: 0).",
    )
    parser.add_argument(
        "--sheet-layout",
        type=str.upper,
        choices=SHEET_LAYOUTS,
        default="BOOKLET",
        help="Sheet layout: BOOKLET for normal 2-up, FOUR_UP for two pages per half-sheet.",
    )
    parser.add_argument(
        "--four-up-partial-strategy",
        type=str.upper,
        choices=FOUR_UP_PARTIAL_STRATEGIES,
        default="BLANK_BACK",
        help="How FOUR_UP handles a 4-page partial signature: BLANK_BACK or SPLIT_ACROSS_SIDES.",
    )
    parser.add_argument(
        "--signature-size",
        type=int,
        default=0,
        help="Split into signatures of N pages (must be multiple of 4). 0 disables.",
    )
    parser.add_argument(
        "--combine-signatures",
        action="store_true",
        help="When using signatures, also write a single combined output PDF.",
    )
    parser.add_argument(
        "--only-combined",
        action="store_true",
        help="When using signatures, write only the combined PDF (no per-signature files).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show booklet plan without writing output files.",
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
        from reportlab.platypus import SimpleDocTemplate  # noqa: F401
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "This feature requires reportlab. Install with: python -m pip install reportlab"
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


def number_for_index(page_index: int, total_count: int, start_number: int, skip_pages: int = 0) -> Optional[int]:
    if page_index >= total_count or page_index < skip_pages:
        return None
    return start_number + page_index - skip_pages


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


def place_page_rotated_in_cell(
    target_page,
    source_page,
    cell_x: float,
    cell_y: float,
    cell_width: float,
    cell_height: float,
) -> None:
    src_w, src_h = page_size_key(source_page)
    scale = min(cell_width / src_h, cell_height / src_w)
    rotated_w = src_h * scale
    rotated_h = src_w * scale

    dx = cell_x + (cell_width - rotated_w) / 2
    dy = cell_y + (cell_height - rotated_h) / 2 + rotated_h

    transform = Transformation().scale(scale, scale).rotate(-90).translate(tx=dx, ty=dy)
    target_page.merge_transformed_page(source_page, transform)


def build_four_up_number_overlay(
    sheet_width: float,
    sheet_height: float,
    placements: tuple[tuple[Optional[int], object, float, float, float, float], ...],
    font_size: float,
    bottom_margin: float,
):
    from reportlab.pdfgen import canvas

    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(sheet_width, sheet_height))
    c.setFont("Helvetica", font_size)

    for number, page, cell_x, cell_y, cell_width, cell_height in placements:
        if number is None:
            continue

        src_w, src_h = page_size_key(page)
        scale = min(cell_width / src_h, cell_height / src_w)
        rotated_w = src_h * scale
        rotated_h = src_w * scale

        dx = cell_x + (cell_width - rotated_w) / 2
        dy = cell_y + (cell_height - rotated_h) / 2 + rotated_h

        x = dx + (bottom_margin * scale)
        y = dy - ((src_w * scale) / 2)

        c.saveState()
        c.translate(x, y)
        c.rotate(-90)
        c.drawCentredString(0, 0, str(number))
        c.restoreState()

    c.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]


def build_layout(
    first_size: tuple[float, float],
    paper_size: str,
    inner_margin: float,
    sheet_layout: str = "BOOKLET",
    four_up_partial_strategy: str = "BLANK_BACK",
    paper_width: float | None = None,
    paper_height: float | None = None,
    paper_unit: str = "PT",
) -> LayoutOptions:
    if inner_margin < 0:
        raise ValueError("--inner-margin must be zero or positive.")

    if paper_size == "AUTO":
        panel_w, panel_h = first_size
    else:
        panel_w, panel_h = resolve_page_size(
            paper_size,
            custom_width=paper_width,
            custom_height=paper_height,
            custom_unit=paper_unit,
        )

    if sheet_layout not in SHEET_LAYOUTS:
        raise ValueError(f"--sheet-layout must be one of: {', '.join(SHEET_LAYOUTS)}")
    if four_up_partial_strategy not in FOUR_UP_PARTIAL_STRATEGIES:
        raise ValueError(
            f"--four-up-partial-strategy must be one of: {', '.join(FOUR_UP_PARTIAL_STRATEGIES)}"
        )

    return LayoutOptions(
        panel_width=panel_w,
        panel_height=panel_h,
        inner_margin=inner_margin,
        sheet_layout=sheet_layout,
        four_up_partial_strategy=four_up_partial_strategy,
    )


def load_source_document(
    input_path: Path,
    text_page_size: str,
    text_page_width: float | None,
    text_page_height: float | None,
    text_page_unit: str,
    body_font_size: float,
    text_margin: float,
    line_spacing: float,
) -> SourceDocument:
    suffix = input_path.suffix.lower()
    if suffix == ".txt":
        ensure_reportlab()
        text = input_path.read_text(encoding="utf-8")
        rendered_pdf = render_text_to_pdf_bytes(
            text,
            TextLayoutOptions(
                page_size=text_page_size,
                body_font_size=body_font_size,
                margin=text_margin,
                line_spacing=line_spacing,
                custom_width=text_page_width,
                custom_height=text_page_height,
                custom_unit=text_page_unit,
            ),
        )
        return SourceDocument(reader=PdfReader(BytesIO(rendered_pdf)), source_label="text")

    return SourceDocument(reader=PdfReader(str(input_path)), source_label="pdf")


def impose_booklet_pages(
    pages: list,
    numbering: NumberingOptions,
    layout: LayoutOptions,
    show_map: bool,
    global_offset: int,
    total_pages: int,
    signature_index: int,
) -> tuple[PdfWriter, int, int]:
    original_count = len(pages)
    padded_count = ((original_count + 3) // 4) * 4

    spread_width = (layout.panel_width * 2) + layout.inner_margin
    spread_height = layout.panel_height

    writer = PdfWriter()
    pairs = spread_pairs(padded_count)

    if show_map:
        header = f"Signature {signature_index} map (left, right):"
        print(header)

    for spread_num, (left_idx, right_idx) in enumerate(pairs, start=1):
        spread_page = writer.add_blank_page(width=spread_width, height=spread_height)

        if show_map:
            left_label = "blank" if left_idx >= original_count else str(global_offset + left_idx + 1)
            right_label = "blank" if right_idx >= original_count else str(global_offset + right_idx + 1)
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
            left_global = global_offset + left_idx
            right_global = global_offset + right_idx
            overlay = build_number_overlay(
                spread_width=spread_width,
                spread_height=spread_height,
                panel_width=layout.panel_width,
                left_number=number_for_index(
                    left_global,
                    total_pages,
                    numbering.start_number,
                    numbering.skip_pages,
                ),
                right_number=number_for_index(
                    right_global,
                    total_pages,
                    numbering.start_number,
                    numbering.skip_pages,
                ),
                font_size=numbering.font_size,
                bottom_margin=numbering.bottom_margin,
            )
            spread_page.merge_page(overlay)

    return writer, original_count, padded_count


def four_up_groups(
    padded_count: int,
    partial_strategy: str = "BLANK_BACK",
) -> list[tuple[int, int, int, int]]:
    pairs = spread_pairs(padded_count)
    if padded_count == 4:
        left, right = pairs
        if partial_strategy == "SPLIT_ACROSS_SIDES":
            blank = padded_count
            return [(left[0], blank, left[1], blank), (right[0], blank, right[1], blank)]
        return [(left[0], right[0], left[1], right[1])]

    groups: list[tuple[int, int, int, int]] = []
    for start in range(0, len(pairs), 4):
        block = pairs[start : start + 4]
        if len(block) < 4:
            block += [(padded_count, padded_count)] * (4 - len(block))
        front_left, back_left, front_right, back_right = block
        groups.append((front_left[0], front_right[0], front_left[1], front_right[1]))
        groups.append((back_left[0], back_right[0], back_left[1], back_right[1]))
    return groups


def impose_four_up_pages(
    pages: list,
    numbering: NumberingOptions,
    layout: LayoutOptions,
    show_map: bool,
    global_offset: int,
    total_pages: int,
    signature_index: int,
) -> tuple[PdfWriter, int, int]:
    original_count = len(pages)
    padded_count = ((original_count + 3) // 4) * 4

    cell_width = layout.panel_height
    cell_height = layout.panel_width
    sheet_width = (cell_width * 2) + layout.inner_margin
    sheet_height = (cell_height * 2) + layout.inner_margin

    writer = PdfWriter()
    groups = four_up_groups(padded_count, layout.four_up_partial_strategy)

    if show_map:
        print(f"Signature {signature_index} 4-up map (top-left, top-right, bottom-left, bottom-right):")

    for sheet_num, group in enumerate(groups, start=1):
        sheet_page = writer.add_blank_page(width=sheet_width, height=sheet_height)
        labels = ["blank" if idx >= original_count else str(global_offset + idx + 1) for idx in group]

        if show_map:
            print(f"  Sheet side {sheet_num}: {', '.join(labels)}")

        cells = (
            (0, cell_height + layout.inner_margin),
            (cell_width + layout.inner_margin, cell_height + layout.inner_margin),
            (0, 0),
            (cell_width + layout.inner_margin, 0),
        )
        for page_idx, (cell_x, cell_y) in zip(group, cells):
            if page_idx < original_count:
                place_page_rotated_in_cell(
                    sheet_page,
                    pages[page_idx],
                    cell_x=cell_x,
                    cell_y=cell_y,
                    cell_width=cell_width,
                    cell_height=cell_height,
                )

        if numbering.enabled:
            placements = tuple(
                (
                    number_for_index(
                        global_offset + page_idx,
                        total_pages,
                        numbering.start_number,
                        numbering.skip_pages,
                    ),
                    pages[page_idx],
                    cell_x,
                    cell_y,
                    cell_width,
                    cell_height,
                )
                for page_idx, (cell_x, cell_y) in zip(group, cells)
                if page_idx < original_count
            )
            overlay = build_four_up_number_overlay(
                sheet_width=sheet_width,
                sheet_height=sheet_height,
                placements=placements,
                font_size=numbering.font_size,
                bottom_margin=numbering.bottom_margin,
            )
            sheet_page.merge_page(overlay)

    if len(writer.pages) % 2:
        writer.add_blank_page(width=sheet_width, height=sheet_height)
        if show_map:
            print(f"  Sheet side {len(writer.pages)}: blank duplex back side")

    return writer, original_count, padded_count


def split_signatures(pages: list, signature_size: int) -> list[list]:
    if signature_size <= 0:
        return [pages]
    if signature_size < 4 or signature_size % 4 != 0:
        raise ValueError("--signature-size must be a multiple of 4 (e.g. 4, 8, 16).")
    return [pages[i : i + signature_size] for i in range(0, len(pages), signature_size)]


def build_output_paths(
    input_pdf: Path,
    output_pdf: Optional[Path],
    signature_count: int,
) -> list[Path]:
    if signature_count == 1:
        return [output_pdf or input_pdf.with_name(f"{input_pdf.stem}_booklet.pdf")]

    if output_pdf is None:
        base_dir = input_pdf.parent
        base_stem = input_pdf.stem
    elif output_pdf.exists() and output_pdf.is_dir():
        base_dir = output_pdf
        base_stem = input_pdf.stem
    else:
        base_dir = output_pdf.parent
        base_stem = output_pdf.stem

    paths: list[Path] = []
    for idx in range(1, signature_count + 1):
        paths.append(base_dir / f"{base_stem}_sig{idx:02d}.pdf")
    return paths


def build_combined_output_path(
    input_pdf: Path,
    output_pdf: Optional[Path],
    signature_count: int,
) -> Path:
    if signature_count == 1:
        return output_pdf or input_pdf.with_name(f"{input_pdf.stem}_booklet.pdf")

    if output_pdf is None:
        return input_pdf.with_name(f"{input_pdf.stem}_booklet.pdf")

    if output_pdf.exists() and output_pdf.is_dir():
        return output_pdf / f"{input_pdf.stem}_booklet.pdf"

    return output_pdf


def convert_booklet(
    input_pdf: Path,
    output_pdf: Optional[Path] = None,
    add_page_numbers: bool = False,
    start_number: int = 1,
    skip_numbering_pages: int = 0,
    font_size: float = 11,
    bottom_margin: float = 18,
    paper_size: str = "AUTO",
    paper_width: float | None = None,
    paper_height: float | None = None,
    paper_unit: str = "PT",
    text_page_size: str = "A5",
    text_page_width: float | None = None,
    text_page_height: float | None = None,
    text_page_unit: str = "PT",
    body_font_size: float = 12,
    text_margin: float = 54,
    line_spacing: float = 16,
    inner_margin: float = 0,
    sheet_layout: str = "BOOKLET",
    four_up_partial_strategy: str = "BLANK_BACK",
    signature_size: int = 0,
    combine_signatures: bool = False,
    only_combined: bool = False,
    show_map: bool = False,
    dry_run: bool = False,
) -> tuple[list[ConversionResult], Optional[CombinedResult]]:
    input_pdf = Path(input_pdf)
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

    source = load_source_document(
        input_pdf,
        text_page_size=text_page_size,
        text_page_width=text_page_width,
        text_page_height=text_page_height,
        text_page_unit=text_page_unit,
        body_font_size=body_font_size,
        text_margin=text_margin,
        line_spacing=line_spacing,
    )
    reader = source.reader
    if not reader.pages:
        raise ValueError(f"Input {source.source_label} has no pages.")

    if add_page_numbers:
        ensure_reportlab()
    if skip_numbering_pages < 0:
        raise ValueError("--skip-numbering-pages must be zero or positive.")

    first_size = page_size_key(reader.pages[0])
    mixed_sizes = [i + 1 for i, p in enumerate(reader.pages) if page_size_key(p) != first_size]
    if mixed_sizes:
        sample = ", ".join(map(str, mixed_sizes[:10]))
        raise ValueError(
            "All pages must have the same size for booklet imposition. "
            f"Mismatched pages include: {sample}"
        )

    numbering = NumberingOptions(
        enabled=add_page_numbers,
        start_number=start_number,
        skip_pages=skip_numbering_pages,
        font_size=font_size,
        bottom_margin=bottom_margin,
    )
    layout = build_layout(
        first_size,
        paper_size,
        inner_margin,
        sheet_layout=sheet_layout,
        four_up_partial_strategy=four_up_partial_strategy,
        paper_width=paper_width,
        paper_height=paper_height,
        paper_unit=paper_unit,
    )

    pages = list(reader.pages)
    signatures = split_signatures(pages, signature_size)
    outputs = build_output_paths(input_pdf, output_pdf, len(signatures))

    results: list[ConversionResult] = []
    offset = 0
    total_pages = len(pages)
    if only_combined:
        combine_signatures = True
    combined_writer = PdfWriter() if combine_signatures and len(signatures) > 1 else None

    for sig_idx, (sig_pages, out_path) in enumerate(zip(signatures, outputs), start=1):
        if layout.sheet_layout == "FOUR_UP":
            writer, original_count, padded_count = impose_four_up_pages(
                sig_pages,
                numbering,
                layout,
                show_map,
                global_offset=offset,
                total_pages=total_pages,
                signature_index=sig_idx,
            )
        else:
            writer, original_count, padded_count = impose_booklet_pages(
                sig_pages,
                numbering,
                layout,
                show_map,
                global_offset=offset,
                total_pages=total_pages,
                signature_index=sig_idx,
            )

        if combined_writer is not None:
            for page in writer.pages:
                combined_writer.add_page(page)

        if not dry_run and not (only_combined and len(signatures) > 1):
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("wb") as f:
                writer.write(f)

        results.append(
            ConversionResult(
                output_path=out_path,
                input_pages=original_count,
                output_spreads=len(writer.pages),
                added_blanks=padded_count - original_count,
                paper_mode=paper_size,
                signature_index=sig_idx,
                signature_count=len(signatures),
            )
        )
        offset += original_count

    combined_result: Optional[CombinedResult] = None
    if combined_writer is not None:
        combined_path = build_combined_output_path(input_pdf, output_pdf, len(signatures))
        if not dry_run:
            combined_path.parent.mkdir(parents=True, exist_ok=True)
            with combined_path.open("wb") as f:
                combined_writer.write(f)
        combined_result = CombinedResult(output_path=combined_path)

    return results, combined_result


def run(argv: Optional[list[str]] = None) -> int:
    normalized_argv = normalize_cli_args(argv or sys.argv[1:])
    args = parse_args(normalized_argv)

    results, combined = convert_booklet(
        input_pdf=args.input_pdf,
        output_pdf=args.output,
        add_page_numbers=args.add_page_numbers,
        start_number=args.start_number,
        skip_numbering_pages=args.skip_numbering_pages,
        font_size=args.font_size,
        bottom_margin=args.bottom_margin,
        paper_size=args.paper_size,
        paper_width=args.paper_width,
        paper_height=args.paper_height,
        paper_unit=args.paper_unit,
        text_page_size=args.text_page_size,
        text_page_width=args.text_page_width,
        text_page_height=args.text_page_height,
        text_page_unit=args.text_page_unit,
        body_font_size=args.body_font_size,
        text_margin=args.text_margin,
        line_spacing=args.line_spacing,
        inner_margin=args.inner_margin,
        sheet_layout=args.sheet_layout,
        four_up_partial_strategy=args.four_up_partial_strategy,
        signature_size=args.signature_size,
        combine_signatures=args.combine_signatures,
        only_combined=args.only_combined,
        show_map=args.show_map,
        dry_run=args.dry_run,
    )

    total_input = sum(r.input_pages for r in results)
    total_blanks = sum(r.added_blanks for r in results)

    print(f"Input pages: {total_input}")
    print(f"Signatures: {results[0].signature_count}")
    if total_blanks:
        print(f"Added blank pages for booklet layout: {total_blanks}")
    print(f"Paper mode: {results[0].paper_mode}")
    print("Print tip: duplex, flip on short edge.")

    if args.dry_run:
        print("Dry run enabled: no output files written.")
        return 0

    if not (args.only_combined and results[0].signature_count > 1):
        for result in results:
            label = f"Signature {result.signature_index}/{result.signature_count}"
            print(f"{label} created: {result.output_path}")

    if combined is not None:
        print(f"Combined output created: {combined.output_path}")

    return 0


def main() -> None:
    try:
        raise SystemExit(run())
    except BrokenPipeError:  # pragma: no cover
        raise SystemExit(1)


if __name__ == "__main__":
    main()
