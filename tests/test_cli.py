from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pypdf import PdfWriter

from bookletcreator.cli import normalize_cli_args, run, spread_pairs


def test_normalize_cli_args_converts_unicode_dash():
    args = ["--paper-size", "A4", "\u2014font-size", "10"]
    normalized = normalize_cli_args(args)
    assert normalized[2] == "-font-size"


def test_spread_pairs_for_eight_pages():
    assert spread_pairs(8) == [(7, 0), (1, 6), (5, 2), (3, 4)]


def test_run_dry_run(tmp_path):
    input_pdf = tmp_path / "in.pdf"
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=612, height=792)
    with input_pdf.open("wb") as f:
        writer.write(f)

    rc = run([str(input_pdf), "--dry-run", "--show-map"])
    assert rc == 0
