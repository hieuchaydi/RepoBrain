from __future__ import annotations

from collections.abc import Iterable
from typing import Any


SOURCE_CHOICES = ("review", "ship", "patch-review", "import")
STYLE_CHOICES = ("generic", "codex", "cursor", "claude")

_SEVERITY_RANK = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

_STYLE_INTRO = {
    "generic": "You are a senior software engineer asked to improve this codebase safely.",
    "codex": "You are Codex working directly in this repository. Apply focused edits only.",
    "cursor": "You are an IDE coding agent. Produce a minimal, verifiable patch in scope.",
    "claude": "You are a code assistant. Provide a precise patch plan and implementation details.",
}

_STYLE_OUTPUT_CONTRACT = {
    "generic": [
        "Return a concise root-cause summary.",
        "List exact file edits and why each is needed.",
        "Include verification commands and expected outcomes.",
    ],
    "codex": [
        "Return changed file paths and exact patch summary.",
        "List tests/checks you ran and their outcomes.",
        "Flag any remaining risks or manual follow-up.",
    ],
    "cursor": [
        "Return a compact edit plan with exact file targets.",
        "Provide concrete patch details and verification steps.",
        "Include rollback or mitigation notes for risky changes.",
    ],
    "claude": [
        "Return structured sections: Analysis, Patch, Verification.",
        "Keep patch scope narrow and tied to evidence.",
        "List unresolved questions explicitly if any remain.",
    ],
}


def build_prompt_pack(
    *,
    source: str,
    repo_root: str,
    payload: dict[str, Any],
    style: str = "generic",
    max_prompts: int = 6,
) -> dict[str, Any]:
    normalized_source = str(source).strip().lower()
    normalized_style = str(style).strip().lower()
    if normalized_source not in SOURCE_CHOICES:
        raise ValueError(f"`source` must be one of: {', '.join(SOURCE_CHOICES)}.")
    if normalized_style not in STYLE_CHOICES:
        raise ValueError(f"`style` must be one of: {', '.join(STYLE_CHOICES)}.")

    prompt_limit = max(1, min(int(max_prompts), 12))
    if normalized_source == "review":
        prompts = _prompts_from_review(payload, style=normalized_style, max_prompts=prompt_limit)
    elif normalized_source == "ship":
        prompts = _prompts_from_ship(payload, style=normalized_style, max_prompts=prompt_limit)
    elif normalized_source == "patch-review":
        prompts = _prompts_from_patch_review(payload, style=normalized_style, max_prompts=prompt_limit)
    else:
        prompts = _prompts_from_import(payload, style=normalized_style, max_prompts=prompt_limit)

    summary = str(payload.get("summary", "")).strip()
    if not summary:
        summary = f"Prompt pack generated from {normalized_source} evidence."

    return {
        "kind": "prompt_pack",
        "source": normalized_source,
        "style": normalized_style,
        "repo_root": repo_root,
        "summary": summary,
        "count": len(prompts),
        "prompts": prompts,
    }


def _prompts_from_review(payload: dict[str, Any], *, style: str, max_prompts: int) -> list[dict[str, Any]]:
    findings = [item for item in payload.get("findings", []) if isinstance(item, dict)]
    findings.sort(
        key=lambda item: (
            _SEVERITY_RANK.get(str(item.get("severity", "")).lower(), 99),
            str(item.get("category", "")).lower(),
            str(item.get("title", "")).lower(),
        )
    )

    prompts: list[dict[str, Any]] = []
    for finding in findings[:max_prompts]:
        severity = str(finding.get("severity", "medium")).lower()
        category = str(finding.get("category", "quality")).strip() or "quality"
        title = str(finding.get("title", "Address review finding")).strip() or "Address review finding"
        summary = str(finding.get("summary", "")).strip()
        recommendation = str(finding.get("recommendation", "")).strip()
        files = _string_list(finding.get("file_paths", []))[:8]

        objective = recommendation or summary or f"Resolve the finding: {title}."
        evidence = _compact_lines(
            [
                f"Severity: {severity}",
                f"Category: {category}",
                f"Finding: {title}",
                summary,
            ]
        )
        tasks = _category_tasks(category, title)
        acceptance = _acceptance_checks_for_category(category)
        risks = _compact_lines(
            [
                f"High-severity changes can cause regressions in nearby modules." if severity in {"critical", "high"} else "",
                "Avoid unrelated refactors while resolving this issue.",
            ]
        )
        prompts.append(
            _build_prompt_payload(
                title=f"{severity.upper()} - {title}",
                category=category,
                objective=objective,
                files_to_open=files,
                evidence=evidence,
                tasks=tasks,
                acceptance_checks=acceptance,
                risk_notes=risks,
                style=style,
            )
        )
    return prompts


def _prompts_from_ship(payload: dict[str, Any], *, style: str, max_prompts: int) -> list[dict[str, Any]]:
    prompts: list[dict[str, Any]] = []
    blockers = _string_list(payload.get("blockers", []))
    checks = [item for item in payload.get("checks", []) if isinstance(item, dict)]
    review = payload.get("review")
    review_findings: list[dict[str, Any]] = []
    if isinstance(review, dict):
        review_findings = [item for item in review.get("findings", []) if isinstance(item, dict)]

    for blocker in blockers:
        files = _best_review_files(review_findings, max_files=6)
        evidence = _compact_lines(
            [
                f"Ship status: {payload.get('status', 'unknown')}",
                f"Blocker: {blocker}",
                str(payload.get("summary", "")).strip(),
            ]
        )
        prompts.append(
            _build_prompt_payload(
                title=f"Unblock ship gate: {blocker}",
                category="ship",
                objective=f"Remove the ship blocker: {blocker}",
                files_to_open=files,
                evidence=evidence,
                tasks=[
                    "Identify the concrete root cause behind this blocker.",
                    "Apply the smallest patch that resolves the blocker safely.",
                    "Document any follow-up work if full remediation needs more than one patch.",
                ],
                acceptance_checks=[
                    "The related ship check should move from fail/warn to pass where feasible.",
                    "Run `python -m pytest -q` and ensure no regressions.",
                    "Keep behavior stable outside the targeted scope.",
                ],
                risk_notes=["Ship-gate fixes often touch release-critical surfaces; validate side effects carefully."],
                style=style,
            )
        )
        if len(prompts) >= max_prompts:
            return prompts

    for check in checks:
        status = str(check.get("status", "")).strip().lower()
        if status not in {"fail", "warn"}:
            continue
        name = str(check.get("name", "check")).strip() or "check"
        summary = str(check.get("summary", "")).strip()
        detail = str(check.get("detail", "")).strip()
        prompts.append(
            _build_prompt_payload(
                title=f"Stabilize readiness check: {name}",
                category="ship",
                objective=summary or f"Improve check `{name}` from `{status}` to a stable pass.",
                files_to_open=_best_review_files(review_findings, max_files=6),
                evidence=_compact_lines([f"Check status: {status}", summary, detail]),
                tasks=[
                    "Trace the failing/warning check back to concrete code or config causes.",
                    "Patch the smallest set of files required to improve readiness.",
                    "Add missing guardrails or tests if the check reveals weak coverage.",
                ],
                acceptance_checks=[
                    f"Check `{name}` should no longer report `{status}` after the patch.",
                    "Run local verification commands and report outcomes.",
                ],
                risk_notes=["Do not mask readiness warnings without fixing the underlying issue."],
                style=style,
            )
        )
        if len(prompts) >= max_prompts:
            return prompts

    return prompts


def _prompts_from_patch_review(payload: dict[str, Any], *, style: str, max_prompts: int) -> list[dict[str, Any]]:
    changed_files = [item for item in payload.get("changed_files", []) if isinstance(item, dict)]
    suggested_tests = [item for item in payload.get("suggested_tests", []) if isinstance(item, dict)]
    config_surfaces = [item for item in payload.get("config_surfaces", []) if isinstance(item, dict)]
    warnings = _string_list(payload.get("warnings", []))

    prompts: list[dict[str, Any]] = []
    files = _string_list(item.get("file_path", "") for item in changed_files)[:10]
    prompts.append(
        _build_prompt_payload(
            title="Reduce patch risk on changed files",
            category="patch-review",
            objective=str(payload.get("summary", "")).strip() or "Lower risk and improve confidence for the current patch.",
            files_to_open=files,
            evidence=_compact_lines(
                [
                    f"Patch mode: {payload.get('mode', 'unknown')}",
                    f"Risk label: {payload.get('risk_label', 'unknown')} (score={payload.get('risk_score', 'n/a')})",
                    *warnings[:4],
                ]
            ),
            tasks=[
                "Inspect changed files for incomplete logic, edge cases, and unsafe assumptions.",
                "Patch only the areas directly tied to the reported risk.",
                "Add guards or validations where failure impact is high.",
            ],
            acceptance_checks=[
                "Patch-review warnings tied to changed files should be reduced or resolved.",
                "No unrelated behavior changes outside the modified scope.",
            ],
            risk_notes=[
                "Avoid broad refactors during patch hardening.",
                "Keep compatibility with existing call sites and config shape.",
            ],
            style=style,
        )
    )
    if len(prompts) >= max_prompts:
        return prompts[:max_prompts]

    if suggested_tests:
        test_files = _string_list(item.get("file_path", "") for item in suggested_tests)[:8]
        prompts.append(
            _build_prompt_payload(
                title="Close regression test gaps for this patch",
                category="patch-review",
                objective="Add or update regression tests that validate the changed behavior.",
                files_to_open=test_files or files,
                evidence=_compact_lines(
                    [
                        "Patch review suggested tests for this change set.",
                        *[str(item.get("file_path", "")).strip() for item in suggested_tests[:4]],
                    ]
                ),
                tasks=[
                    "Implement focused tests that cover success and failure paths introduced by the patch.",
                    "Keep tests deterministic and aligned with current runtime behavior.",
                ],
                acceptance_checks=[
                    "New tests fail before fix and pass after fix when applicable.",
                    "Existing test suite remains green.",
                ],
                risk_notes=["Do not weaken assertions just to make tests pass."],
                style=style,
            )
        )
        if len(prompts) >= max_prompts:
            return prompts[:max_prompts]

    if config_surfaces:
        config_files = _string_list(item.get("file_path", "") for item in config_surfaces)[:8]
        prompts.append(
            _build_prompt_payload(
                title="Validate config touchpoints for the patch",
                category="patch-review",
                objective="Confirm configuration and environment surfaces remain correct after this patch.",
                files_to_open=config_files,
                evidence=_compact_lines(
                    [
                        "Patch review detected configuration-sensitive files.",
                        *[str(item.get("file_path", "")).strip() for item in config_surfaces[:4]],
                    ]
                ),
                tasks=[
                    "Verify defaults, env bindings, and parsing logic used by the patch.",
                    "Prevent silent misconfiguration through explicit validation.",
                ],
                acceptance_checks=[
                    "Configuration-dependent paths still work with current defaults.",
                    "Error paths are explicit and actionable.",
                ],
                risk_notes=["Configuration regressions can be silent; validate startup and runtime paths."],
                style=style,
            )
        )
    return prompts[:max_prompts]


def _prompts_from_import(payload: dict[str, Any], *, style: str, max_prompts: int) -> list[dict[str, Any]]:
    top_findings = [item for item in payload.get("top_findings", []) if isinstance(item, dict)]
    prompts: list[dict[str, Any]] = []
    for finding in top_findings[:max_prompts]:
        severity = str(finding.get("severity", "medium")).lower()
        category = str(finding.get("category", "quality")).strip() or "quality"
        title = str(finding.get("title", "Import assessment finding")).strip() or "Import assessment finding"
        files = _string_list(finding.get("file_paths", []))[:8]
        prompts.append(
            _build_prompt_payload(
                title=f"Import hardening: {title}",
                category=category,
                objective=f"Resolve high-impact import finding ({severity}) to improve project readiness.",
                files_to_open=files,
                evidence=_compact_lines(
                    [
                        f"Import readiness: {payload.get('readiness', 'unknown')} ({payload.get('score', 'n/a')}/10)",
                        f"Finding severity: {severity}",
                        f"Finding title: {title}",
                    ]
                ),
                tasks=_category_tasks(category, title),
                acceptance_checks=_acceptance_checks_for_category(category),
                risk_notes=["Prioritize safe, incremental hardening and verify behavior before broad changes."],
                style=style,
            )
        )

    if prompts:
        return prompts[:max_prompts]

    next_steps = _string_list(payload.get("next_steps", []))
    index_stats = payload.get("index", {})
    if not isinstance(index_stats, dict):
        index_stats = {}
    prompts.append(
        _build_prompt_payload(
            title="Import onboarding: stabilize baseline quality",
            category="import",
            objective="Improve initial readiness after import and indexing.",
            files_to_open=[],
            evidence=_compact_lines(
                [
                    f"Readiness: {payload.get('readiness', 'unknown')}",
                    f"Indexed files: {index_stats.get('files', 0)}",
                    f"Indexed chunks: {index_stats.get('chunks', 0)}",
                    *next_steps[:3],
                ]
            ),
            tasks=[
                "Use the import summary to identify one high-impact quality or security gap.",
                "Apply the minimum safe patch to improve readiness score.",
                "Record any follow-up work that should be tracked separately.",
            ],
            acceptance_checks=[
                "Project readiness should improve or risk concentration should decrease.",
                "No new warnings introduced in unrelated modules.",
            ],
            risk_notes=["Do not overfit to score alone; keep runtime behavior and safety first."],
            style=style,
        )
    )
    return prompts[:max_prompts]


def _build_prompt_payload(
    *,
    title: str,
    category: str,
    objective: str,
    files_to_open: list[str],
    evidence: list[str],
    tasks: list[str],
    acceptance_checks: list[str],
    risk_notes: list[str],
    style: str,
) -> dict[str, Any]:
    return {
        "title": title,
        "category": category,
        "objective": objective,
        "files_to_open": _ordered_unique(files_to_open)[:10],
        "evidence": evidence[:8],
        "tasks": tasks[:6],
        "acceptance_checks": acceptance_checks[:6],
        "risk_notes": risk_notes[:6],
        "prompt_text": _render_prompt_text(
            title=title,
            objective=objective,
            files_to_open=files_to_open,
            evidence=evidence,
            tasks=tasks,
            acceptance_checks=acceptance_checks,
            risk_notes=risk_notes,
            style=style,
        ),
    }


def _render_prompt_text(
    *,
    title: str,
    objective: str,
    files_to_open: list[str],
    evidence: list[str],
    tasks: list[str],
    acceptance_checks: list[str],
    risk_notes: list[str],
    style: str,
) -> str:
    lines = [
        _STYLE_INTRO[style],
        "",
        f"Task title: {title}",
        f"Objective: {objective}",
        "",
        "Evidence context:",
    ]
    if evidence:
        lines.extend(f"- {item}" for item in evidence)
    else:
        lines.append("- No additional evidence lines were provided.")

    lines.extend(["", "Scope files (prioritize these first):"])
    if files_to_open:
        lines.extend(f"- {item}" for item in _ordered_unique(files_to_open)[:10])
    else:
        lines.append("- Determine concrete file targets from the nearest related module.")

    lines.extend(["", "Implementation tasks:"])
    lines.extend(f"- {item}" for item in tasks[:6])

    lines.extend(["", "Done criteria:"])
    lines.extend(f"- {item}" for item in acceptance_checks[:6])

    lines.extend(["", "Risk guardrails:"])
    lines.extend(f"- {item}" for item in risk_notes[:6])
    lines.extend(
        [
            "- Keep edits minimal and avoid unrelated refactors.",
            "- Preserve backward-compatible behavior unless explicitly fixing a breaking bug.",
        ]
    )

    lines.extend(["", "Output contract:"])
    lines.extend(f"- {item}" for item in _STYLE_OUTPUT_CONTRACT[style])
    return "\n".join(lines).strip()


def _acceptance_checks_for_category(category: str) -> list[str]:
    lowered = category.lower()
    if "security" in lowered:
        return [
            "Security-sensitive paths are validated explicitly and reject unsafe input.",
            "Secrets, credentials, and tokens are not exposed in logs or responses.",
            "Run `python -m pytest -q` and ensure security-relevant tests pass.",
        ]
    if "production" in lowered:
        return [
            "Error handling and fallback behavior are explicit for failure paths.",
            "Operational checks (`doctor`/`ship`) should improve for this issue.",
            "Run `python -m pytest -q` and confirm no runtime regressions.",
        ]
    return [
        "The finding is resolved with focused code changes.",
        "Add or update tests where behavior changed.",
        "Run `python -m pytest -q` and ensure green results.",
    ]


def _category_tasks(category: str, title: str) -> list[str]:
    lowered = category.lower()
    if "security" in lowered:
        return [
            f"Trace the trust boundary related to `{title}` and locate unsafe assumptions.",
            "Add strict validation/sanitization at the earliest boundary.",
            "Harden sensitive branches and error paths without widening scope.",
        ]
    if "production" in lowered:
        return [
            f"Locate runtime-critical code paths connected to `{title}`.",
            "Improve resilience: retries, timeouts, fallback, or explicit failure handling.",
            "Add observability or clearer failure messages where practical.",
        ]
    return [
        f"Confirm the root cause behind `{title}` using the cited files.",
        "Apply a focused patch that removes the issue without broad refactors.",
        "Update tests/docs only where directly needed to support the fix.",
    ]


def _best_review_files(findings: list[dict[str, Any]], *, max_files: int) -> list[str]:
    paths: list[str] = []
    for finding in findings:
        paths.extend(_string_list(finding.get("file_paths", [])))
        if len(paths) >= max_files:
            break
    return _ordered_unique(paths)[:max_files]


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _string_list(values: Any) -> list[str]:
    if isinstance(values, str):
        cleaned = values.strip()
        return [cleaned] if cleaned else []
    if not isinstance(values, Iterable):
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def _compact_lines(values: Iterable[str]) -> list[str]:
    return [item.strip() for item in values if str(item).strip()]

