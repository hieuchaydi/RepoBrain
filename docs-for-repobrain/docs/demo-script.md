# Demo Script

## Goal

Show that RepoBrain improves agent context gathering before code generation.

## Demo Flow

1. Run `repobrain demo-clean --format text` on the RepoBrain repo if you want to remove old test/build clutter before showing the product.
2. Open a sample repo and run `repobrain first-look --format text`.
3. Show the first-look summary: indexed files, parser counts, review snapshot, starter questions, and top files.
4. Open `.repobrain/report.html` and show the local dashboard: status, files, chunks, symbols, parser choices, and local-only security posture.
5. Run `repobrain serve-web --open`.
6. In the web UI, click `Choose folder` to show native local folder selection, or paste a path for Docker/headless runs.
7. Click `Import + Index`.
8. Run `repobrain chat` or double-click `chat.cmd` on Windows.
9. Ask: `Where is payment retry logic implemented?`
10. Show the returned files, snippets, and dependency edges.
11. Ask: `/trace Trace login with Google from route to service`
12. Highlight route -> service -> helper evidence.
13. Ask: `/targets Which files should I edit to add GitHub login?`
14. Show edit targets and warnings.
15. Run `repobrain benchmark`.

## Talking Points

- hybrid retrieval beats embedding-only search on small code fixtures
- edit targets are ranked explicitly
- confidence is surfaced, not hidden
- the tool stays local-first and works without a hosted backend
- the strongest public demo does not need a VPS or provider key

## Good Visuals

- terminal recording of `index`, `query`, and `targets`
- browser capture of `.repobrain/report.html`
- short clip of the local chat loop
- side-by-side comparison with a naive grep or chat-only answer
- highlight citations and dependency edges in both text output and the JSON response

## Accessibility Notes

- Prefer `--format text` during live demos so non-agent users can follow the output.
- Keep JSON examples for automation sections, MCP contracts, and agent integrations.
- Use `report.cmd` and `chat.cmd` on Windows when demoing to people who are less comfortable with terminals.
