# Progress Report: Release Validation Follow-Up

Date: 2026-04-18

Current branch: `continue-release-validation-20260418`

Base branch status:

- Started from `continue-wip-20260418`.
- Committed the Windows pytest stabilization work as `a5b757c test: stabilize windows pytest temp handling`.
- Switched to `master`.
- Fast-forward merged `continue-wip-20260418` into `master`.
- Created `continue-release-validation-20260418` from the updated `master`.

## What Was Completed

### 1. Merged the prior pytest stabilization into `master`

The previous work is now on local `master`.

Included changes:

- Updated pytest config so generated locked folders do not get collected.
- Added ignore rules for pytest/temp/build scratch folders.
- Made `doctor` always return `embedding_model` and `reranker_model`, even for local providers.
- Isolated provider-related environment variables in tests so local `.env` values do not make tests flaky.
- Updated handoff/run docs to say the old full-pytest blocker was addressed.

Verification before merge:

- `python -m pytest -q` passed with `60 passed`.
- `npm run build` passed in `webapp/`.
- Python compile check passed for source and test entry files.

### 2. Started release artifact validation work

Added a new release inspection path:

- New module: `src/repobrain/release.py`
- New CLI command: `repobrain release-check`
- New text formatter in `src/repobrain/ux.py`
- New release workflow step in `.github/workflows/release.yml`
- New tests in `tests/test_release.py`
- New CLI smoke coverage in `tests/test_cli.py`

The new command checks:

- version alignment across `pyproject.toml`, `src/repobrain/__init__.py`, and `webapp/package.json`
- required React build assets under `webapp/dist`
- wheel and sdist presence under `dist/`
- whether built wheel/sdist artifacts include `webapp/dist/index.html`, `webapp/dist/app.js`, and `webapp/dist/app.css`

Local usage:

```bash
repobrain release-check --format text
repobrain release-check --require-dist --format text
```

Source-tree usage without editable install:

```powershell
$env:PYTHONPATH='src'
python -m repobrain.cli release-check --repo . --format text
```

### 3. Updated docs for the new release check

Updated:

- `README.md`
- `CHANGELOG.md`
- `docs/cli.md`
- `docs/run.md`
- `docs/release-checklist.md`
- `docs/production-readiness.md`
- `docs/gemini-fallback-handoff.md`

Docs now mention:

- `repobrain release-check --format text` before packaging
- `repobrain release-check --require-dist --format text` after `python -m build`
- release workflow now inspects built artifacts before upload/publish

## Verification Done

### Passed

Targeted release/CLI tests, outside sandbox:

```powershell
python -m pytest tests\test_release.py tests\test_cli.py -q --basetemp=pytest_work_manual_004
```

Result:

```text
12 passed in 1.17s
```

Full test suite, outside sandbox:

```powershell
python -m pytest -q --basetemp=pytest_work_manual_005
```

Result:

```text
64 passed in 3.11s
```

Frontend build:

```powershell
npm run build
```

Result:

```text
repobrain-webapp@0.5.0 build
node build.mjs
```

Release check from source tree:

```powershell
$env:PYTHONPATH='src'
python -m repobrain.cli release-check --repo . --format text
```

Result summary:

```text
Status: WARN
Versions: pyproject=0.5.0 package=0.5.0 webapp=0.5.0
Dist: wheels=0 sdists=0
```

This warning is expected because `python -m build` has not been run yet, so there are no `dist/*.whl` or `dist/*.tar.gz` artifacts to inspect.

### Still problematic inside sandbox

Running pytest without escalation still hits Windows permission issues around pytest basetemp directories in this workspace.

Observed failure shape:

```text
PermissionError: [WinError 5] Access is denied
```

Affected paths included:

- `.pytest_tmp_run_*`
- `pytest_work_run_*`
- manual `pytest_work_manual_*` folders when run inside the sandbox

Important note:

- The same targeted tests and full suite pass outside sandbox.
- Treat this as a workspace/sandbox permission issue, not a product regression.

## What Is Not Done Yet

### 1. Current branch changes are not committed yet

The `continue-release-validation-20260418` branch currently has uncommitted work for the new release-check feature.

Before switching branches next time, review:

```powershell
git status --short --branch
git diff --stat
```

Recommended commit message if the diff still looks good:

```text
feat: add release artifact validation command
```

### 2. Real release artifacts have not been built locally

Not yet run:

```powershell
python -m build
```

After building, run:

```powershell
$env:PYTHONPATH='src'
python -m repobrain.cli release-check --repo . --require-dist --format text
```

Expected goal:

- `Status: PASS`
- `wheels=1`
- `sdists=1`
- packaged frontend asset check passes

### 3. GitHub Actions release workflow has not been run

Not yet done:

- Manual workflow run with `publish = false`
- Download/inspect `repobrain-dist` artifact from GitHub Actions
- Confirm the workflow `release-check --require-dist` step passes in CI

### 4. Live provider validation is still not done

Still requires real keys/network outside this sandbox:

```powershell
repobrain doctor --format text
repobrain provider-smoke --format text
```

Provider-specific live validation still needed for:

- Gemini fallback pool
- OpenAI embeddings, if selected
- Voyage embeddings, if selected
- Cohere reranking, if selected

## Suggested Next Session Plan

1. Start by checking branch and diff:

```powershell
git status --short --branch
git diff --stat
```

2. Run verification outside sandbox if permission errors appear:

```powershell
python -m pytest -q --basetemp=pytest_work_manual_next
npm run build
$env:PYTHONPATH='src'
python -m repobrain.cli release-check --repo . --format text
```

3. If tests are still green, commit current branch:

```powershell
git add .github/workflows/release.yml .gitignore CHANGELOG.md README.md docs src tests pyproject.toml
git commit -m "feat: add release artifact validation command"
```

4. Build real release artifacts:

```powershell
python -m build
```

5. Inspect built artifacts:

```powershell
$env:PYTHONPATH='src'
python -m repobrain.cli release-check --repo . --require-dist --format text
```

6. If artifact check passes, merge this branch back into `master`.

7. Run GitHub Actions release workflow manually with `publish = false`.

8. Only after CI artifact inspection and live-provider smoke checks pass, consider tagging `v0.5.0`.

## Files Changed In Current Workstream

Current uncommitted feature area includes:

- `.github/workflows/release.yml`
- `.gitignore`
- `CHANGELOG.md`
- `README.md`
- `docs/cli.md`
- `docs/gemini-fallback-handoff.md`
- `docs/production-readiness.md`
- `docs/release-checklist.md`
- `docs/run.md`
- `pyproject.toml`
- `src/repobrain/cli.py`
- `src/repobrain/release.py`
- `src/repobrain/ux.py`
- `tests/conftest.py`
- `tests/test_cli.py`
- `tests/test_release.py`

## Decision Notes

- The product work that can be automated locally is release artifact validation.
- The work that cannot be completed in this sandbox is live-provider validation because it needs real API keys and network access.
- The pytest permission problem is environmental. Keep the dynamic basetemp/ignore hardening, but run tests outside sandbox when Windows denies access to generated temp directories.
- Do not tag a release until a real `publish = false` workflow run proves the wheel/sdist artifacts contain the React frontend files.
