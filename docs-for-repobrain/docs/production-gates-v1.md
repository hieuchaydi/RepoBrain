# Production Gates v1

This document defines the minimum pass/fail quality gates for moving RepoBrain from alpha-level confidence toward production-grade reliability.

The goal is not to block iteration. The goal is to prevent silent regressions in trust, stability, and release quality.

## Gate Set

All gates below are release blockers unless marked as advisory.

### 1) Build And Install Gate

Pass when:

- package installs from a clean environment using `python -m pip install -e ".[dev,tree-sitter,mcp]"`
- `python -m compileall src testsuite` succeeds

Fail when:

- install fails on supported Python versions (`3.12`, `3.13`)
- compile errors appear in tracked sources

### 2) Lint Gate (Critical)

Pass when:

- `python -m ruff check src testsuite --select E9,F63,F7,F82` succeeds

Fail when:

- syntax/runtime-critical lint errors are detected

### 3) Type Gate (Critical Contracts)

Pass when:

- `python -m mypy` succeeds using `mypy.ini`
- typed contract modules stay valid:
  - `src/repobrain/engine/provider_base.py`
  - `src/repobrain/models.py`

Fail when:

- these core contract modules violate type checks

### 4) Test Gate (Contract + Utility)

Pass when:

- `python -m pytest -q testsuite` succeeds

Fail when:

- any test fails or test discovery is broken

### 5) Coverage Gate (Baseline)

Pass when:

- `python -m pytest -q testsuite --cov=repobrain.engine.provider_base --cov=repobrain.models --cov-report=term-missing --cov-fail-under=80` succeeds

Fail when:

- coverage of the baseline contract modules drops below `80%`

Notes:

- This is intentionally scoped to contract-heavy modules first.
- Expand coverage scope gradually after deterministic tests are added for more subsystems.

### 6) Release Artifact Gate

Pass when:

- `python -m build` succeeds
- `python -m repobrain.cli release-check --repo . --require-dist --format text` succeeds
- wheel/sdist include required frontend artifacts (`webapp/dist/**`)

Fail when:

- release artifact validation reports missing assets or metadata mismatch

### 7) Runtime Trust Gate

Pass when:

- `repobrain doctor --format text` reports local provider path ready
- `repobrain index --format text`, `query`, `trace`, `impact`, and `targets` run on a clean sample repo
- low-evidence queries produce warnings rather than strong confidence language

Fail when:

- trust signals are missing, misleading, or contradictory for weak evidence

## CI Mapping

Current workflow mapping:

- `.github/workflows/ci.yml`: gates 1 to 5
- `.github/workflows/release.yml`: gates 1 to 6
- manual release checklist: gates 6 to 7

## Change Control

When updating these gates:

1. update this file first
2. update CI/release workflows in the same branch
3. include rationale in `CHANGELOG.md` under the unreleased section
4. avoid raising thresholds and changing scope in the same commit as large feature changes
