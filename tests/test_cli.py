from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pypdf import PdfReader, PdfWriter

from bookletcreator.cli import build_layout, convert_booklet, four_up_groups, normalize_cli_args, run, spread_pairs
from bookletcreator.text_layout import convert_dimension_to_points, resolve_page_size


def test_normalize_cli_args_converts_unicode_dash():
    args = ["--paper-size", "A4", "\u2014font-size", "10"]
    normalized = normalize_cli_args(args)
    assert normalized[2] == "-font-size"


def test_spread_pairs_for_eight_pages():
    assert spread_pairs(8) == [(7, 0), (1, 6), (5, 2), (3, 4)]


def test_four_up_groups_for_sixteen_pages():
    assert four_up_groups(16)[0] == (15, 13, 0, 2)
    assert four_up_groups(16)[1] == (1, 3, 14, 12)


def test_four_up_groups_for_four_pages():
    assert four_up_groups(4) == [(3, 1, 0, 2)]


def test_run_dry_run(tmp_path):
    input_pdf = tmp_path / "in.pdf"
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=612, height=792)
    with input_pdf.open("wb") as f:
        writer.write(f)

    rc = run([str(input_pdf), "--dry-run", "--show-map"])
    assert rc == 0


def test_convert_booklet_from_text_file(tmp_path):
    input_text = tmp_path / "chapter.txt"
    input_text.write_text(("This is a test paragraph.\n\n" * 80), encoding="utf-8")
    output_pdf = tmp_path / "chapter_booklet.pdf"

    results, combined = convert_booklet(
        input_pdf=input_text,
        output_pdf=output_pdf,
        text_page_size="A5",
        body_font_size=14,
        text_margin=48,
        line_spacing=20,
    )

    assert combined is None
    assert results[0].output_path == output_pdf
    assert output_pdf.exists()

    reader = PdfReader(str(output_pdf))
    assert len(reader.pages) >= 1


def test_convert_booklet_four_up_dry_run(tmp_path):
    input_pdf = tmp_path / "four-up.pdf"
    writer = PdfWriter()
    for _ in range(16):
        writer.add_blank_page(width=420, height=595)
    with input_pdf.open("wb") as f:
        writer.write(f)

    results, combined = convert_booklet(
        input_pdf=input_pdf,
        signature_size=16,
        sheet_layout="FOUR_UP",
        dry_run=True,
    )

    assert combined is None
    assert results[0].output_spreads == 4


def test_run_dry_run_with_text_input(tmp_path):
    input_text = tmp_path / "book.txt"
    input_text.write_text(("Sample book text.\n\n" * 120), encoding="utf-8")

    rc = run(
        [
            str(input_text),
            "--dry-run",
            "--text-page-size",
            "6X9",
            "--body-font-size",
            "13",
            "--text-margin",
            "50",
            "--line-spacing",
            "18",
        ]
    )

    assert rc == 0


def test_build_layout_with_custom_panel_size():
    layout = build_layout((612, 792), "CUSTOM", inner_margin=10, paper_width=420, paper_height=680)

    assert layout.panel_width == 420
    assert layout.panel_height == 680
    assert layout.inner_margin == 10


def test_convert_dimension_to_points_supports_metric_units():
    assert round(convert_dimension_to_points(1, "IN"), 2) == 72.00
    assert round(convert_dimension_to_points(2.54, "CM"), 2) == 72.00
    assert round(convert_dimension_to_points(25.4, "MM"), 2) == 72.00


def test_resolve_page_size_converts_custom_metric_units():
    width, height = resolve_page_size("CUSTOM", custom_width=12.7, custom_height=20.32, custom_unit="CM")

    assert round(width, 2) == 360.00
    assert round(height, 2) == 576.00


def test_convert_booklet_from_text_file_with_custom_page_size(tmp_path):
    input_text = tmp_path / "custom.txt"
    input_text.write_text(("Custom sized text page.\n\n" * 90), encoding="utf-8")
    output_pdf = tmp_path / "custom_booklet.pdf"

    results, _ = convert_booklet(
        input_pdf=input_text,
        output_pdf=output_pdf,
        text_page_size="CUSTOM",
        text_page_width=12.7,
        text_page_height=20.32,
        text_page_unit="CM",
        paper_size="CUSTOM",
        paper_width=127,
        paper_height=203.2,
        paper_unit="MM",
    )

    assert results[0].output_path == output_pdf
    assert output_pdf.exists()
