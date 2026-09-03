# Release Notes Template

Copy this into the GitHub Release description and replace placeholders.

## BookletCreator vX.Y.Z

### Highlights
- Create print-ready booklet PDFs from PDF or plain text input.
- Split longer books into signatures for stitched binding.
- Use the desktop GUI or command-line workflow.

### What's New
- Normal 2-up booklet layout with automatic blank-page padding.
- 4-up signature sheet layout with `--sheet-layout FOUR_UP`.
- Optional page numbering controls, including cover-page skipping with `--skip-numbering-pages`.
- Signature controls: `--signature-size`, `--combine-signatures`, and `--only-combined`.
- Custom paper and text-page sizes using points, inches, centimeters, or millimeters.
- Tabbed GUI with grouped layout, text, numbering, and output settings.

### Fixes
- Unicode dash handling for copied command-line options.
- Clearer errors for missing dependencies and mixed page sizes.

### Installation

```bash
python -m pip install --upgrade bookletcreator
```

### Quick Start

```bash
bookletcreator input.pdf --add-page-numbers
bookletcreator input.pdf --add-page-numbers --skip-numbering-pages 1
bookletcreator input.pdf --signature-size 16 --sheet-layout FOUR_UP --only-combined
bookletcreator-gui
```

### Notes
- Duplex print setting: **flip on short edge**.
- For full details, see `CHANGELOG.md`.
