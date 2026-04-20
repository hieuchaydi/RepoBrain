# GitHub Growth Content Kit

This file contains ready-to-post drafts to drive RepoBrain discovery and stars.

## Posting Plan (2 Weeks)

1. Day 1: Problem framing + one-command demo.
2. Day 3: Before/after workflow with grounded citations.
3. Day 5: Demo GIF + local-first angle.
4. Day 8: Patch-review safety loop.
5. Day 10: Browser UI + MCP integration.
6. Day 13: Benchmark snapshot + call for contributor feedback.

## Post 1: One Command Start

- Hook: "Most AI coding failures are context failures, not generation failures."
- Body:
  - I built `RepoBrain` to fix the pre-generation step.
  - Run one command and get grounded files + flow hints + edit targets:
  - `repobrain first-look --repo /path/to/repo --format text`
  - Works locally without hosted backend or API key.
- CTA: "If this helps your agent workflow, star the repo and tell me your first query."
- Asset: `assets/repobrain-demo.gif`
- Channels: X, LinkedIn, Reddit (`r/programming`, `r/LocalLLaMA`)

## Post 2: Before vs After

- Hook: "Before RepoBrain: grep + guess. After RepoBrain: evidence + ranked targets."
- Body:
  - Before: spend 15-30 minutes finding route/service/job ownership.
  - After: ask `/trace` and `/targets` to get high-signal files fast.
  - Example prompts:
  - `/trace Trace login with Google from route to service`
  - `/targets Which files should I edit to add GitHub login?`
- CTA: "Drop your hardest codebase question; I will run it in RepoBrain."
- Asset: terminal screenshot + cited output snippet.
- Channels: X thread, Dev.to short post

## Post 3: Local-First Trust

- Hook: "You should not need to upload your repo to get useful codebase intelligence."
- Body:
  - RepoBrain defaults to local mode.
  - Remote providers are opt-in.
  - Good fit for teams that care about privacy and explicit evidence.
- CTA: "If local-first matters to you, star and share your security constraints."
- Asset: README "Start Here" section screenshot.
- Channels: LinkedIn, Hacker News "Show HN" follow-up comment

## Post 4: Safer Pre-Merge Loop

- Hook: "My current pre-merge loop is 3 commands."
- Body:
  - `repobrain review --format text`
  - `repobrain ship --format text`
  - `repobrain patch-review --format text`
  - This catches weak evidence and risky surfaces before editing.
- CTA: "Want the same loop for your stack? Star the repo and open an issue with your language/framework."
- Asset: short terminal clip.
- Channels: X, LinkedIn

## Post 5: CLI + Browser + MCP

- Hook: "RepoBrain is not just a CLI. It is a local workbench."
- Body:
  - Use CLI for fast queries.
  - Use `serve-web` for visual diagnostics.
  - Use `serve-mcp` to plug into Cursor/Codex/Claude Code workflows.
- CTA: "If you want an integration guide for your tool, comment the tool name."
- Asset: split image (terminal + web UI).
- Channels: X thread, GitHub Discussions

## Post 6: Benchmark Snapshot + Ask

- Hook: "Publishing local benchmark snapshots so claims are reproducible."
- Body:
  - Latest local snapshot (2026-04-20) is in README.
  - Includes files/chunks/symbols/edges, runtime, and confidence.
  - Repro command and env vars included.
- CTA: "Run the same command on your repo and post your results. Best results will be added to community benchmarks."
- Asset: README benchmark table crop.
- Channels: X, Reddit, Discord communities

## Reusable CTA Variants

- "Star the repo if you want grounded answers instead of confident guesses."
- "Open an issue with one painful query and I will add it to the benchmark set."
- "If this saves you context-switching time, share it with one teammate."

