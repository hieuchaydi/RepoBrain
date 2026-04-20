# Release Checklist

RepoBrain releases should be boring, reproducible, and explicit. Do not publish because code changed; publish because a user-facing capability is meaningfully more complete or more trustworthy.

Use [Production Gates v1](production-gates-v1.md) as the canonical pass/fail baseline.

## Before A Release

- Confirm `CHANGELOG.md` describes the release in user-facing language.
- Confirm `pyproject.toml` has the intended version and final repository URLs.
- If the browser UI is part of the release, run `npm ci` and `npm run build` in `webapp/`.
- Run `python -m compileall src tests`.
- Run `python -m pytest -q`.
- Run `repobrain quickstart`.
- Run `repobrain doctor --format text`.
- Run `repobrain index --format text` on a clean sample repo.
- Run one `query`, one `trace`, one `impact`, and one `targets` command with `--format text`.
- Run `repobrain report --format text` and confirm `.repobrain/report.html` is generated.
- Run `repobrain release-check --format text` before building artifacts to confirm version alignment and frontend assets.
- If remote providers are part of the release notes, run a live-key smoke test for each configured provider outside CI.

## Manual GitHub Release Workflow

The workflow at `.github/workflows/release.yml` is intentionally manual.

Default mode:

- `publish = false`
- builds wheel and sdist
- runs compile and tests
- runs `repobrain release-check --require-dist --format text` to inspect built wheel/sdist contents
- uploads `dist/*` as a GitHub Actions artifact

Publish mode:

- `publish = true`
- performs the same build and test gates
- publishes to PyPI through trusted publishing

## Tagging

Recommended tag format:

```text
v0.1.0
v0.2.0
v0.3.0
v0.5.0
```

Tag only after the release artifact build succeeds. Use `v0.5.0` when the release includes the integration-heavy track now on `master` such as provider adapters, provider smoke, and the React browser UI. Use `v0.2.0` for a narrower parser/retrieval-quality line, or `v0.1.0` only for the bare MVP line.

## Rollback

- Do not delete source history to hide a bad release.
- Mark the GitHub release as pre-release or withdrawn if needed.
- Publish a patch version with a clear changelog entry.
- Keep local-first defaults unchanged unless there is an explicit security reason.
