# RepoBrain v1.2.0

## Highlights
- Added **Prompt Pack workflow** to generate actionable fix prompts from repo evidence for both CLI and Web.
- Improved setup and startup performance for faster first-run experience across machines.
- Stabilized quality gates and fixed Python CLI + mypy issues that impacted CI reliability.

## What's New
- New CLI command: `repobrain prompt`
  - Supports `--source review|ship|patch-review|import|flow`
  - Supports styles `generic|codex|cursor|claude`
  - Supports `--max-prompts`, `--focus`, `--baseline-label`, `--flow-query`, and patch inputs `--base/--files`
- New backend API: `POST /api/prompt-pack`
- Updated web Prompt Pack panel in Workbench: source/style/focus/max/baseline + dynamic flow and patch inputs
- Flow prompt generation now filters per-file prompts by confidence score threshold (default `0.7`)
- Added text renderer for `prompt_pack` payloads in terminal output

## Reliability & DX
- Fixed direct source execution for Python CLI (`python src/repobrain/cli.py ...`)
- Resolved mypy/type issues in provider + CLI-related paths
- Improved Docker/setup defaults and reduced setup friction on new machines
- Added focused tests for prompt-pack generation

## Verification
- `python -m pytest -q` passing
- `python -m repobrain.cli prompt --help` validated
- Frontend rebuilt and synced in `webapp/dist`

## Main Commits Included
- `f019cdc` feat: add prompt pack workflow for cli and web
- `b09cd2c` fix: resolve mypy failures in CLI and provider base
- `764d6a5` fix: allow direct python CLI execution from source
- `765addc` build: speed up setup flow and docker defaults
- `a8d9a2e` perf: reduce CLI startup time with lazy imports

## Notes
- This release targets local-first usage and keeps CI behavior unchanged.
