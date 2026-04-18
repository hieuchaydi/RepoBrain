import architectureDoc from '../../docs/architecture.md?raw'
import cliDoc from '../../docs/cli.md?raw'
import demoScriptDoc from '../../docs/demo-script.md?raw'
import evaluationDoc from '../../docs/evaluation.md?raw'
import installDoc from '../../docs/install.md?raw'
import mcpDoc from '../../docs/mcp.md?raw'
import productionReadinessDoc from '../../docs/production-readiness.md?raw'
import releaseChecklistDoc from '../../docs/release-checklist.md?raw'
import runDoc from '../../docs/run.md?raw'
import uxDoc from '../../docs/ux.md?raw'
import visionDoc from '../../docs/vision.md?raw'
import roadmapDoc from '../../ROADMAP.md?raw'

export type DocEntry = {
  id: string
  title: string
  eyebrow: string
  path: string
  summary: string
  audience: string
  tags: string[]
  content: string
}

export type CommandEntry = {
  category: string
  command: string
  summary: string
  result: string
}

export type SurfaceEntry = {
  title: string
  description: string
  detail: string
}

export type RepoMapEntry = {
  path: string
  summary: string
}

export type StatusEntry = {
  label: string
  state: 'pass' | 'pending' | 'info'
  detail: string
}

export type FaqEntry = {
  question: string
  answer: string
}

export const navigationSections = [
  { id: 'overview', label: 'Overview' },
  { id: 'surfaces', label: 'Product Surfaces' },
  { id: 'quickstart', label: 'Quickstart' },
  { id: 'commands', label: 'Command Catalog' },
  { id: 'repo-map', label: 'Repo Map' },
  { id: 'docs-library', label: 'Docs Library' },
  { id: 'reader', label: 'Reading Room' },
  { id: 'release-state', label: 'Release State' },
  { id: 'faq', label: 'FAQ' },
] as const

export const heroMetrics = [
  { value: 'CLI + Web + MCP', label: 'Ways to use RepoBrain' },
  { value: 'Local-first', label: 'Default security posture' },
  { value: '0.5.x track', label: 'Current integration line' },
  { value: 'Docs reader', label: 'Built for onboarding humans fast' },
]

export const surfaces: SurfaceEntry[] = [
  {
    title: 'Grounded CLI',
    description: 'Start with `init`, `review`, `index`, and `query` to answer codebase questions with evidence.',
    detail: 'The CLI is still the fastest path for engineers who want concrete file paths, snippets, edit targets, and ship checks.',
  },
  {
    title: 'Browser UI',
    description: 'Use `repobrain serve-web --open` when you want a friendly local interface for import, review, doctor, and provider smoke.',
    detail: 'The React UI is local-only and already ships inside the main RepoBrain package through `webapp/dist`.',
  },
  {
    title: 'Release Safety',
    description: 'Use `release-check`, `python -m build`, and `demo-clean` to keep packaging and demo flows predictable.',
    detail: 'This track now validates built artifacts, frontend packaging, and safe cleanup of test/build clutter before a live session.',
  },
  {
    title: 'Agent Transport',
    description: 'Use `serve-mcp` to expose RepoBrain tools to coding assistants that speak MCP-style stdio transports.',
    detail: 'RepoBrain exists to improve context gathering before code generation, especially for multi-file or flow-tracing tasks.',
  },
]

export const quickstartSteps = [
  {
    title: 'Install the dev stack',
    body: 'Create a virtual environment, install the editable package, then keep everything local by default.',
    command: 'python -m pip install -e ".[dev,tree-sitter,mcp]"',
  },
  {
    title: 'Initialize one repo once',
    body: 'Run `repobrain init --repo <path>` and let RepoBrain remember the active project for later commands.',
    command: 'repobrain init --repo "C:\\path\\to\\your-project" --format text',
  },
  {
    title: 'Scan, then index',
    body: 'Use `review` to understand the repo quickly, then build the local memory index for grounded retrieval.',
    command: 'repobrain review --format text\nrepobrain index --format text',
  },
  {
    title: 'Ask operational questions',
    body: 'Use `query`, `trace`, and `targets` when you need evidence for where logic lives and what is safest to touch next.',
    command: 'repobrain query "Where is payment retry logic implemented?" --format text',
  },
  {
    title: 'Close with ship and release gates',
    body: 'Use `ship`, `release-check`, and `demo-clean` when you are moving from development toward demo or release.',
    command: 'repobrain ship --format text\nrepobrain release-check --require-dist --format text\nrepobrain demo-clean --format text',
  },
]

export const commandCatalog: CommandEntry[] = [
  {
    category: 'Setup',
    command: 'repobrain init --repo "<path>" --format text',
    summary: 'Create local RepoBrain state and remember the active project.',
    result: 'Generates `.repobrain/`, `repobrain.toml`, and an active-repo pointer.',
  },
  {
    category: 'Exploration',
    command: 'repobrain review --format text',
    summary: 'Get the fastest risk-oriented scan of a repo before indexing.',
    result: 'Shows security, production, and code-quality findings in plain English.',
  },
  {
    category: 'Exploration',
    command: 'repobrain index --format text',
    summary: 'Build the local metadata and vector index used by retrieval flows.',
    result: 'Reports files, chunks, symbols, edges, and parser usage stats.',
  },
  {
    category: 'Retrieval',
    command: 'repobrain query "<question>" --format text',
    summary: 'Answer locate-style questions with top files, snippets, and confidence.',
    result: 'Returns grounded retrieval evidence instead of a vague repo summary.',
  },
  {
    category: 'Retrieval',
    command: 'repobrain trace "<question>" --format text',
    summary: 'Bias the engine toward route-to-service or job-to-handler flows.',
    result: 'Highlights likely call chains and dependency edges.',
  },
  {
    category: 'Retrieval',
    command: 'repobrain targets "<question>" --format text',
    summary: 'Rank the safest files to inspect or edit next for a requested change.',
    result: 'Returns edit targets with explicit rationale.',
  },
  {
    category: 'Operations',
    command: 'repobrain doctor --format text',
    summary: 'Inspect provider readiness, parser posture, and index health.',
    result: 'Confirms whether the current local configuration is actually usable.',
  },
  {
    category: 'Operations',
    command: 'repobrain provider-smoke --format text',
    summary: 'Run a direct embedding/reranker smoke check through configured providers.',
    result: 'Validates the real provider path before you trust it in production flows.',
  },
  {
    category: 'Operations',
    command: 'repobrain ship --format text',
    summary: 'Run a higher-level production-readiness gate across review, benchmark, and health signals.',
    result: 'Summarizes whether the project is blocked, cautionary, or ready.',
  },
  {
    category: 'Docs',
    command: 'repobrain report --open',
    summary: 'Generate and open the local HTML report/dashboard.',
    result: 'Good for demos, screenshots, and non-terminal teammates.',
  },
  {
    category: 'Web',
    command: 'repobrain serve-web --open',
    summary: 'Start the browser UI for import, review, question-answering, and diagnostics.',
    result: 'Serves the built React frontend from `webapp/dist`.',
  },
  {
    category: 'Release',
    command: 'python -m build',
    summary: 'Build the wheel and sdist artifacts that the release workflow expects.',
    result: 'Creates `dist/*.whl` and `dist/*.tar.gz` for artifact validation.',
  },
  {
    category: 'Release',
    command: 'repobrain release-check --require-dist --format text',
    summary: 'Validate version alignment and built artifact contents before publishing.',
    result: 'Confirms the wheel and sdist include the React frontend assets.',
  },
  {
    category: 'Demo',
    command: 'repobrain demo-clean --format text',
    summary: 'Remove temporary build/test clutter without breaking the browser demo.',
    result: 'Preserves `webapp/dist` and the root `.repobrain` workspace state by default.',
  },
]

export const repoMap: RepoMapEntry[] = [
  {
    path: 'src/repobrain',
    summary: 'Python package with the engine, CLI, review flow, provider adapters, release checks, and web server.',
  },
  {
    path: 'webapp',
    summary: 'React frontend for the local RepoBrain browser UI that ships inside the package as built assets.',
  },
  {
    path: 'docs',
    summary: 'Primary markdown documentation set covering install, run, CLI, architecture, release, evaluation, and product direction.',
  },
  {
    path: 'tests',
    summary: 'Pytest suite for CLI, providers, release validation, review flows, and web routes.',
  },
  {
    path: '.github/workflows',
    summary: 'Automation for CI and release flows, including strict release artifact validation.',
  },
  {
    path: 'docs-for-repobrain',
    summary: 'This documentation frontend, built to make RepoBrain easier to read and onboard without opening every markdown file manually.',
  },
]

export const releaseStatus: StatusEntry[] = [
  {
    label: 'Local packaging fixes',
    state: 'pass',
    detail: 'Wheel packaging now includes `webapp/dist`, and invalid metadata blockers were already fixed earlier in the branch history.',
  },
  {
    label: 'Release validation tooling',
    state: 'pass',
    detail: '`repobrain release-check` and `repobrain demo-clean` are available locally and documented for operator use.',
  },
  {
    label: 'Docs frontend',
    state: 'info',
    detail: 'This docs app is the new human-friendly frontend for understanding the repo, commands, and release posture.',
  },
  {
    label: 'Remote release workflow',
    state: 'pending',
    detail: 'Still depends on GitHub auth/remote workflow execution and cannot be declared complete until that path is run.',
  },
  {
    label: 'Live provider smoke',
    state: 'pending',
    detail: 'Still depends on real API keys and provider access beyond the local mocked/default path.',
  },
]

export const faqs: FaqEntry[] = [
  {
    question: 'What problem is RepoBrain actually solving?',
    answer: 'RepoBrain reduces bad code generation by fixing the step before code generation: finding the right files, tracing real flows, surfacing evidence, and lowering confidence when the evidence is weak.',
  },
  {
    question: 'Should I start with `review` or `index`?',
    answer: 'Start with `review` when you need a quick human summary of risks. Start with `index` when you are ready for grounded retrieval, tracing, and edit-target ranking.',
  },
  {
    question: 'When does the browser UI matter?',
    answer: 'Use the browser UI when you want a local-first experience for demos, onboarding, or teammates who prefer forms and panels over raw terminal commands.',
  },
  {
    question: 'How do I know whether remote providers are safe to use?',
    answer: 'Treat remote providers as opt-in. Use `repobrain doctor` and `repobrain provider-smoke` first, and remember RepoBrain stays local-first until you explicitly switch providers in `repobrain.toml`.',
  },
  {
    question: 'Why is there a dedicated `demo-clean` command?',
    answer: 'The repo accumulates heavy temporary folders during test/build cycles on Windows. `demo-clean` removes that clutter safely without deleting the frontend assets needed by `serve-web`.',
  },
]

export const docsLibrary: DocEntry[] = [
  {
    id: 'vision',
    title: 'Vision',
    eyebrow: 'Product direction',
    path: 'docs/vision.md',
    summary: 'Why RepoBrain exists, what behavior it is trying to change in coding assistants, and what success looks like.',
    audience: 'Founders, reviewers, new contributors',
    tags: ['product', 'direction', 'why'],
    content: visionDoc,
  },
  {
    id: 'install',
    title: 'Install Guide',
    eyebrow: 'Get started',
    path: 'docs/install.md',
    summary: 'Environment setup, package installation, and the minimum path to first use.',
    audience: 'Anyone onboarding to the repo',
    tags: ['install', 'onboarding', 'setup'],
    content: installDoc,
  },
  {
    id: 'run',
    title: 'Run Guide',
    eyebrow: 'Daily workflow',
    path: 'docs/run.md',
    summary: 'How to run RepoBrain from CLI, browser UI, report mode, MCP mode, and demo prep flows.',
    audience: 'Users and operators',
    tags: ['run', 'workflow', 'demo'],
    content: runDoc,
  },
  {
    id: 'cli',
    title: 'CLI Reference',
    eyebrow: 'Command surface',
    path: 'docs/cli.md',
    summary: 'Descriptions of every primary command, what it returns, and how the tools fit together.',
    audience: 'Power users and maintainers',
    tags: ['cli', 'commands', 'reference'],
    content: cliDoc,
  },
  {
    id: 'architecture',
    title: 'Architecture',
    eyebrow: 'System design',
    path: 'docs/architecture.md',
    summary: 'The retrieval engine, indexing model, grounding flow, and major design tradeoffs behind RepoBrain.',
    audience: 'Engineers reading the core design',
    tags: ['architecture', 'engine', 'design'],
    content: architectureDoc,
  },
  {
    id: 'mcp',
    title: 'MCP',
    eyebrow: 'Agent integration',
    path: 'docs/mcp.md',
    summary: 'How RepoBrain exposes tools over a stdio transport for coding assistants and automation layers.',
    audience: 'Tooling engineers and agent builders',
    tags: ['mcp', 'agent', 'integration'],
    content: mcpDoc,
  },
  {
    id: 'ux',
    title: 'User Experience',
    eyebrow: 'Interaction design',
    path: 'docs/ux.md',
    summary: 'What the human-facing product should feel like across CLI, report, and browser surfaces.',
    audience: 'Product and frontend contributors',
    tags: ['ux', 'frontend', 'design'],
    content: uxDoc,
  },
  {
    id: 'evaluation',
    title: 'Evaluation',
    eyebrow: 'Quality signals',
    path: 'docs/evaluation.md',
    summary: 'How retrieval quality is measured and what metrics matter for RepoBrain confidence.',
    audience: 'Engineers tuning relevance and safety',
    tags: ['evaluation', 'benchmark', 'quality'],
    content: evaluationDoc,
  },
  {
    id: 'production-readiness',
    title: 'Production Readiness',
    eyebrow: 'Operator checklist',
    path: 'docs/production-readiness.md',
    summary: 'The bridge between “it works locally” and “it is safe enough to ship or demo seriously”.',
    audience: 'Operators and release owners',
    tags: ['production', 'readiness', 'ship'],
    content: productionReadinessDoc,
  },
  {
    id: 'release-checklist',
    title: 'Release Checklist',
    eyebrow: 'Publish flow',
    path: 'docs/release-checklist.md',
    summary: 'What to verify before tagging or publishing, including artifact validation and frontend packaging.',
    audience: 'Release owners',
    tags: ['release', 'checklist', 'publish'],
    content: releaseChecklistDoc,
  },
  {
    id: 'demo-script',
    title: 'Demo Script',
    eyebrow: 'Show the product well',
    path: 'docs/demo-script.md',
    summary: 'A practical sequence for live demos that keeps the story grounded and legible to non-experts.',
    audience: 'Demo presenters and OSS launch prep',
    tags: ['demo', 'presentation', 'script'],
    content: demoScriptDoc,
  },
  {
    id: 'roadmap',
    title: 'Roadmap',
    eyebrow: 'Release track',
    path: 'ROADMAP.md',
    summary: 'The staged release path from MVP toward a stable 1.0 codebase memory product.',
    audience: 'Anyone planning future work',
    tags: ['roadmap', 'versions', 'future'],
    content: roadmapDoc,
  },
]
