# RepoBrain Agent Skill

## Overview

This package teaches Skill-capable coding agents how to orchestrate RepoBrain's existing repository-analysis tools. It does not bundle, fork, or replace RepoBrain. RepoBrain remains the runtime that indexes code and produces grounded evidence.

The package was authored against RepoBrain `0.5.0` at source commit `2b43d9d`. The verified runtime exposes a local newline-delimited JSON transport described by the project as "MCP-style". It is not an implementation of the standard MCP JSON-RPC lifecycle in this revision; see [MCP configuration](#mcp-configuration).

The Skill layout and frontmatter follow the official Agent Skills specification. `name: repobrain` exactly matches the parent directory, the activation description is within the official limit, and detailed material is loaded progressively from `references/` only when needed.

## Features

- Repository indexing and grounded code discovery
- Execution-flow and dependency-edge tracing
- Change-impact and edit-target analysis
- Working-tree, base-ref, or explicit-file patch review
- Production, security, and quality review
- Pre-merge readiness assessment
- Multi-repository workspace search and persisted repository notes
- Conservative confidence handling and merge-safety reporting

### Public versus early-access features

This package documents only tools registered by the public `src/repobrain/mcp_server.py` at the audited commit. The root RepoBrain README separately advertises private v1.3 early-access names including `repobrain_search`, `repobrain_blast`, `repobrain_ship`, `repobrain_gate`, and `repobrain_status`. Those names are not registered by the public server implementation and are therefore not callable through this Skill. Similar public capabilities use the verified names documented in [references/mcp-tools.md](references/mcp-tools.md).

## Prerequisites

- Python 3.12 or newer
- Git for working-tree and base-ref patch review
- A local checkout of RepoBrain or an installed `repobrain` package
- A repository the user is authorized to inspect
- An agent integration or bridge capable of speaking RepoBrain's current line-oriented stdio JSON protocol

The core local provider has no required Python dependencies beyond RepoBrain itself. Tree-sitter parsers, development tools, remote providers, and the declared `mcp` extra are optional. The `mcp` extra does not convert the current server into standard MCP by itself because `src/repobrain/mcp_server.py` does not import or use that SDK.

## RepoBrain installation

For local development from the RepoBrain checkout:

```bash
python -m venv .venv
```

Activate the environment, then install:

```bash
python -m pip install -e .
```

For deeper Python, TypeScript, and JavaScript parsing:

```bash
python -m pip install -e ".[tree-sitter]"
```

Remote provider support is opt-in:

```bash
python -m pip install -e ".[providers]"
```

Keep providers local unless the user explicitly accepts remote code processing.

## Repository indexing setup

Initialize and index a target project from any directory:

```bash
repobrain init --repo "/absolute/path/to/project" --format text
repobrain index --repo "/absolute/path/to/project" --format text
repobrain doctor --repo "/absolute/path/to/project" --format text
```

Initialization creates `repobrain.toml` and local state under `.repobrain/`. The index normally contains `metadata.db`, vector data, and cache files. Do not package or commit those files.

`serve-mcp --repo` accepts an explicit target path. Without it, RepoBrain can select a previously saved active repository from the file named by `REPOBRAIN_ACTIVE_REPO_FILE` or, by default, the user's `~/.repobrain/active_repo.txt`; otherwise it falls back to the current directory. Prefer an explicit absolute path in integrations.

## MCP configuration

See [mcp-config.example.json](mcp-config.example.json) for the two verified launch forms:

- installed command: `repobrain serve-mcp --repo <ABSOLUTE_REPOSITORY_PATH>`
- source checkout: `python -m repobrain serve-mcp --repo <ABSOLUTE_REPOSITORY_PATH>` with `PYTHONPATH` pointing to `src`

The server writes a banner followed by one JSON object per line. It accepts:

```json
{"method":"tools/list"}
{"method":"tools/call","name":"search_codebase","arguments":{"query":"Where is authentication implemented?"}}
```

Claude Code, Cursor, Codex, and most MCP clients expect standard MCP JSON-RPC initialization and standard tool schemas. The current RepoBrain transport does not implement those protocol messages, so pasting the launcher into a standard `mcpServers` block is not verified and is expected to require a compatible bridge. Configuration-file locations also vary by agent and version. This package deliberately avoids presenting an untested agent-specific block as working configuration.

Manual compatibility test for any bridge:

1. Start the configured process with an explicit repository path.
2. Confirm the first stdout line reports `"transport":"stdio-json"`.
3. Send `{"method":"tools/list"}` followed by a newline.
4. Confirm all 14 documented tools are returned.
5. Send a representative `tools/call` and confirm the bridge maps the response to the agent's tool-result format.
6. Confirm stderr notices are not mixed into protocol stdout.

## Agent Skill installation

Install the `repobrain/` folder, not only `SKILL.md`, in the skills directory supported by the target agent. Preserve the `references/` and `examples/` paths.

For Agensi, upload the distribution ZIP. Its single top-level folder is `repobrain/`, and `SKILL.md` is directly inside that folder.

Agent-specific discovery paths and MCP settings change over time. Follow the current official instructions for the installed agent, and test activation instead of assuming support from the presence of a `SKILL.md` file.

## Usage examples

Example prompts:

```text
Where is OAuth callback handling implemented, and what calls it?
```

```text
What could break if we change the payment retry scheduler?
```

```text
Review my current patch and identify missing tests or configuration checks.
```

```text
Assess whether this branch is ready to merge. Separate verified checks from remaining uncertainty.
```

See [examples/usage-examples.md](examples/usage-examples.md) for expected orchestration behavior.

## Troubleshooting

Use [references/troubleshooting.md](references/troubleshooting.md) for index, startup, Git, provider, and protocol failures. The most common recovery is to verify the selected repository and run `repobrain index --repo <path>`.

## Security considerations

- The local index stores source-derived metadata and snippets under `.repobrain/`; protect it like the source repository.
- Remote embedding or reranking providers can receive code-derived text. They are disabled by default and require explicit configuration and credentials.
- `.env` is loaded from the target repository. Do not display or distribute it.
- Workspace tracking and notes persist state outside ordinary read-only analysis.
- `review_patch` executes local Git commands for working-tree and base-ref modes.
- Never expose the stdio process directly to a network endpoint.

## Version compatibility

Verified from source:

- RepoBrain package version: `0.5.0`
- Python: `>=3.12`
- Transport: local newline-delimited `stdio-json`
- Tool count: 14
- Skill frontmatter: portable core fields `name` and `description`
- Agensi ZIP rule: one top-level `repobrain/` folder
- Official Agent Skills validation: `skills-ref 0.1.0`
- Codex CLI Skill discovery and explicit activation: tested with `codex-cli 0.144.1`

Not integration-tested in this environment:

- Claude Code
- Cursor
- Codex CLI MCP client configuration for RepoBrain's nonstandard transport
- Any third-party standard-MCP bridge

Codex Skill activation does not prove MCP connectivity. The activation layer and RepoBrain server transport were tested separately; end-to-end Codex-to-RepoBrain MCP configuration remains blocked by the protocol mismatch described above.

Re-audit `src/repobrain/mcp_server.py` whenever RepoBrain changes, especially if it adopts the official MCP SDK or adds, removes, or changes tools.
