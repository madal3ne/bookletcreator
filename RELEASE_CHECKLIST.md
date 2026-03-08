# Release Checklist

Use this checklist for each release.

## 1. Prepare

- [ ] Confirm working tree is clean.
- [ ] Run tests locally: `pytest`
- [ ] Run quick manual test:
  - [ ] `bookletcreator input.pdf --dry-run --show-map`
  - [ ] `bookletcreator-gui` launches and creates output PDF
- [ ] Update version in `pyproject.toml`.
- [ ] Update `CHANGELOG.md`:
  - [ ] Move items from `[Unreleased]` into new version section.
  - [ ] Add release date in `YYYY-MM-DD`.
  - [ ] Update compare links at the bottom.

## 2. Commit and tag

- [ ] Commit release changes.
- [ ] Create annotated tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- [ ] Push branch and tag: `git push && git push --tags`

## 3. GitHub Release

- [ ] Create a new GitHub Release from tag `vX.Y.Z`.
- [ ] Paste release notes from `RELEASE_TEMPLATE.md`.
- [ ] Publish release.

## 4. PyPI publish verification

- [ ] Confirm GitHub Action `Publish to PyPI` succeeded.
- [ ] Install from PyPI in a clean env: `python -m pip install bookletcreator`
- [ ] Smoke test:
  - [ ] `bookletcreator --help`
  - [ ] `bookletcreator-gui`

## 5. Post-release

- [ ] Bump `pyproject.toml` to next development version if desired.
- [ ] Add initial notes under `[Unreleased]` in `CHANGELOG.md`.
