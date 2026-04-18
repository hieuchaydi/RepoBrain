import {
  type ChangeEvent,
  startTransition,
  useDeferredValue,
  useEffect,
  useState,
} from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Binary,
  BookOpenText,
  Bot,
  ChevronRight,
  Command,
  GitBranch,
  LayoutDashboard,
  MoonStar,
  Search,
  ShieldCheck,
  Sparkles,
  SunMedium,
  TerminalSquare,
  Workflow,
} from 'lucide-react'
import { RepoBrainLogo } from './components/RepoBrainLogo'
import {
  commandCatalog,
  docsLibrary,
  faqs,
  heroMetrics,
  navigationSections,
  quickstartSteps,
  releaseStatus,
  repoMap,
  surfaces,
} from './content'
import './App.css'

type Theme = 'light' | 'dark'

const sectionIcons = [
  Sparkles,
  TerminalSquare,
  Workflow,
  LayoutDashboard,
]

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') {
    return 'dark'
  }

  const savedTheme = window.localStorage.getItem('repobrain-docs-theme')
  if (savedTheme === 'light' || savedTheme === 'dark') {
    return savedTheme
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function normalizeSearchText(value: string) {
  return value.toLowerCase().replaceAll('`', '').trim()
}

function App() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme)
  const [query, setQuery] = useState('')
  const [selectedDocId, setSelectedDocId] = useState(docsLibrary[0]?.id ?? '')
  const deferredQuery = useDeferredValue(normalizeSearchText(query))

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    window.localStorage.setItem('repobrain-docs-theme', theme)
  }, [theme])

  const visibleDocs = docsLibrary.filter((doc) => {
    if (!deferredQuery) {
      return true
    }

    const haystack = normalizeSearchText(
      `${doc.title} ${doc.eyebrow} ${doc.summary} ${doc.audience} ${doc.path} ${doc.tags.join(' ')} ${doc.content.slice(0, 600)}`,
    )

    return haystack.includes(deferredQuery)
  })

  const visibleCommands = commandCatalog.filter((entry) => {
    if (!deferredQuery) {
      return true
    }

    return normalizeSearchText(
      `${entry.category} ${entry.command} ${entry.summary} ${entry.result}`,
    ).includes(deferredQuery)
  })

  const visibleFaqs = faqs.filter((entry) => {
    if (!deferredQuery) {
      return true
    }

    return normalizeSearchText(`${entry.question} ${entry.answer}`).includes(deferredQuery)
  })

  const effectiveSelectedDocId =
    visibleDocs.find((entry) => entry.id === selectedDocId)?.id ??
    visibleDocs[0]?.id ??
    docsLibrary[0]?.id ??
    ''

  const selectedDoc =
    docsLibrary.find((entry) => entry.id === effectiveSelectedDocId) ??
    visibleDocs[0] ??
    docsLibrary[0]

  function handleSearchChange(event: ChangeEvent<HTMLInputElement>) {
    const nextValue = event.target.value
    startTransition(() => {
      setQuery(nextValue)
    })
  }

  function toggleTheme() {
    setTheme((current) => (current === 'dark' ? 'light' : 'dark'))
  }

  function resolveLocalDocId(href: string | undefined) {
    if (!href) {
      return null
    }

    const cleanedHref = href.split('#')[0]?.replaceAll('\\', '/').replace(/^\.?\//, '')
    if (!cleanedHref) {
      return null
    }

    const cleanedBasename = cleanedHref.split('/').at(-1)

    for (const entry of docsLibrary) {
      const entryBasename = entry.path.split('/').at(-1)
      if (
        cleanedHref === entry.path ||
        cleanedHref === entryBasename ||
        entry.path.endsWith(cleanedHref) ||
        cleanedBasename === entryBasename
      ) {
        return entry.id
      }
    }

    return null
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="sidebar-panel">
          <RepoBrainLogo compact />
          <p className="sidebar-copy">
            A human-friendly frontend for understanding the RepoBrain repo without
            jumping across markdown files and scattered notes.
          </p>

          <div className="sidebar-search">
            <label className="search-field" htmlFor="repo-search">
              <Search size={17} />
              <input
                id="repo-search"
                type="search"
                value={query}
                onChange={handleSearchChange}
                placeholder="Search docs, commands, or release notes"
              />
            </label>
            <button className="theme-toggle" type="button" onClick={toggleTheme}>
              {theme === 'dark' ? <SunMedium size={16} /> : <MoonStar size={16} />}
              <span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
            </button>
          </div>

          <nav className="sidebar-nav" aria-label="Documentation sections">
            {navigationSections.map((section) => (
              <a key={section.id} href={`#${section.id}`}>
                <span>{section.label}</span>
                <ChevronRight size={16} />
              </a>
            ))}
          </nav>

          <div className="sidebar-status">
            <div>
              <span className="eyebrow">Search scope</span>
              <strong>{visibleDocs.length} docs</strong>
              <small>{visibleCommands.length} commands and {visibleFaqs.length} FAQ entries match</small>
            </div>
            <div>
              <span className="eyebrow">Current focus</span>
              <strong>{selectedDoc?.title ?? 'No document selected'}</strong>
              <small>{selectedDoc?.path ?? 'Pick a document from the library below'}</small>
            </div>
          </div>
        </div>
      </aside>

      <main className="app-main">
        <section className="hero-section" id="overview">
          <div className="hero-copy card">
            <span className="eyebrow">RepoBrain documentation frontend</span>
            <RepoBrainLogo />
            <p className="hero-lead">
              RepoBrain is a local-first codebase memory engine that helps AI
              coding assistants gather context before they generate code. This
              frontend turns the repo into a readable, modern docs experience for
              teammates, reviewers, and curious users.
            </p>
            <div className="hero-actions">
              <a className="primary-action" href="#docs-library">
                Explore docs
              </a>
              <a className="secondary-action" href="#quickstart">
                Follow quickstart
              </a>
            </div>
          </div>

          <div className="hero-stack">
            <div className="card hero-spotlight">
              <span className="eyebrow">What makes this repo interesting</span>
              <ul className="bullet-grid">
                <li>Grounded retrieval over code, symbols, snippets, and edges</li>
                <li>CLI, local browser UI, report dashboard, and MCP transport</li>
                <li>Release validation and demo cleanup flows built into the tool</li>
                <li>Safer context-gathering before any assistant edits code</li>
              </ul>
            </div>
            <div className="metrics-grid">
              {heroMetrics.map((metric) => (
                <article className="card metric-card" key={metric.label}>
                  <strong>{metric.value}</strong>
                  <span>{metric.label}</span>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section-block" id="surfaces">
          <div className="section-heading">
            <span className="eyebrow">Product surfaces</span>
            <h2>One repo, several ways to use it</h2>
            <p>
              RepoBrain is no longer just a CLI experiment. The repo now includes
              a browser UI, ship checks, release validation, a docs frontend, and
              an MCP-style transport for assistant tooling.
            </p>
          </div>
          <div className="surface-grid">
            {surfaces.map((surface, index) => {
              const Icon = sectionIcons[index % sectionIcons.length]

              return (
                <article className="card surface-card" key={surface.title}>
                  <div className="surface-icon">
                    <Icon size={20} />
                  </div>
                  <h3>{surface.title}</h3>
                  <p>{surface.description}</p>
                  <small>{surface.detail}</small>
                </article>
              )
            })}
          </div>
        </section>

        <section className="section-block quickstart-block" id="quickstart">
          <div className="section-heading">
            <span className="eyebrow">Quickstart</span>
            <h2>How to understand the repo in one sitting</h2>
            <p>
              This path is the shortest route from clean clone to meaningful
              RepoBrain usage. It is also the path a new teammate can follow
              without reading every markdown file first.
            </p>
          </div>

          <div className="quickstart-layout">
            <div className="quickstart-steps">
              {quickstartSteps.map((step, index) => (
                <article className="card quickstart-card" key={step.title}>
                  <span className="step-index">0{index + 1}</span>
                  <div>
                    <h3>{step.title}</h3>
                    <p>{step.body}</p>
                    <pre>
                      <code>{step.command}</code>
                    </pre>
                  </div>
                </article>
              ))}
            </div>

            <aside className="card quickstart-panel">
              <h3>Recommended reading order</h3>
              <ol>
                <li>`Vision` to understand the why.</li>
                <li>`Install Guide` and `Run Guide` to operate the product.</li>
                <li>`CLI Reference` and `Architecture` to reason about behavior.</li>
                <li>`Production Readiness` and `Release Checklist` before demos or tags.</li>
              </ol>

              <div className="repo-callouts">
                <div>
                  <BookOpenText size={18} />
                  <p>Use the docs library below to open any source markdown file inside this UI.</p>
                </div>
                <div>
                  <ShieldCheck size={18} />
                  <p>Use `doctor`, `provider-smoke`, and `release-check` before claiming readiness.</p>
                </div>
                <div>
                  <LayoutDashboard size={18} />
                  <p>Use `demo-clean` before a live session so the repo feels intentional, not cluttered.</p>
                </div>
              </div>
            </aside>
          </div>
        </section>

        <section className="section-block" id="commands">
          <div className="section-heading">
            <span className="eyebrow">Command catalog</span>
            <h2>What people actually run</h2>
            <p>
              The repo has grown enough that a readable command map matters. These
              are the commands most likely to show up in onboarding, demos,
              release checks, and everyday investigation.
            </p>
          </div>

          <div className="command-grid">
            {visibleCommands.map((entry) => (
              <article className="card command-card" key={entry.command}>
                <div className="command-card-top">
                  <span className="command-category">{entry.category}</span>
                  <Command size={16} />
                </div>
                <pre>
                  <code>{entry.command}</code>
                </pre>
                <p>{entry.summary}</p>
                <small>{entry.result}</small>
              </article>
            ))}
          </div>
        </section>

        <section className="section-block repo-map-block" id="repo-map">
          <div className="section-heading">
            <span className="eyebrow">Repo map</span>
            <h2>Where to look when you want source, UX, or release logic</h2>
            <p>
              RepoBrain mixes Python, React, docs, tests, and release automation.
              This map gives contributors a clean mental model of the top-level
              structure.
            </p>
          </div>
          <div className="repo-map-grid">
            {repoMap.map((entry) => (
              <article className="card repo-map-card" key={entry.path}>
                <code>{entry.path}</code>
                <p>{entry.summary}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section-block docs-block" id="docs-library">
          <div className="section-heading">
            <span className="eyebrow">Docs library</span>
            <h2>Open the repo docs without leaving the frontend</h2>
            <p>
              Pick any important markdown source and read it below in the reading
              room. Search narrows the list when you only remember a topic, not a
              file name.
            </p>
          </div>

          <div className="docs-grid">
            {visibleDocs.map((doc) => (
              <button
                className={`card doc-card${selectedDoc?.id === doc.id ? ' active' : ''}`}
                key={doc.id}
                type="button"
                onClick={() => setSelectedDocId(doc.id)}
              >
                <span className="eyebrow">{doc.eyebrow}</span>
                <h3>{doc.title}</h3>
                <p>{doc.summary}</p>
                <div className="doc-meta">
                  <code>{doc.path}</code>
                  <span>{doc.audience}</span>
                </div>
                <div className="doc-tags">
                  {doc.tags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="section-block reader-block" id="reader">
          <div className="section-heading">
            <span className="eyebrow">Reading room</span>
            <h2>{selectedDoc?.title ?? 'Select a document'}</h2>
            <p>
              This section renders the source markdown directly from the repo so
              the docs frontend stays aligned with the actual project documents.
            </p>
          </div>

          {selectedDoc ? (
            <div className="reader-layout">
              <aside className="card reader-meta">
                <span className="eyebrow">{selectedDoc.eyebrow}</span>
                <h3>{selectedDoc.title}</h3>
                <p>{selectedDoc.summary}</p>
                <div className="reader-stat">
                  <strong>Source file</strong>
                  <code>{selectedDoc.path}</code>
                </div>
                <div className="reader-stat">
                  <strong>Best for</strong>
                  <span>{selectedDoc.audience}</span>
                </div>
                <div className="reader-tags">
                  {selectedDoc.tags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
                <a className="secondary-action full-width" href="#docs-library">
                  Switch document
                </a>
              </aside>

              <article className="card markdown-shell">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ href, children }) => {
                      const localDocId = resolveLocalDocId(href)

                      if (localDocId) {
                        return (
                          <a
                            href="#reader"
                            onClick={(event) => {
                              event.preventDefault()
                              setSelectedDocId(localDocId)
                            }}
                          >
                            {children}
                          </a>
                        )
                      }

                      return (
                        <a href={href} target="_blank" rel="noreferrer">
                          {children}
                        </a>
                      )
                    },
                  }}
                >
                  {selectedDoc.content}
                </ReactMarkdown>
              </article>
            </div>
          ) : (
            <div className="card empty-state">
              <p>No document matches the current search. Clear the search box to reopen the full docs library.</p>
            </div>
          )}
        </section>

        <section className="section-block release-block" id="release-state">
          <div className="section-heading">
            <span className="eyebrow">Release state</span>
            <h2>What is done locally, and what still needs real-world validation</h2>
            <p>
              RepoBrain is already much stronger locally. The biggest remaining
              uncertainty is no longer packaging logic but remote workflow and
              real provider execution.
            </p>
          </div>
          <div className="status-grid">
            {releaseStatus.map((entry) => (
              <article className={`card status-card status-${entry.state}`} key={entry.label}>
                <div className="status-pill">{entry.state}</div>
                <h3>{entry.label}</h3>
                <p>{entry.detail}</p>
              </article>
            ))}
          </div>
          <div className="card release-callout">
            <div>
              <Binary size={18} />
              <p>
                Remote publish validation still depends on GitHub workflow access
                and real credentials. That part cannot be honestly marked done
                from UI work alone.
              </p>
            </div>
            <div>
              <Bot size={18} />
              <p>
                The local product is now easier to explain to humans, which makes
                future demo, onboarding, and OSS storytelling materially better.
              </p>
            </div>
            <div>
              <GitBranch size={18} />
              <p>
                Once remote auth is available, the next practical move is to push
                `master`, run the release workflow with `publish=false`, and
                inspect the produced artifacts.
              </p>
            </div>
          </div>
        </section>

        <section className="section-block faq-block" id="faq">
          <div className="section-heading">
            <span className="eyebrow">FAQ</span>
            <h2>Questions teammates usually ask first</h2>
            <p>
              These answers are tuned for onboarding conversations, project
              reviews, and demo prep.
            </p>
          </div>
          <div className="faq-list">
            {visibleFaqs.map((entry) => (
              <details className="card faq-item" key={entry.question}>
                <summary>{entry.question}</summary>
                <p>{entry.answer}</p>
              </details>
            ))}
          </div>
        </section>

        <footer className="footer card">
          <div>
            <RepoBrainLogo compact />
            <p>
              Built as a readable docs frontend for the RepoBrain repository. Use
              it alongside the source docs, not instead of them.
            </p>
          </div>
          <div className="footer-links">
            <a href="#overview">Back to top</a>
            <a href="#reader">Open reading room</a>
            <a href="#release-state">Check release state</a>
          </div>
        </footer>
      </main>
    </div>
  )
}

export default App
