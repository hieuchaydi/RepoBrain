import { useEffect, useMemo, useState } from "react";

type Locale = "en" | "vi";
type Theme = "light" | "dark";
type QueryMode = "query" | "trace" | "impact" | "targets";
type ActionKind =
  | "import"
  | "index"
  | "review"
  | "ship"
  | "baseline"
  | "provider-smoke"
  | "doctor"
  | "query"
  | "trace"
  | "impact"
  | "targets";

type BootstrapPayload = {
  ok: boolean;
  active_repo: string;
  repo_input: string;
  report_url: string;
  locales: Locale[];
  default_mode: QueryMode;
};

type ProviderStatusDetail = {
  active?: string;
  configured?: string;
  ready?: boolean;
  local_only?: boolean;
  requires_network?: boolean;
  warnings?: string[];
  missing?: string[];
};

type ParserDetail = {
  selected?: string;
  heuristic_fallback?: boolean;
};

type DoctorData = {
  indexed?: boolean;
  repo_root?: string;
  stats?: {
    files?: number;
    chunks?: number;
    symbols?: number;
    edges?: number;
  };
  providers?: {
    embedding?: string;
    reranker?: string;
    embedding_model?: string;
    reranker_model?: string;
    reranker_models?: string[];
    reranker_last_failover_error?: string | null;
  };
  provider_status?: Record<string, ProviderStatusDetail>;
  security?: {
    local_storage_only?: boolean;
    remote_providers_enabled?: boolean;
    network_required?: boolean;
  };
  capabilities?: {
    language_parsers?: Record<string, ParserDetail>;
  };
};

type ProviderSmokeData = {
  repo_root?: string;
  providers?: DoctorData["providers"];
  provider_status?: Record<string, ProviderStatusDetail>;
  embedding_smoke?: {
    status?: string;
    vector_count?: number;
    dimensions?: number;
    error?: string;
  };
  reranker_smoke?: {
    status?: string;
    score?: number;
    active_model_before?: string | null;
    active_model_after?: string | null;
    pool?: string[];
    last_failover_error?: string | null;
    error?: string;
  };
};

type ActionPayload = {
  ok: boolean;
  active_repo: string;
  repo_input: string;
  message: string;
  title: string;
  result: string;
  report_url?: string;
  data?: DoctorData | ProviderSmokeData | null;
};

type ActivityEntry = {
  id: number;
  action: ActionKind;
  message: string;
  timestamp: string;
};

const copy = {
  en: {
    brand: "RepoBrain Web",
    subtitle:
      "Local React workspace for importing a project, indexing it once, and running grounded codebase actions without repeating repo paths.",
    language: "Language",
    theme: "Theme",
    english: "English",
    vietnamese: "Vietnamese",
    light: "Light",
    dark: "Dark",
    activeRepo: "Active repo",
    none: "None",
    noActiveRepo: "No active repo yet. Import a project path below.",
    importTitle: "Fast import",
    projectPath: "Project path",
    projectPathPlaceholder: "C:\\path\\to\\your-project",
    importButton: "Import + Index",
    importHint:
      "This initializes RepoBrain state, stores the active repo, and builds the local index in one step.",
    actionsTitle: "Active repo actions",
    index: "Re-index active repo",
    review: "Scan project review",
    ship: "Ship gate",
    baseline: "Save baseline",
    providerSmoke: "Provider smoke",
    doctor: "Doctor",
    openReport: "Open report",
    actionsHint:
      "Use Project Review for gaps, Ship Gate for a blunt release verdict, Baseline for drift tracking, and Provider Smoke for direct model/provider validation.",
    queryTitle: "Grounded question",
    mode: "Mode",
    question: "Question",
    questionPlaceholder: "Where is payment retry logic implemented?",
    run: "Run",
    resultTitle: "Result",
    emptyResult:
      "No result yet. Import a repo, then run review, doctor, provider smoke, or a grounded question.",
    loading: "Working...",
    queryMode: "Query",
    traceMode: "Trace",
    impactMode: "Impact",
    targetsMode: "Targets",
    interfaceStatus: "Interface status",
    localOnly: "Local-only browser UI",
    localOnlyHint:
      "The browser app talks to your local RepoBrain Python server only. No hosted backend is required.",
    reportHint:
      "The detailed dashboard still opens as a separate local report so you can keep the React workflow focused on actions and results.",
    diagnosticsTitle: "Release diagnostics",
    diagnosticsHint:
      "Doctor posture and provider smoke stay visible here so release checks do not depend on scrolling through raw text output.",
    doctorSnapshot: "Doctor snapshot",
    smokeSnapshot: "Provider smoke snapshot",
    activityTitle: "Recent activity",
    activityHint: "RepoBrain keeps a short local timeline of what you just ran in this browser tab.",
    noDiagnostics: "Run Doctor after import to populate structured release diagnostics.",
    noSmoke: "Run Provider Smoke to see active models, failover state, and direct provider health here.",
    noActivity: "No activity yet in this session.",
    indexed: "Indexed",
    files: "Files",
    chunks: "Chunks",
    symbols: "Symbols",
    edges: "Edges",
    embedding: "Embedding",
    reranker: "Reranker",
    embeddingModel: "Embedding model",
    rerankerModel: "Reranker model",
    fallbackPool: "Gemini fallback pool",
    singleModel: "Single-model mode",
    failover: "Last failover",
    remoteProviders: "Remote providers",
    networkRequired: "Network required",
    localStorageOnly: "Local storage only",
    parserPosture: "Parser posture",
    providerPosture: "Provider posture",
    warnings: "Warnings",
    noWarnings: "No warnings",
    status: "Status",
    score: "Score",
    vectors: "Vectors",
    dimensions: "Dimensions",
    activeBefore: "Active before",
    activeAfter: "Active after",
    lastSync: "Last sync",
    unavailable: "Unavailable",
    yes: "Yes",
    no: "No",
    ready: "Ready",
    notReady: "Not ready",
    disabledUntilImport: "Import a repo to unlock actions and grounded queries.",
  },
  vi: {
    brand: "RepoBrain Web",
    subtitle:
      "Workspace React local để import dự án, index một lần, và chạy các tác vụ codebase có grounding mà không cần lặp lại đường dẫn repo.",
    language: "Ngôn ngữ",
    theme: "Giao diện",
    english: "Tiếng Anh",
    vietnamese: "Tiếng Việt",
    light: "Sáng",
    dark: "Tối",
    activeRepo: "Repo đang active",
    none: "Chưa có",
    noActiveRepo: "Chưa có repo active. Hãy import đường dẫn dự án ở bên dưới.",
    importTitle: "Import nhanh",
    projectPath: "Đường dẫn dự án",
    projectPathPlaceholder: "C:\\đường-dẫn\\tới\\dự-án-của-bạn",
    importButton: "Import + Index",
    importHint:
      "Tác vụ này sẽ khởi tạo state RepoBrain, lưu repo active, và build local index chỉ trong một bước.",
    actionsTitle: "Tác vụ trên repo active",
    index: "Index lại repo active",
    review: "Quét project review",
    ship: "Ship gate",
    baseline: "Lưu baseline",
    providerSmoke: "Smoke provider",
    doctor: "Doctor",
    openReport: "Mở report",
    actionsHint:
      "Dùng Project Review để xem gap, Ship Gate để xem verdict release, Baseline để track drift, và Provider Smoke để kiểm tra trực tiếp model/provider hiện tại.",
    queryTitle: "Câu hỏi có grounding",
    mode: "Chế độ",
    question: "Câu hỏi",
    questionPlaceholder: "Logic payment retry nằm ở đâu?",
    run: "Chạy",
    resultTitle: "Kết quả",
    emptyResult:
      "Chưa có kết quả. Hãy import repo, sau đó chạy review, doctor, provider smoke, hoặc một câu hỏi grounded.",
    loading: "Đang xử lý...",
    queryMode: "Query",
    traceMode: "Trace",
    impactMode: "Impact",
    targetsMode: "Targets",
    interfaceStatus: "Trạng thái giao diện",
    localOnly: "Giao diện trình duyệt chỉ chạy local",
    localOnlyHint:
      "Ứng dụng browser này chỉ gọi tới RepoBrain Python server đang chạy local của bạn. Không cần hosted backend.",
    reportHint:
      "Dashboard chi tiết vẫn mở thành một local report riêng để luồng React tập trung vào thao tác và kết quả.",
    diagnosticsTitle: "Diagnostics cho release",
    diagnosticsHint:
      "Doctor posture và provider smoke được giữ hiển thị ở đây để lúc release không phải đọc lại cả khối text dài.",
    doctorSnapshot: "Ảnh chụp Doctor",
    smokeSnapshot: "Ảnh chụp Provider Smoke",
    activityTitle: "Hoạt động gần đây",
    activityHint: "RepoBrain giữ một timeline ngắn cho những tác vụ bạn vừa chạy trong tab này.",
    noDiagnostics: "Hãy chạy Doctor sau khi import để đổ dữ liệu diagnostics có cấu trúc.",
    noSmoke: "Hãy chạy Provider Smoke để xem model active, trạng thái failover, và sức khỏe provider trực tiếp tại đây.",
    noActivity: "Chưa có hoạt động nào trong session này.",
    indexed: "Đã index",
    files: "Files",
    chunks: "Chunks",
    symbols: "Symbols",
    edges: "Edges",
    embedding: "Embedding",
    reranker: "Reranker",
    embeddingModel: "Model embedding",
    rerankerModel: "Model reranker",
    fallbackPool: "Pool fallback Gemini",
    singleModel: "Chế độ một model",
    failover: "Failover gần nhất",
    remoteProviders: "Provider từ xa",
    networkRequired: "Cần mạng",
    localStorageOnly: "Chỉ lưu local",
    parserPosture: "Trạng thái parser",
    providerPosture: "Trạng thái provider",
    warnings: "Cảnh báo",
    noWarnings: "Không có cảnh báo",
    status: "Trạng thái",
    score: "Điểm",
    vectors: "Vectors",
    dimensions: "Chiều",
    activeBefore: "Model trước",
    activeAfter: "Model sau",
    lastSync: "Lần đồng bộ",
    unavailable: "Chưa có",
    yes: "Có",
    no: "Không",
    ready: "Sẵn sàng",
    notReady: "Chưa sẵn sàng",
    disabledUntilImport: "Hãy import repo trước để mở khóa action và truy vấn grounded.",
  },
} as const;

function useLocale(): [Locale, (next: Locale) => void] {
  const [locale, setLocale] = useState<Locale>(() => {
    const saved = window.localStorage.getItem("repobrain-web-locale");
    return saved === "vi" ? "vi" : "en";
  });

  useEffect(() => {
    window.localStorage.setItem("repobrain-web-locale", locale);
    document.documentElement.lang = locale;
  }, [locale]);

  return [locale, setLocale];
}

function useTheme(): [Theme, (next: Theme) => void] {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = window.localStorage.getItem("repobrain-web-theme");
    if (saved === "dark" || saved === "light") {
      return saved;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    window.localStorage.setItem("repobrain-web-theme", theme);
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  return [theme, setTheme];
}

async function readJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  const payload = (await response.json()) as T & { error?: string };
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

function labelForAction(locale: Locale, action: ActionKind): string {
  const t = copy[locale];
  switch (action) {
    case "trace":
      return t.traceMode;
    case "impact":
      return t.impactMode;
    case "targets":
      return t.targetsMode;
    case "index":
      return t.index;
    case "review":
      return t.review;
    case "ship":
      return t.ship;
    case "baseline":
      return t.baseline;
    case "provider-smoke":
      return t.providerSmoke;
    case "doctor":
      return t.doctor;
    case "import":
      return t.importButton;
    default:
      return t.queryMode;
  }
}

function toneForBoolean(value?: boolean | null): string {
  if (value === true) {
    return "good";
  }
  if (value === false) {
    return "bad";
  }
  return "warn";
}

function toneForStatus(status?: string | null): string {
  if (!status) {
    return "warn";
  }
  if (status === "pass" || status === "ready") {
    return "good";
  }
  if (status === "error" || status === "fail") {
    return "bad";
  }
  return "warn";
}

function formatTimestamp(locale: Locale, value: string | null): string {
  if (!value) {
    return copy[locale].unavailable;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return copy[locale].unavailable;
  }
  return date.toLocaleTimeString(locale === "vi" ? "vi-VN" : "en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function yesNo(locale: Locale, value?: boolean | null): string {
  if (value === undefined || value === null) {
    return copy[locale].unavailable;
  }
  return value ? copy[locale].yes : copy[locale].no;
}

function formatWarnings(locale: Locale, warnings?: string[]): string {
  if (!warnings || warnings.length === 0) {
    return copy[locale].noWarnings;
  }
  return warnings.join(" | ");
}

function parserSummary(detail?: ParserDetail, locale?: Locale): string {
  if (!detail) {
    return locale ? copy[locale].unavailable : "Unavailable";
  }
  const selected = detail.selected || (locale ? copy[locale].unavailable : "Unavailable");
  const fallback = detail.heuristic_fallback;
  if (fallback === undefined) {
    return selected;
  }
  return `${selected} · fallback ${fallback ? "on" : "off"}`;
}

export function App() {
  const [locale, setLocale] = useLocale();
  const [theme, setTheme] = useTheme();
  const [boot, setBoot] = useState<BootstrapPayload | null>(null);
  const [repoPath, setRepoPath] = useState("");
  const [query, setQuery] = useState("Where is payment retry logic implemented?");
  const [mode, setMode] = useState<QueryMode>("query");
  const [message, setMessage] = useState("");
  const [resultTitle, setResultTitle] = useState("");
  const [resultBody, setResultBody] = useState("");
  const [resultAction, setResultAction] = useState<ActionKind>("query");
  const [busy, setBusy] = useState<string | null>(null);
  const [doctorData, setDoctorData] = useState<DoctorData | null>(null);
  const [smokeData, setSmokeData] = useState<ProviderSmokeData | null>(null);
  const [doctorSyncAt, setDoctorSyncAt] = useState<string | null>(null);
  const [smokeSyncAt, setSmokeSyncAt] = useState<string | null>(null);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);

  const t = copy[locale];
  const activeRepo = boot?.active_repo || "";
  const reportUrl = boot?.report_url || "/report";
  const hasActiveRepo = Boolean(activeRepo);

  useEffect(() => {
    void (async () => {
      const payload = await readJson<BootstrapPayload>("/api/bootstrap");
      setBoot(payload);
      setRepoPath(payload.repo_input || "");
      setMode(payload.default_mode);
    })().catch((error: Error) => {
      setMessage(error.message);
    });
  }, []);

  async function refreshDoctorSnapshot() {
    try {
      const payload = await readJson<ActionPayload>("/api/doctor");
      const data = payload.data as DoctorData | undefined;
      if (data) {
        setDoctorData(data);
        setDoctorSyncAt(new Date().toISOString());
      }
    } catch {
      // Keep the last visible diagnostics if a background refresh fails.
    }
  }

  useEffect(() => {
    if (!hasActiveRepo) {
      setDoctorData(null);
      setSmokeData(null);
      setDoctorSyncAt(null);
      setSmokeSyncAt(null);
      return;
    }
    void refreshDoctorSnapshot();
  }, [hasActiveRepo, activeRepo]);

  function syncBoot(payload: ActionPayload) {
    setBoot((current) => ({
      ok: true,
      active_repo: payload.active_repo,
      repo_input: payload.repo_input,
      report_url: payload.report_url || current?.report_url || "/report",
      locales: current?.locales || ["en", "vi"],
      default_mode: current?.default_mode || mode,
    }));
    setRepoPath(payload.repo_input || payload.active_repo || "");
  }

  function appendActivity(action: ActionKind, messageText: string) {
    const entry: ActivityEntry = {
      id: Date.now(),
      action,
      message: messageText,
      timestamp: new Date().toISOString(),
    };
    setActivity((current) => [entry, ...current].slice(0, 6));
  }

  function applyPayload(action: ActionKind, payload: ActionPayload) {
    syncBoot(payload);
    setMessage(payload.message);
    setResultTitle(payload.title);
    setResultBody(payload.result);
    setResultAction(action);
    appendActivity(action, payload.message);

    if (action === "doctor" && payload.data) {
      setDoctorData(payload.data as DoctorData);
      setDoctorSyncAt(new Date().toISOString());
    }
    if (action === "provider-smoke" && payload.data) {
      setSmokeData(payload.data as ProviderSmokeData);
      setSmokeSyncAt(new Date().toISOString());
    }
    if (action === "import" || action === "index") {
      void refreshDoctorSnapshot();
    }
  }

  async function runAction(action: "index" | "review" | "ship" | "baseline" | "provider-smoke" | "doctor") {
    try {
      setBusy(action);
      const payload =
        action === "doctor"
          ? await readJson<ActionPayload>("/api/doctor")
          : await readJson<ActionPayload>(`/api/${action}`, {
              method: "POST",
              body: JSON.stringify({}),
            });
      applyPayload(action, payload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  async function handleImport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setBusy("import");
      const payload = await readJson<ActionPayload>("/api/import", {
        method: "POST",
        body: JSON.stringify({ repo_path: repoPath }),
      });
      applyPayload("import", payload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  async function handleQuery(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setBusy("query");
      const payload = await readJson<ActionPayload>("/api/query", {
        method: "POST",
        body: JSON.stringify({ mode, query }),
      });
      const queryAction: ActionKind = mode === "query" ? "query" : mode;
      applyPayload(queryAction, payload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  const actionButtons = useMemo(
    () => [
      { key: "index", label: t.index, tone: "ghost-button" },
      { key: "review", label: t.review, tone: "ghost-button" },
      { key: "ship", label: t.ship, tone: "secondary-button" },
      { key: "baseline", label: t.baseline, tone: "ghost-button" },
      { key: "provider-smoke", label: t.providerSmoke, tone: "ghost-button" },
      { key: "doctor", label: t.doctor, tone: "ghost-button" },
    ] as const,
    [t],
  );

  const providerEntries = Object.entries(doctorData?.provider_status || {}) as [string, ProviderStatusDetail][];
  const parserEntries = Object.entries(doctorData?.capabilities?.language_parsers || {}) as [string, ParserDetail][];
  const rerankerPool = doctorData?.providers?.reranker_models || smokeData?.reranker_smoke?.pool || [];
  const rerankerPoolText = rerankerPool.length > 0 ? rerankerPool.join(" -> ") : t.singleModel;
  const lastFailoverText =
    doctorData?.providers?.reranker_last_failover_error ||
    smokeData?.reranker_smoke?.last_failover_error ||
    t.noWarnings;
  const resultBadge = labelForAction(locale, resultAction);

  return (
    <main className="app-shell">
      <section className="hero-grid">
        <article className="hero-card brand-card">
          <div className="hero-topline">
            <span className="status-pill">{t.localOnly}</span>
            <div className="control-cluster">
              <div className="chip-switcher" aria-label={t.language}>
                <button
                  className={locale === "en" ? "chip-button active" : "chip-button"}
                  onClick={() => setLocale("en")}
                  type="button"
                >
                  EN
                </button>
                <button
                  className={locale === "vi" ? "chip-button active" : "chip-button"}
                  onClick={() => setLocale("vi")}
                  type="button"
                >
                  VI
                </button>
              </div>
              <div className="chip-switcher" aria-label={t.theme}>
                <button
                  className={theme === "light" ? "chip-button active" : "chip-button"}
                  onClick={() => setTheme("light")}
                  type="button"
                >
                  {t.light}
                </button>
                <button
                  className={theme === "dark" ? "chip-button active" : "chip-button"}
                  onClick={() => setTheme("dark")}
                  type="button"
                >
                  {t.dark}
                </button>
              </div>
            </div>
          </div>
          <h1>{t.brand}</h1>
          <p className="lead">{t.subtitle}</p>
          <div className="info-strip">
            <div>
              <span className="eyebrow">{t.interfaceStatus}</span>
              <strong>{hasActiveRepo ? t.ready : t.noActiveRepo}</strong>
            </div>
            <div>
              <span className="eyebrow">{t.activeRepo}</span>
              <strong>{activeRepo || t.none}</strong>
            </div>
            <div>
              <span className="eyebrow">{t.theme}</span>
              <strong>{theme === "dark" ? t.dark : t.light}</strong>
            </div>
          </div>
          <p className="muted-copy">{t.localOnlyHint}</p>
        </article>

        <article className="hero-card import-card">
          <h2>{t.importTitle}</h2>
          <form className="panel-form" onSubmit={handleImport}>
            <label htmlFor="repoPath">{t.projectPath}</label>
            <input
              id="repoPath"
              placeholder={t.projectPathPlaceholder}
              value={repoPath}
              onChange={(event) => setRepoPath(event.target.value)}
            />
            <button className="primary-button" disabled={busy === "import"} type="submit">
              {busy === "import" ? t.loading : t.importButton}
            </button>
          </form>
          <p className="muted-copy">{t.importHint}</p>
          {!hasActiveRepo ? <div className="notice-box neutral">{t.disabledUntilImport}</div> : null}
        </article>
      </section>

      <section className="workspace-grid">
        <article className="panel-card">
          <h2>{t.actionsTitle}</h2>
          <div className="button-grid">
            {actionButtons.map((item) => (
              <button
                key={item.key}
                className={item.tone}
                disabled={!hasActiveRepo || busy === item.key}
                onClick={() => void runAction(item.key)}
                type="button"
              >
                {busy === item.key ? t.loading : item.label}
              </button>
            ))}
            <button
              className="outline-button"
              disabled={!hasActiveRepo}
              onClick={() => window.open(reportUrl, "_blank", "noopener")}
              type="button"
            >
              {t.openReport}
            </button>
          </div>
          <p className="muted-copy">{t.actionsHint}</p>
          {message ? <div className="notice-box">{message}</div> : null}
        </article>

        <article className="panel-card">
          <h2>{t.queryTitle}</h2>
          <form className="panel-form" onSubmit={handleQuery}>
            <label htmlFor="modeSelect">{t.mode}</label>
            <select
              id="modeSelect"
              value={mode}
              onChange={(event) => setMode(event.target.value as QueryMode)}
            >
              <option value="query">{labelForAction(locale, "query")}</option>
              <option value="trace">{labelForAction(locale, "trace")}</option>
              <option value="impact">{labelForAction(locale, "impact")}</option>
              <option value="targets">{labelForAction(locale, "targets")}</option>
            </select>
            <label htmlFor="queryText">{t.question}</label>
            <textarea
              id="queryText"
              placeholder={t.questionPlaceholder}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <button className="primary-button" disabled={!hasActiveRepo || busy === "query"} type="submit">
              {busy === "query" ? t.loading : t.run}
            </button>
          </form>
          <p className="muted-copy">{t.reportHint}</p>
        </article>
      </section>

      <section className="status-grid">
        <article className="panel-card">
          <div className="section-heading">
            <div>
              <h2>{t.diagnosticsTitle}</h2>
              <p className="section-copy">{t.diagnosticsHint}</p>
            </div>
            <span className="mini-pill">{t.lastSync}: {formatTimestamp(locale, doctorSyncAt)}</span>
          </div>
          {doctorData ? (
            <>
              <div className="metric-grid">
                <article className={`metric-card ${toneForBoolean(doctorData.indexed)}`}>
                  <span>{t.indexed}</span>
                  <strong>{yesNo(locale, doctorData.indexed)}</strong>
                </article>
                <article className="metric-card">
                  <span>{t.files}</span>
                  <strong>{doctorData.stats?.files ?? 0}</strong>
                </article>
                <article className="metric-card">
                  <span>{t.embedding}</span>
                  <strong>{doctorData.providers?.embedding || t.unavailable}</strong>
                  <small>{doctorData.providers?.embedding_model || t.unavailable}</small>
                </article>
                <article className="metric-card">
                  <span>{t.reranker}</span>
                  <strong>{doctorData.providers?.reranker || t.unavailable}</strong>
                  <small>{doctorData.providers?.reranker_model || t.unavailable}</small>
                </article>
              </div>

              <div className="compact-grid">
                <article className="compact-card">
                  <span className="eyebrow">{t.fallbackPool}</span>
                  <strong>{rerankerPoolText}</strong>
                  <p>{t.failover}: {lastFailoverText}</p>
                </article>
                <article className="compact-card">
                  <span className="eyebrow">{t.remoteProviders}</span>
                  <strong>{yesNo(locale, doctorData.security?.remote_providers_enabled)}</strong>
                  <p>{t.networkRequired}: {yesNo(locale, doctorData.security?.network_required)}</p>
                </article>
                <article className="compact-card">
                  <span className="eyebrow">{t.localStorageOnly}</span>
                  <strong>{yesNo(locale, doctorData.security?.local_storage_only)}</strong>
                  <p>{t.parserPosture}: {parserEntries.length || 0}</p>
                </article>
              </div>

              <div className="subpanel-grid">
                <article className="subpanel-card">
                  <div className="subpanel-head">
                    <h3>{t.providerPosture}</h3>
                    <span className="mini-pill">{providerEntries.length || 0}</span>
                  </div>
                  {providerEntries.length > 0 ? (
                    <div className="status-list">
                      {providerEntries.map(([kind, detail]) => (
                        <article key={kind} className={`status-item ${toneForBoolean(detail.ready)}`}>
                          <div className="status-row">
                            <strong>{kind}</strong>
                            <span>{detail.active || detail.configured || t.unavailable}</span>
                          </div>
                          <p>
                            {t.status}: {detail.ready ? t.ready : t.notReady} · {t.networkRequired}:{" "}
                            {yesNo(locale, detail.requires_network)}
                          </p>
                          <small>{t.warnings}: {formatWarnings(locale, detail.warnings)}</small>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">{t.noDiagnostics}</div>
                  )}
                </article>

                <article className="subpanel-card">
                  <div className="subpanel-head">
                    <h3>{t.parserPosture}</h3>
                    <span className="mini-pill">{parserEntries.length || 0}</span>
                  </div>
                  {parserEntries.length > 0 ? (
                    <div className="status-list">
                      {parserEntries.map(([language, detail]) => (
                        <article key={language} className="status-item neutral">
                          <div className="status-row">
                            <strong>{language}</strong>
                            <span>{detail.selected || t.unavailable}</span>
                          </div>
                          <small>{parserSummary(detail, locale)}</small>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">{t.noDiagnostics}</div>
                  )}
                </article>
              </div>
            </>
          ) : (
            <div className="empty-state">{t.noDiagnostics}</div>
          )}
        </article>

        <article className="panel-card">
          <div className="section-heading">
            <div>
              <h2>{t.activityTitle}</h2>
              <p className="section-copy">{t.activityHint}</p>
            </div>
            <span className="mini-pill">{t.lastSync}: {formatTimestamp(locale, smokeSyncAt)}</span>
          </div>

          <div className="subpanel-card inset">
            <div className="subpanel-head">
              <h3>{t.smokeSnapshot}</h3>
              <span className={`mini-pill ${toneForStatus(smokeData?.reranker_smoke?.status)}`}>
                {smokeData?.reranker_smoke?.status || t.unavailable}
              </span>
            </div>
            {smokeData ? (
              <div className="metric-grid small">
                <article className={`metric-card ${toneForStatus(smokeData.embedding_smoke?.status)}`}>
                  <span>{t.embedding}</span>
                  <strong>{smokeData.embedding_smoke?.status || t.unavailable}</strong>
                  <small>
                    {t.vectors}: {smokeData.embedding_smoke?.vector_count ?? 0} · {t.dimensions}:{" "}
                    {smokeData.embedding_smoke?.dimensions ?? 0}
                  </small>
                </article>
                <article className={`metric-card ${toneForStatus(smokeData.reranker_smoke?.status)}`}>
                  <span>{t.reranker}</span>
                  <strong>{smokeData.reranker_smoke?.status || t.unavailable}</strong>
                  <small>{t.score}: {smokeData.reranker_smoke?.score ?? t.unavailable}</small>
                </article>
                <article className="metric-card">
                  <span>{t.activeBefore}</span>
                  <strong>{smokeData.reranker_smoke?.active_model_before || t.unavailable}</strong>
                </article>
                <article className="metric-card">
                  <span>{t.activeAfter}</span>
                  <strong>{smokeData.reranker_smoke?.active_model_after || t.unavailable}</strong>
                </article>
              </div>
            ) : (
              <div className="empty-state">{t.noSmoke}</div>
            )}
          </div>

          <div className="subpanel-card inset">
            <div className="subpanel-head">
              <h3>{t.activityTitle}</h3>
              <span className="mini-pill">{activity.length}</span>
            </div>
            {activity.length > 0 ? (
              <div className="activity-list">
                {activity.map((item) => (
                  <article key={item.id} className="activity-item">
                    <div className="status-row">
                      <strong>{labelForAction(locale, item.action)}</strong>
                      <span>{formatTimestamp(locale, item.timestamp)}</span>
                    </div>
                    <p>{item.message}</p>
                  </article>
                ))}
              </div>
            ) : (
              <div className="empty-state">{t.noActivity}</div>
            )}
          </div>
        </article>
      </section>

      <section className="result-card">
        <div className="result-header">
          <h2>{resultTitle || t.resultTitle}</h2>
          <span className="result-chip">{resultBadge}</span>
        </div>
        <pre>{resultBody || t.emptyResult}</pre>
      </section>
    </main>
  );
}
