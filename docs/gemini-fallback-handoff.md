# Gemini Fallback Handoff

## Goal

Add a Gemini rerank model pool driven by `.env` so RepoBrain can move to the next configured Gemini model when the current model hits quota or rate-limit exhaustion, then document the release-facing changes and leave a clear continuation note for the next session.

The workstream later expanded to cover the local browser UI as well: the web frontend is now served as a React TSX app with English/Vietnamese interface labels, a light/dark theme toggle, and structured diagnostics panels for `doctor` and `provider-smoke`.

## Status

- Date: 2026-04-18
- Status: implementation complete for the current feature cycle, feature branch merged into local `master`, release/tag still not cut
- Owner context: continue release work from `master`
- Source branch for the merged feature work: `feat-web-theme-release-diagnostics`
- Remote feature branch retained at `origin/feat-web-theme-release-diagnostics`

## What Was Completed

### Runtime behavior

- Added `GEMINI_MODELS` environment support for a comma-separated ordered Gemini rerank pool.
- Added `gemini_models` config support inside `[providers]` in `repobrain.toml`.
- Gemini reranking now:
  - starts with the active model
  - detects Gemini quota/rate-limit exhaustion errors
  - switches to the next configured Gemini model
  - keeps the newly healthy model active for later requests
  - still fails fast on non-quota errors such as bad model names or auth/config issues

### Diagnostics

- `repobrain doctor` payload now includes:
  - `embedding_model`
  - `reranker_model`
  - `reranker_models`
  - `reranker_last_failover_error`
- Text output now shows the active reranker model and the configured Gemini fallback pool.
- Local HTML report now shows provider posture, active Gemini reranker model, fallback pool, and last recorded failover event.
- `repobrain provider-smoke` now runs one direct embedding call and one direct reranker call through the configured providers.

### Docs and release notes

- Updated `.env.example` with a real `GEMINI_MODELS` example.
- Updated `README.md`, `docs/config.md`, and `docs/run.md` with fallback-pool guidance.
- Updated `docs/contracts.md` and `docs/cli.md` so the public output shape and CLI/report narrative match the new provider fields.
- Added a reusable `repobrain provider-smoke` command and browser action for direct provider validation.
- Updated `CHANGELOG.md` and `docs/releases.md` so the unreleased line reflects the new provider behavior.
- Added a React TSX browser frontend under `webapp/`, removed the old `src/repobrain/web_frontend` asset mirror, and the Python server now serves the built frontend from `webapp/dist/`.
- Added a light/dark theme toggle and structured diagnostics/activity panels to the React browser UI.
- Added structured `data` payloads to the web `doctor` and `provider-smoke` API responses so the frontend can render release diagnostics without parsing text output.

## Files Changed

- `src/repobrain/engine/providers.py`
- `src/repobrain/engine/core.py`
- `src/repobrain/ux.py`
- `src/repobrain/cli.py`
- `src/repobrain/web.py`
- `tests/test_providers.py`
- `tests/test_config.py`
- `tests/test_engine.py`
- `tests/test_cli.py`
- `tests/test_web.py`
- `.env`
- `.env.example`
- `README.md`
- `docs/config.md`
- `docs/run.md`
- `docs/contracts.md`
- `docs/cli.md`
- `CHANGELOG.md`
- `docs/releases.md`
- `webapp/*`

## Verification Done

### Automated or semi-automated checks

- Added test coverage for:
  - pass-through Gemini model names
  - failover to the next Gemini model on quota exhaustion
  - error when the full Gemini pool is exhausted
  - loading `GEMINI_MODELS` from `.env`
  - bundle construction from `GEMINI_MODELS`
  - doctor payload including reranker model details
  - HTML report rendering of provider pool details
  - provider smoke engine, CLI, and web route coverage
  - React shell and JSON API smoke flow for `serve-web`
  - structured web `doctor` and `provider-smoke` payload coverage

### Manual smoke result

- Python smoke script passed for:
  - default Gemini reranker model selection
  - pass-through model names
  - configured rerank pool behavior

## Known Blockers

- Full `pytest` completion is currently blocked in this workspace by Windows permission errors on pytest temp directories:
  - `WinError 5`
  - affected paths included `pytest_tmp` and `pytest_tmp_rb`
- This looks like an environment or workspace lock issue, not a failure in the fallback logic itself.

## What Is Not Done Yet

### Release execution

- Version bump is now prepared locally on `master` for the `0.5.x` integration line.
- No release tag was created.
- No GitHub release workflow was run.
- No release artifact validation was performed.
- Frontend packaging is now wired into CI/release automation, but the built wheel/sdist still needs a real artifact inspection run with `publish = false`.

### Live-provider validation

- No real network smoke test was run against the Gemini API for the fallback pool.
- The current implementation assumes quota/rate-limit errors are detectable through exception text patterns.
- `repobrain provider-smoke` exists now, but it still needs a real live-key run outside this sandbox.
- Real SDK/runtime responses should still be validated with live keys before a public release.

### UI/report surfacing

- The terminal `doctor` text was updated.
- The HTML report/dashboard now renders provider posture and Gemini pool details.
- The browser UI was reworked into a React TSX frontend with bilingual interface labels.
- The browser UI now also supports light/dark themes and keeps structured diagnostics cards visible for release checks.

## Recommended Next Steps

1. Run `repobrain provider-smoke --format text` with a real Gemini API key and `GEMINI_MODELS` configured in `.env`.
2. Confirm the exact error text or exception shape for quota exhaustion in the Google SDK runtime you use.
3. Tighten `_is_gemini_quota_or_rate_limit_error()` if the real payloads differ.
4. Re-run the full test suite in an environment where pytest temp directories are writable.
5. Only after that, cut the next release from `master` on the `0.5.x` integration line if the browser UI, provider smoke, and live-provider validation all hold up together.

## Frontend Notes

- Frontend source now lives in `webapp/`.
- Build command: `npm run build` from `webapp/`.
- Built files are served from `webapp/dist/`.
- Runtime `repobrain serve-web` does not require Node if the built assets are already present.
- `GET /api/doctor` and `POST /api/provider-smoke` now include structured `data` payloads for the React diagnostics panels.

## Suggested Live Smoke Scenario

1. Configure:
   - `GEMINI_API_KEY`
   - `GEMINI_MODELS`
2. Set `[providers] reranker = "gemini"` in `repobrain.toml`.
3. Run:
   - `repobrain doctor --format text`
   - `repobrain provider-smoke --format text`
   - `repobrain index --format text`
   - `repobrain query "Where is payment retry logic implemented?" --format text`
4. Intentionally place a low-quota or preview model first in `GEMINI_MODELS` if you want to test failover behavior faster.
5. Confirm the request still completes and that `doctor` shows the expected reranker model pool.

## Notes For The Next Person

- The fallback pool currently applies to Gemini reranking only, not Gemini embeddings.
- `GEMINI_MODELS` is intended to be the user-facing `.env` shortcut.
- `REPOBRAIN_GEMINI_RERANK_MODEL` still works and remains the single-model fallback when no pool is configured.
- The repo currently has unrelated local workspace changes and some locked temp folders, so review `git status` carefully before packaging a release.
