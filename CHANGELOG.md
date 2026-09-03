# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Added
- 4-up signature sheet layout via `--sheet-layout FOUR_UP`.
- Tabbed GUI layout with grouped settings for files, layout, text input, page numbers, and output.
- Combined-signature output controls, including `--only-combined`.
- Page-numbering offset via `--skip-numbering-pages`.

## [0.1.0] - 2026-03-08

### Added
- Core booklet PDF imposition engine.
- CLI command `bookletcreator` for converting PDFs to booklet layout.
- Optional page numbering (`--add-page-numbers`, `--start-number`, `--skip-numbering-pages`, `--font-size`, `--bottom-margin`).
- Paper target options (`--paper-size AUTO|A4|LETTER`).
- Inner panel margin option (`--inner-margin`).
- Signature splitting (4, 8, 16 pages, etc.) for stitched sections.
- 4-up signature sheets with two source pages on each half of the sheet.
- Combined-signature output controls.
- Planning and debug options (`--show-map`, `--dry-run`).
- Unicode-dash normalization for robust CLI argument parsing.
- Backward-compatible launcher script `booklet_maker.py`.
- Desktop GUI command `bookletcreator-gui`.
- Project packaging via `pyproject.toml`.
- Basic automated tests.
- GitHub Actions CI workflow for test/build.
- GitHub Actions publish workflow for PyPI trusted publishing.
- Documentation, license, and repository hygiene files.

[Unreleased]: https://github.com/madal3ne/bookletcreator/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/madal3ne/bookletcreator/releases/tag/v0.1.0
