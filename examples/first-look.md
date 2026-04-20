# RepoBrain First Look Example

This is the local demo path to show GitHub visitors. It does not require a VPS, hosted backend, or provider API key.

```bash
repobrain first-look --repo /path/to/your-project --format text
```

Representative output:

```text
RepoBrain First Look
Repo: /path/to/your-project
Mode: local-only, no hosted backend required

Indexed surface:
files=128 chunks=342 symbols=211 edges=94
Parsers: heuristic=128

Project review snapshot:
Readiness: needs_hardening
Score: 6.4/10
RepoBrain found a usable project surface, plus a few release and test gaps to inspect first.

Top signals:
1. [high] Missing tests around integration entrypoints
2. [medium] Configuration and runtime paths need hardening
3. [medium] Release docs do not explain provider fallback

Starter questions already tested:
- query: Where is the main flow implemented? -> confidence=0.742 good
  files: backend/app/api/auth.py, backend/app/services/auth_service.py, frontend/src/routes/login.ts
- trace: Trace the primary request flow from entrypoint to service -> confidence=0.688 medium
  files: backend/app/api/auth.py, backend/app/services/auth_service.py, backend/app/config/settings.py
- targets: Which files should I inspect first before changing this repo? -> confidence=0.713 good
  files: backend/app/api/auth.py, backend/app/services/auth_service.py, backend/tests/test_auth_flow.py

Report: /path/to/your-project/.repobrain/report.html

Next commands:
- repobrain serve-web --open
- repobrain chat
- repobrain patch-review --format text
- repobrain key groq --format text
```

Good screenshot sequence:

1. Run `repobrain first-look --format text`.
2. Open `.repobrain/report.html`.
3. Run `repobrain serve-web --open`.
4. Click `Choose folder`, select the same repo, then click `Import + Index`.
5. Ask a grounded question and show the cited files.
