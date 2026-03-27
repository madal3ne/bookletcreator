# BookletCreator

BookletCreator turns a regular PDF into a print-ready booklet PDF (imposed for duplex printing, short-edge flip).

## Features

- Booklet page imposition (correct fold/staple order)
- Auto padding with blank pages to multiples of 4
- Optional page numbers
- Accepts pasted Unicode dashes in CLI flags
- Optional paper target (`AUTO`, `A4`, `LETTER`)
- Optional inner margin (gutter) between booklet panels
- Signature splitting (4, 8, 16 pages, etc.) for stitched sections
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

### CLI: with output path and page numbers

```bash
bookletcreator input.pdf -o output_booklet.pdf --add-page-numbers
```

### CLI: signatures (stitched sections)

```bash
bookletcreator input.pdf --signature-size 16
```

This creates multiple outputs like `input_sig01.pdf`, `input_sig02.pdf`, ...

### CLI: custom layout and preview

```bash
bookletcreator input.pdf --paper-size A4 --inner-margin 10 --show-map --dry-run
```

### GUI

```bash
bookletcreator-gui
```

Then select input/output files, adjust options, and click **Create Booklet**.

### Windows local script fallback

```powershell
python .\booklet_maker.py .\input.pdf --add-page-numbers
```

## Common options

- `--add-page-numbers`: draw page numbers on each panel
- `--start-number N`: first displayed page number (default `1`)
- `--font-size N`: page number font size (default `11`)
- `--bottom-margin N`: number position from bottom in points (default `18`)
- `--paper-size {AUTO,A4,LETTER}`: panel paper size target
- `--inner-margin N`: gap between left/right panel in points
- `--signature-size N`: split into N-page signatures (multiple of 4)
- `--show-map`: print spread mapping
- `--dry-run`: run without writing output

## Print settings

- Duplex printing
- Flip on short edge
- Print at 100% scale (or disable "fit to page" in printer dialog)

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
- Mixed page sizes are rejected with a clear error.
