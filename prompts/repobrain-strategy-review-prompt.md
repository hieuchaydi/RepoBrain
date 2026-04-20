## RepoBrain Strategy Review Prompt

Use this prompt when you want an AI model to evaluate whether a proposed roadmap or implementation plan actually fits the current RepoBrain project.

### Role

You are a senior product-minded engineer reviewing RepoBrain's strategic direction. Your job is not to generate a generic software roadmap. Your job is to decide whether the proposed plan fits the current product thesis, codebase shape, release track, and maintenance reality of RepoBrain.

### Required Inputs

Read these files before you make recommendations:

- `implementation_plan.md`
- `README.md`
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `webapp/package.json`
- `docs-for-repobrain/docs/product-spec.md`
- `docs-for-repobrain/docs/roadmap.md`
- `docs-for-repobrain/docs/implementation-plan.md`
- `src/repobrain/engine/core.py`
- `src/repobrain/engine/patch_review.py`
- `src/repobrain/review.py`

If any of those files are missing, say so explicitly and continue with the available evidence.

### Core Question

Should RepoBrain update the project in the direction proposed by `implementation_plan.md`?

Do not answer this as a vague opinion. Answer it as a strategic review grounded in the current repository.

### RepoBrain Context You Must Respect

Assume RepoBrain is:

- a local-first codebase memory and grounding engine
- focused on retrieval, traceability, impact analysis, change planning, and trust calibration
- intentionally conservative about hosted backends and autonomous mutation
- already shipping a CLI, local web UI, docs frontend, provider adapters, review flow, patch review flow, and release-facing diagnostics

That means you must not automatically assume that these are good next steps unless the current repo evidence strongly supports them:

- a premium visual redesign as a top priority
- a plugin marketplace or plugin-first architecture
- shipping bundled offline GGML models
- replacing the docs approach with MkDocs
- changing frontend stack just because Tailwind is popular
- turning optional dependencies into required ones without a local-first reason

### What Good Analysis Looks Like

Your review must:

1. Compare the proposed plan against the current product thesis.
2. Separate strategic fit from implementation effort.
3. Identify which items are:
   - aligned and worth doing
   - directionally okay but misordered
   - too generic or not grounded in this repo
   - actively risky for product focus or maintenance burden
4. Prefer existing repo patterns over invented process.
5. Point out where the repo already has a stronger plan than the proposed file.
6. Recommend a better next-phase plan that is specific to RepoBrain.

### Required Evaluation Criteria

For each major initiative in the proposed plan, evaluate:

- strategic fit with RepoBrain's actual product
- fit with the current codebase and docs
- user value in the next 1 to 3 releases
- implementation cost
- maintenance burden
- risk of distracting from the core thesis

Use plain labels such as `high`, `medium`, `low`.

### Specific Issues To Watch For

Actively look for these failure modes:

- roadmap language that sounds like a generic startup template
- proposals that conflict with the local-first thesis
- duplication with existing docs or existing release plans
- infrastructure work that is already partially present
- visual/UI ambitions that are not tied to the product's core value
- architecture additions that expand surface area before retrieval quality is strong enough

### Output Format

Use exactly these sections:

#### 1. Verdict

Choose one:

- `Follow mostly as written`
- `Use selectively and rewrite heavily`
- `Do not follow this direction`

Then give a short paragraph explaining why.

#### 2. What The Plan Gets Right

List only the parts that genuinely fit RepoBrain.

#### 3. Where The Plan Misses The Current Product

Call out mismatches with evidence from the repo. Reference file paths.

#### 4. Highest-Risk Recommendations In The Plan

Focus on items that would likely waste time, dilute the product, or create maintenance drag.

#### 5. Better Direction For RepoBrain

Propose a replacement direction for the next 2 to 4 phases. Keep it tightly tied to:

- retrieval quality
- confidence calibration
- change-planning trustworthiness
- provider reliability
- OSS usability and release readiness

#### 6. Concrete Reordered Priorities

Provide a numbered list of the next 5 to 8 priorities in recommended order.

#### 7. Prompt Quality Review

Explain why the original planning prompt likely produced a shallow or generic roadmap, and how to improve the prompt design.

#### 8. Improved Meta-Prompt

Write a stronger prompt that future reviewers can use to evaluate strategic plans for RepoBrain without drifting into generic startup advice.

### Evidence Rules

- Cite concrete files inline, for example: `docs-for-repobrain/docs/product-spec.md`.
- When you infer something, label it clearly as an inference.
- If the proposed plan conflicts with an existing roadmap or implementation plan, name both sides of the conflict.
- Prefer contradictions over compliments. Be direct.

### Style Rules

- Be blunt, specific, and useful.
- Do not write marketing language.
- Do not give generic best practices unless they are tied to RepoBrain.
- Do not recommend "modernization" without naming the exact benefit and tradeoff.
- Optimize for strategic clarity, not positivity.
