# BookletCreator

BookletCreator turns a regular PDF or plain text file into a print-ready booklet PDF (imposed for duplex printing, short-edge flip).

## Features

- Booklet page imposition (correct fold/staple order)
- Plain text ingestion with automatic page layout
- Auto padding with blank pages to multiples of 4
- Optional page numbers
- Accepts pasted Unicode dashes in CLI flags
- Optional paper target (`AUTO`, `A5`, `A4`, `LETTER`, `HALF_LETTER`, `6X9`)
- Optional inner margin (gutter) between booklet panels
- Signature splitting (4, 8, 16 pages, etc.) for stitched sections
- 4-up signature sheets with two source pages on each half of the sheet
- Dry-run mode and spread mapping preview
- Desktop GUI app for non-technical users

## Installation

### From source

```bash
python -m pip install .
```

This installs two commands:

- `bookletcreator` (CLI)
- `bookletcreator-gui` (desktop app)

## Usage

### CLI: basic

```bash
bookletcreator input.pdf
```

### CLI: create a booklet from a text file

```bash
bookletcreator manuscript.txt --text-page-size 6X9 --body-font-size 12 --text-margin 54 --line-spacing 16
```

### CLI: custom page dimensions

You can enter custom sizes in `pt`, `in`, `cm`, or `mm`.

```bash
bookletcreator manuscript.txt --text-page-size CUSTOM --text-page-width 12.7 --text-page-height 20.32 --text-page-unit CM --paper-size CUSTOM --paper-width 127 --paper-height 203.2 --paper-unit MM
```

### CLI: with output path and page numbers

```bash
bookletcreator input.pdf -o output_booklet.pdf --add-page-numbers
```

To leave the cover unnumbered and start numbering on the second source page:

```bash
bookletcreator input.pdf --add-page-numbers --skip-numbering-pages 1 --start-number 1
```

### CLI: signatures (stitched sections)

```bash
bookletcreator input.pdf --signature-size 16
```

This creates multiple outputs like `input_sig01.pdf`, `input_sig02.pdf`, ...

To also produce a single combined PDF:

```bash
bookletcreator input.pdf --signature-size 16 --combine-signatures
```

To produce only a single combined PDF (no per-signature files):

```bash
bookletcreator input.pdf --signature-size 16 --only-combined
```

### CLI: 4-up signature sheets

```bash
bookletcreator input.pdf --signature-size 16 --sheet-layout FOUR_UP
```

This creates sheets with four source pages per printed side: top-left, top-right, bottom-left, and bottom-right.
If the final four-up sheet has no reverse side, BookletCreator adds a blank back side so duplex printing stays aligned.

For a 4-page partial signature, you can split the pages across front and back instead:

```bash
bookletcreator input.pdf --signature-size 4 --sheet-layout FOUR_UP --four-up-partial-strategy SPLIT_ACROSS_SIDES
```

### CLI: custom layout and preview

```bash
bookletcreator input.pdf --paper-size A4 --inner-margin 10 --show-map --dry-run
```

### GUI

```bash
bookletcreator-gui
```

Then select a PDF or `.txt` file, adjust the book/page settings, and click **Create Booklet**.

### Windows local script fallback

```powershell
python .\booklet_maker.py .\input.pdf --add-page-numbers
```

## Common options

- `--add-page-numbers`: draw page numbers on each panel
- `--start-number N`: first displayed page number (default `1`)
- `--skip-numbering-pages N`: leave the first N source pages unnumbered
- `--font-size N`: page number font size (default `11`)
- `--bottom-margin N`: number position from bottom in points (default `18`)
- `--paper-size {AUTO,CUSTOM,A5,A4,LETTER,HALF_LETTER,6X9}`: panel paper size target
- `--paper-width N`: custom panel width when using `CUSTOM`
- `--paper-height N`: custom panel height when using `CUSTOM`
- `--paper-unit {PT,IN,CM,MM}`: unit for custom booklet dimensions
- `--text-page-size {CUSTOM,A5,A4,LETTER,HALF_LETTER,6X9}`: source page size for text input
- `--text-page-width N`: custom text page width when using `CUSTOM`
- `--text-page-height N`: custom text page height when using `CUSTOM`
- `--text-page-unit {PT,IN,CM,MM}`: unit for custom text-page dimensions
- `--body-font-size N`: body text font size for text input
- `--text-margin N`: source page margin for text input
- `--line-spacing N`: line spacing for text input
- `--inner-margin N`: gap between left/right panel in points
- `--sheet-layout {BOOKLET,FOUR_UP}`: normal 2-up booklet layout or 4-up signature sheets
- `--four-up-partial-strategy {BLANK_BACK,SPLIT_ACROSS_SIDES}`: how 4-page four-up signatures use duplex sides
- `--signature-size N`: split into N-page signatures (multiple of 4)
- `--combine-signatures`: when signatures are used, also write a combined PDF
- `--only-combined`: when signatures are used, write only the combined PDF
- `--show-map`: print spread mapping
- `--dry-run`: run without writing output

## Print settings

- Duplex printing
- Flip on short edge
- Print at 100% scale (or disable "fit to page" in printer dialog)
- Four-up output is padded with blank back sides when needed for duplex printing.

## Development

Install dev dependencies:

```bash
python -m pip install -e .[dev]
```

Run tests:

```bash
pytest
```

Build package:

```bash
python -m build
```

## GitHub Actions

This repo includes:

- `.github/workflows/ci.yml`: runs tests and package build on pushes/PRs
- `.github/workflows/publish.yml`: publishes to PyPI when a GitHub Release is published

### PyPI trusted publishing setup

1. Create the project on PyPI (name: `bookletcreator`) if it does not exist.
2. In PyPI project settings, add a Trusted Publisher for this GitHub repo.
3. In GitHub, create a release (for example `v0.1.0`) to trigger publish.

## Release Process

- Changelog: `CHANGELOG.md`
- Release checklist: `RELEASE_CHECKLIST.md`
- GitHub release notes template: `RELEASE_TEMPLATE.md`

## Notes

- Input PDF pages must all be the same size.
- Text input must be UTF-8 encoded plain text.
- Custom widths and heights can be specified in `PT`, `IN`, `CM`, or `MM`.
- `72` points = `1` inch.
- Mixed page sizes are rejected with a clear error.
