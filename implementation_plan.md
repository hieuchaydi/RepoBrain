# RepoBrain Project Roadmap & Implementation Plan

## Project Direction & Goals

Provide a clear, step‑by‑step roadmap to transform the current codebase into a polished, production‑ready AI‑assisted coding assistant that runs locally, offers a premium web UI, and supports extensibility via plugins.

### User Review Required
> **[!IMPORTANT]** Please review the overall timeline and priorities. Let me know if any milestone should be reordered, merged, or removed before we proceed.

### Open Questions
> **[!WARNING]**
> - **Dependency list** – Do you want all optional dependencies (e.g., `tree‑sitter`, `fastapi`) promoted to required runtime dependencies, or keep them optional?
> - **Offline model** – Should we ship a default GGML model now, or provide a script for users to download the model of their choice?
> - **Web UI framework** – Do you prefer vanilla CSS (as currently used) or would you like to adopt TailwindCSS for faster styling? If Tailwind is desired, confirm the version (latest stable).
> - **Testing coverage target** – Is 80 % sufficient for the MVP, or would you like to aim for ≥ 90 %?

Please answer these questions so the plan can be finalised.

## Proposed Changes

### Phase 1 – Foundations (Weeks 1‑4)

**Linting & Type‑Checking**
- **[MODIFY]** `pyproject.toml` – Add `ruff`, `black`, `isort`, `mypy` as dev‑dependencies.
- **[NEW]** `.flake8` – Basic flake8 config.
- **[NEW]** `mypy.ini` – Type‑checking settings.

**Testing Infrastructure**
- **[NEW]** `tests/` – Add `test_cli.py`, `test_engine.py`, `test_web.py` with pytest fixtures.
- **[NEW]** `pytest.ini` – Configure coverage thresholds.
- **[MODIFY]** CI workflow `ci.yml` – Run `ruff`, `mypy`, and `pytest --cov`.

**Packaging Adjustments**
- **[MODIFY]** `pyproject.toml` – Populate `dependencies` with required packages (`fastapi`, `httpx`, `tree-sitter`, etc.) based on the answer to the dependency question.
- **[NEW]** `requirements.txt` – Pin exact versions for reproducible CI builds.

### Phase 2 – CI / Documentation (Weeks 5‑8)

**CI Enhancements**
- **[MODIFY]** `.github/workflows/ci.yml` – Add matrix for Python 3.12‑3.13, run lint, type‑check, tests, and generate coverage badge.

**Documentation**
- **[NEW]** `docs/` – MkDocs site with sections: Overview, Installation, CLI Usage, API Reference, Plugin Development.
- **[MODIFY]** `README.md` – Add badges (build, coverage), setup instructions for web UI, and contribution guide link.

**Web UI Preparation**
- **[NEW]** `webapp/README-webapp.md` – Build/run instructions (`npm install && npm run dev`).
- **[MODIFY]** `webapp/package.json` – Add `eslint`, `prettier` scripts.

### Phase 3 – Offline Model & Plugin System (Weeks 9‑12)

**Offline Model Support**
- **[NEW]** `scripts/download_model.sh` – Downloads a default GGML model and places it in `models/`.
- **[MODIFY]** `src/repobrain/models.py` – Add fallback to load local model if API keys not provided.

**Plugin Architecture**
- **[NEW]** `src/repobrain/plugins/__init__.py` – Define entry‑point namespace `repobrain_plugins`.
- **[NEW]** Example plugins:
  - `code_formatter.py` – Formats code using `black`.
  - `security_scanner.py` – Runs basic secret detection.
- **[MODIFY]** `setup.cfg` – Register entry‑points.

### Phase 4 – Premium Web UI (Weeks 13‑16)

**Design System**
- Adopt a **glassmorphism** style with dark mode, smooth micro‑animations, custom Google Font (e.g., *Inter*).
- **[MODIFY]** `webapp/src/styles.css` – Add CSS variables for theme, transition effects.
- **[NEW]** `webapp/src/components/ThemeProvider.tsx` – Context to toggle dark/light mode.

**UI Features**
- **[NEW]** Dashboard showing readiness checks (pass/warn/fail) with animated status cards.
- **[NEW]** “Run Review” modal with progress spinner.
- **[NEW]** Settings page for API keys, model path, and plugin toggle.

**Build & Deploy**
- **[MODIFY]** `webapp/package.json` – Add `build` script to output to `webapp/dist`.
- **[MODIFY]** `pyproject.toml` – Ensure `webapp/dist/**` is included in wheel (`force-include` already present).

### Phase 5 – Community & Scaling (Months 5‑12)

- Publish a **starter‑template repository** containing the basic plugin scaffold.
- Create a **GitHub Action** (`repobrain-review.yml`) that runs RepoBrain on pull requests.
- Organise a **hackathon** / demo video series to attract contributors.
- Collect **benchmarks** (speed, accuracy) and publish a performance report.

## Verification Plan

### Automated Tests
- Run `pytest` with coverage ≥ 80 % (or 90 % if chosen). CI pipeline must pass lint, type‑check, and tests on each push.

### Manual Checks
- Verify the web UI loads within 2 seconds on a typical laptop.
- Confirm offline model loading works without network access.
- Test plugin discovery by installing a dummy plugin and ensuring it appears in the dashboard.

### Acceptance Criteria
- All CI checks green for the `main` branch.
- `repobrain --help` displays updated commands and options.
- The web UI shows a polished, responsive dashboard with dark mode toggle.
- Documentation builds without errors and is hosted (e.g., GitHub Pages).

---

*Please respond with answers to the open questions so we can lock the plan and generate the task list.*
