# Demo Script

## Goal

Show that RepoBrain improves agent context gathering before code generation.

## Demo Flow

1. Run `repobrain demo-clean --format text` on the RepoBrain repo if you want to remove old test/build clutter before showing the product.
2. Open a sample repo and run `repobrain quickstart`.
3. Run `repobrain init --repo /path/to/sample --format text`.
4. Run `repobrain index --format text` without repeating `--repo`.
5. Show parser usage counts from the readable index output.
6. Run `repobrain report --format text` or double-click `report.cmd` on Windows.
7. Open `.repobrain/report.html` and show the local dashboard: status, files, chunks, symbols, parser choices, and local-only security posture.
8. Run `repobrain serve-web --open` and show the one-step browser import form.
9. Run `repobrain chat` or double-click `chat.cmd` on Windows.
10. Ask: `Where is payment retry logic implemented?`
11. Show the returned files, snippets, and dependency edges.
12. Ask: `/trace Trace login with Google from route to service`
13. Highlight route -> service -> helper evidence.
14. Ask: `/targets Which files should I edit to add GitHub login?`
15. Show edit targets and warnings.
16. Run `repobrain benchmark`.

## Talking Points

- hybrid retrieval beats embedding-only search on small code fixtures
- edit targets are ranked explicitly
- confidence is surfaced, not hidden
- the tool stays local-first and works without a hosted backend

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
