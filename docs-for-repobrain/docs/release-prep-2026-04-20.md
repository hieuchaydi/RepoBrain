# RepoBrain Release Prep Notes - 2026-04-20

This note captures the current project health review before writing the next formal release note.

## Current Verdict

RepoBrain is in a much healthier state than before and is suitable for an OSS alpha/MVP release.

Local checks currently put the project around:

- OSS/MVP launch readiness: 8/10
- RepoBrain `ship` score after indexing: 8.8/10
- Production-grade readiness: not yet 10/10

The project is strong enough to present publicly as a serious alpha, but a few release-hardening tasks should be completed before calling it production-ready.

## Verification Snapshot

Commands run from `C:\Users\ASUS\Desktop\new-AI`:

```powershell
python -m pytest -q
npm run build
python -m repobrain index --repo . --format text
python -m repobrain benchmark --repo . --format text
python -m repobrain ship --repo . --format text
python -m repobrain doctor --repo . --format text
```

Results:

- Python tests: 104 passed
- Main webapp build: passed
- Docs frontend build: passed, with a Vite chunk-size warning
- Repo index: 52 files, 281 chunks, 268 symbols, 801 edges
- Benchmark: recall@3 1.0, MRR 1.0, citation accuracy 1.0, edit-target hit rate 1.0
- Ship gate: Ready, 8.8/10
- Git worktree after checks: clean

## Strengths

RepoBrain has a clear product position: a local-first AI codebase analyst that helps coding agents gather better context before editing.

The README is now cleaner after removing the broken Vietnamese overview block. The 60-second demo, CLI examples, Docker commands, provider setup, release track, and docs index make the project easier to understand for new users.

The product surface is stronger than a simple library. It includes:

- CLI workflows
- Local browser UI
- Local HTML reports
- Review, baseline, patch-review, and ship gates
- MCP-style adapter
- Docker support
- Optional remote provider adapters

The test and CI posture is solid for an MVP:

- 104 Python tests currently pass locally
- CI runs on Python 3.12 and 3.13
- CI builds the main webapp
- CI lints and builds the docs frontend
- CI runs strict flake8 checks for Python syntax and undefined names
- CI compiles Python sources and runs pytest

The local-first security posture is a real strength. RepoBrain defaults to local embeddings/reranking and requires explicit opt-in before sending code to remote providers.

The release workflow is already structured: it builds frontend assets, runs tests, builds wheel/sdist artifacts, inspects release artifacts, uploads artifacts, and can publish to PyPI when requested.

## Weaknesses

The benchmark set is still too small. The current benchmark has only 3 cases, so perfect scores are encouraging but not enough to prove retrieval quality on larger or more complex repositories.

The local release check warns if wheel and sdist artifacts have not been built yet. This is not a code bug, but the final release process must include artifact generation and package-content inspection.

There were two CI workflows with overlapping responsibility:

- `.github/workflows/ci.yml`
- `.github/workflows/python-package.yml`

The duplicate `.github/workflows/python-package.yml` workflow has been removed. The main `ci.yml` workflow is now the single pull-request gate for Python 3.12/3.13 tests, webapp build, docs lint/build, compileall, strict flake8 syntax/undefined-name checks, and pytest.

Formatting and lint guardrails are still incomplete. CI runs strict flake8 checks for syntax and undefined names, but broader style formatting is not yet enforced. The repo would benefit from a clear Ruff/Black or Ruff-only setup plus pre-commit.

The active repo memory was confusing. Running `repobrain ship` without `--repo .` could use an older active repo path instead of the current working directory. The CLI now emits a visible stderr notice when it falls back to a saved active repo outside the current directory.

The docs frontend currently builds successfully, but Vite reports a JavaScript chunk above 500 KB. This is acceptable for now, but code splitting should be considered if the docs UI grows.

RepoBrain self-review still flags a possible raw-exception-text leak. The evidence may be noisy, but before a stronger production claim, exception handling should be audited so internal errors do not leak to users.

## Recommended Next Work

1. Add a shared formatter/linter setup, preferably Ruff plus pre-commit.
2. Expand benchmark coverage from 3 cases to at least 20-50 cases.
3. Run the full release artifact flow:

```powershell
npm run build
python -m build
python -m repobrain release-check --require-dist --format text
```

4. Audit exception handling before making production-ready claims.
5. Consider docs frontend code splitting if bundle size keeps growing.

## Release Note Direction

The next release should present RepoBrain as a cleaner and more complete local-first alpha.

Suggested release themes:

- Cleaner English-first README and launch narrative
- Stronger CI and release validation
- Local browser UI and docs frontend maturity
- Provider setup and smoke-check improvements
- MCP/local workflow improvements
- Safer local-first defaults
- Better ship/readiness diagnostics

Avoid claiming that the project is production-ready. A more accurate phrase is:

> RepoBrain is now a runnable local-first alpha with stronger docs, CI, release checks, provider workflows, and browser UI support.

## Draft Release Title

RepoBrain 0.5.0 - Local-first alpha with stronger UI, providers, and release readiness

## Draft Release Summary

RepoBrain 0.5.0 turns the project into a more complete local-first workflow for understanding repositories before AI-assisted edits. This release sharpens the README, expands the local browser UI and docs experience, adds provider setup and diagnostics, improves release validation, and keeps the default path local-only unless users explicitly enable remote providers.

The release is best described as an alpha/MVP milestone: strong enough for public testing and demos, but still needing broader benchmark coverage, stricter formatting guardrails, and a final exception-handling audit before production-ready claims.
