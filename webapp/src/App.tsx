import { useEffect, useMemo, useState } from "react";
import markUrl from "./assets/repobrain-mark.svg";

type Locale = "en" | "vi";
type Theme = "light" | "dark";
type QueryMode = "query" | "trace" | "impact" | "targets" | "multi";
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
  | "targets"
  | "multi"
  | "workspace-use"
  | "remember"
  | "clear-notes";

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

type WorkspaceProject = {
  name: string;
  repo_root: string;
  active: boolean;
  summary: string;
  manual_notes: string[];
  recent_queries: string[];
  top_files: string[];
  warnings: string[];
  next_questions: string[];
  updated_at: string;
};

type WorkspacePayload = {
  kind: "workspace_projects";
  message: string;
  current_repo: string;
  project_count: number;
  projects: WorkspaceProject[];
};

type WorkspaceSummary = {
  kind: "workspace_summary";
  message: string;
  name: string;
  repo_root: string;
  summary: string;
  manual_notes: string[];
  recent_queries: string[];
  top_files: string[];
  warnings: string[];
  next_questions: string[];
  updated_at: string;
};

type WorkspaceCitation = {
  file_path: string;
  language: string;
  role: string;
  score: number;
  start_line: number;
  end_line: number;
  symbol_name?: string | null;
  reasons: string[];
  preview: string;
};

type WorkspaceQueryResult = {
  name: string;
  repo_root: string;
  active: boolean;
  confidence: number;
  evidence_score: number;
  global_rank?: number | null;
  intent: string;
  top_files: string[];
  warnings: string[];
  summary: string;
  memory_summary: string;
  next_questions: string[];
  citations: WorkspaceCitation[];
};

type WorkspaceGlobalEvidenceHit = WorkspaceCitation & {
  name: string;
  repo_root: string;
  active: boolean;
  rank?: number | null;
};

type WorkspaceComparison = {
  best_match?: {
    name: string;
    repo_root: string;
    confidence: number;
    evidence_score: number;
    global_rank?: number | null;
    intent: string;
    summary: string;
  } | null;
  active_rank?: number | null;
  shared_hotspots?: Array<{
    label: string;
    count: number;
    repos: string[];
  }>;
  intent_groups?: Array<{
    intent: string;
    count: number;
    repos: string[];
  }>;
  global_evidence?: WorkspaceGlobalEvidenceHit[];
  notes?: string[];
};

type WorkspaceQueryData = {
  kind: "workspace_query";
  query: string;
  current_repo: string;
  project_count: number;
  results: WorkspaceQueryResult[];
  errors: Array<{
    name: string;
    repo_root: string;
    error: string;
  }>;
  context_applied: boolean;
  comparison: WorkspaceComparison;
};

type BootstrapPayload = {
  ok: boolean;
  active_repo: string;
  repo_input: string;
  report_url: string;
  locales: Locale[];
  default_mode: QueryMode;
  workspace: WorkspacePayload;
  summary: WorkspaceSummary | null;
};

type ActionPayload = {
  ok: boolean;
  active_repo: string;
  repo_input: string;
  message: string;
  title: string;
  result: string;
  report_url?: string;
  data?: DoctorData | ProviderSmokeData | WorkspaceQueryData | null;
  workspace?: WorkspacePayload;
  summary?: WorkspaceSummary | null;
};

type ActivityEntry = {
  id: number;
  action: ActionKind;
  message: string;
  timestamp: string;
};

const copy = {
  en: {
    brand: "RepoBrain",
    subtitle:
      "Local-first codebase memory for indexing one project, tracing real flows, and ranking safer edit targets with evidence.",
    language: "Language",
    theme: "Theme",
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
      "Import initializes RepoBrain state, stores the repo in the shared workspace, and builds the local index in one step.",
    actionsTitle: "Active repo actions",
    actionsHint:
      "Use Review for gaps, Ship Gate for a release verdict, Baseline for drift tracking, and Provider Smoke for direct model checks.",
    index: "Re-index active repo",
    review: "Scan project review",
    ship: "Ship gate",
    baseline: "Save baseline",
    providerSmoke: "Provider smoke",
    doctor: "Doctor",
    openReport: "Open report",
    queryTitle: "Grounded question",
    mode: "Mode",
    question: "Question",
    questionPlaceholder: "Where is payment retry logic implemented?",
    run: "Run",
    resultTitle: "Result",
    crossRepoOverview: "Cross-repo overview",
    bestMatch: "Best match",
    activeRank: "Active rank",
    sharedHotspots: "Shared hotspots",
    comparisonNotes: "Comparison notes",
    evidenceLeaders: "Evidence leaders",
    citationScore: "Citation score",
    globalRank: "Global rank",
    citations: "Citations",
    repoMemory: "Repo memory",
    rawTranscript: "Raw transcript",
    workspaceErrors: "Workspace errors",
    emptyResult:
      "No result yet. Import a repo, then run review, doctor, provider smoke, or a grounded question.",
    loading: "Working...",
    queryMode: "Query",
    traceMode: "Trace",
    impactMode: "Impact",
    targetsMode: "Targets",
    multiMode: "Cross-repo",
    interfaceStatus: "Interface status",
    localOnly: "Local-only browser UI",
    localOnlyHint:
      "The browser app talks to your local RepoBrain Python server only. No hosted backend is required.",
    reportHint:
      "Single-repo queries automatically reuse stored repo memory. Use Cross-repo mode to compare evidence across all tracked projects.",
    diagnosticsTitle: "Release diagnostics",
    diagnosticsHint:
      "Doctor posture and provider smoke stay visible here so release checks do not depend on scrolling through raw text output.",
    activityTitle: "Recent activity",
    activityHint: "RepoBrain keeps a short local timeline of what you just ran in this browser tab.",
    workspaceTitle: "Workspace control",
    workspaceHint:
      "Imported repos stay tracked here. Switch active repos instantly and keep asking without losing the main thread.",
    memoryTitle: "Repo memory",
    memoryHint:
      "Store a few key notes, then let RepoBrain carry the summary, hot files, and follow-up threads into the next question.",
    rememberNote: "Memory note",
    notePlaceholder: "Auth callback is the critical integration thread.",
    saveNote: "Save note",
    clearNotes: "Clear notes",
    useRepo: "Use repo",
    activeLabel: "Active",
    noSummary: "No stored summary yet.",
    manualNotes: "Manual notes",
    recentAsks: "Recent asks",
    hotFiles: "Hot files",
    nextThread: "Next thread",
    updatedAt: "Updated",
    noWorkspace: "No tracked repos yet. Import the first project to start a continuous workspace.",
    noDiagnostics: "Run Doctor after import to populate structured release diagnostics.",
    noSmoke: "Run Provider Smoke to see active models, failover state, and direct provider health here.",
    noActivity: "No activity yet in this session.",
    indexed: "Indexed",
    files: "Files",
    chunks: "Chunks",
    embedding: "Embedding",
    reranker: "Reranker",
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
    disabledUntilImport: "Import a repo to unlock actions, memory, and grounded queries.",
  },
  vi: {
    brand: "RepoBrain",
    subtitle:
      "Bo nho codebase local-first de index nhieu du an, trace dung flow, va xep hang edit target an toan hon dua tren evidence.",
    language: "Ngon ngu",
    theme: "Giao dien",
    light: "Sang",
    dark: "Toi",
    activeRepo: "Repo dang active",
    none: "Chua co",
    noActiveRepo: "Chua co repo active. Hay import duong dan du an o ben duoi.",
    importTitle: "Import nhanh",
    projectPath: "Duong dan du an",
    projectPathPlaceholder: "C:\\duong-dan\\toi\\du-an-cua-ban",
    importButton: "Import + Index",
    importHint:
      "Import se tao state RepoBrain, them repo vao workspace chung, va build local index trong mot buoc.",
    actionsTitle: "Tac vu tren repo active",
    actionsHint:
      "Dung Review de xem gap, Ship Gate de xem verdict release, Baseline de track drift, va Provider Smoke de check model.",
    index: "Index lai repo active",
    review: "Quet project review",
    ship: "Ship gate",
    baseline: "Luu baseline",
    providerSmoke: "Smoke provider",
    doctor: "Doctor",
    openReport: "Mo report",
    queryTitle: "Cau hoi grounded",
    mode: "Che do",
    question: "Cau hoi",
    questionPlaceholder: "Logic payment retry nam o dau?",
    run: "Chay",
    resultTitle: "Ket qua",
    crossRepoOverview: "Tong quan da repo",
    bestMatch: "Repo dan dau",
    activeRank: "Hang repo active",
    sharedHotspots: "Hotspot chung",
    comparisonNotes: "Ghi chu so sanh",
    evidenceLeaders: "Evidence dan dau",
    citationScore: "Diem citation",
    globalRank: "Hang toan workspace",
    citations: "Citation",
    repoMemory: "Bo nho repo",
    rawTranscript: "Ban raw",
    workspaceErrors: "Loi workspace",
    emptyResult:
      "Chua co ket qua. Hay import repo, sau do chay review, doctor, provider smoke, hoac mot cau hoi grounded.",
    loading: "Dang xu ly...",
    queryMode: "Query",
    traceMode: "Trace",
    impactMode: "Impact",
    targetsMode: "Targets",
    multiMode: "Da repo",
    interfaceStatus: "Trang thai giao dien",
    localOnly: "Giao dien browser chi chay local",
    localOnlyHint:
      "Ung dung browser nay chi goi toi RepoBrain Python server dang chay local cua ban. Khong can hosted backend.",
    reportHint:
      "Query mot repo se tu dong tai su dung repo memory da luu. Dung Da repo de so sanh evidence tren tat ca project da track.",
    diagnosticsTitle: "Diagnostics cho release",
    diagnosticsHint:
      "Doctor posture va provider smoke duoc giu o day de luc release khong phai doc lai ca khoi text dai.",
    activityTitle: "Hoat dong gan day",
    activityHint: "RepoBrain giu mot timeline ngan cho nhung tac vu ban vua chay trong tab nay.",
    workspaceTitle: "Dieu khien workspace",
    workspaceHint:
      "Cac repo da import se duoc track tai day. Co the doi repo active ngay va hoi tiep ma khong mat mach.",
    memoryTitle: "Repo memory",
    memoryHint:
      "Luu vai ghi chu quan trong, sau do de RepoBrain giu summary, hot files, va next thread cho lan hoi tiep theo.",
    rememberNote: "Ghi chu memory",
    notePlaceholder: "Auth callback la thread tich hop quan trong.",
    saveNote: "Luu ghi chu",
    clearNotes: "Xoa ghi chu",
    useRepo: "Dung repo",
    activeLabel: "Dang active",
    noSummary: "Chua co summary da luu.",
    manualNotes: "Ghi chu tay",
    recentAsks: "Cau hoi gan day",
    hotFiles: "Hot files",
    nextThread: "Luong tiep theo",
    updatedAt: "Cap nhat",
    noWorkspace: "Chua co repo nao duoc track. Hay import project dau tien de bat dau workspace lien tuc.",
    noDiagnostics: "Hay chay Doctor sau khi import de do du lieu diagnostics co cau truc.",
    noSmoke: "Hay chay Provider Smoke de xem model active, failover state, va suc khoe provider tai day.",
    noActivity: "Chua co hoat dong nao trong session nay.",
    indexed: "Da index",
    files: "Files",
    chunks: "Chunks",
    embedding: "Embedding",
    reranker: "Reranker",
    fallbackPool: "Pool fallback Gemini",
    singleModel: "Che do mot model",
    failover: "Failover gan nhat",
    remoteProviders: "Provider tu xa",
    networkRequired: "Can mang",
    localStorageOnly: "Chi luu local",
    parserPosture: "Trang thai parser",
    providerPosture: "Trang thai provider",
    warnings: "Canh bao",
    noWarnings: "Khong co canh bao",
    status: "Trang thai",
    score: "Diem",
    vectors: "Vectors",
    dimensions: "Chieu",
    activeBefore: "Model truoc",
    activeAfter: "Model sau",
    lastSync: "Lan dong bo",
    unavailable: "Chua co",
    yes: "Co",
    no: "Khong",
    ready: "San sang",
    notReady: "Chua san sang",
    disabledUntilImport: "Hay import repo truoc de mo khoa action, memory, va grounded query.",
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
    case "multi":
      return t.multiMode;
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
    case "workspace-use":
      return t.useRepo;
    case "remember":
      return t.saveNote;
    case "clear-notes":
      return t.clearNotes;
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
  return `${selected} | fallback ${fallback ? "on" : "off"}`;
}

function hasSummaryField(payload: ActionPayload): payload is ActionPayload & { summary: WorkspaceSummary | null } {
  return Object.prototype.hasOwnProperty.call(payload, "summary");
}

function isWorkspaceQueryData(data: ActionPayload["data"]): data is WorkspaceQueryData {
  return Boolean(data && typeof data === "object" && "kind" in data && data.kind === "workspace_query");
}

export function App() {
  const [locale, setLocale] = useLocale();
  const [theme, setTheme] = useTheme();
  const [boot, setBoot] = useState<BootstrapPayload | null>(null);
  const [workspace, setWorkspace] = useState<WorkspacePayload | null>(null);
  const [summary, setSummary] = useState<WorkspaceSummary | null>(null);
  const [repoPath, setRepoPath] = useState("");
  const [query, setQuery] = useState("Where is payment retry logic implemented?");
  const [mode, setMode] = useState<QueryMode>("query");
  const [note, setNote] = useState("");
  const [message, setMessage] = useState("");
  const [resultTitle, setResultTitle] = useState("");
  const [resultBody, setResultBody] = useState("");
  const [resultAction, setResultAction] = useState<ActionKind>("query");
  const [resultData, setResultData] = useState<ActionPayload["data"] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [doctorData, setDoctorData] = useState<DoctorData | null>(null);
  const [smokeData, setSmokeData] = useState<ProviderSmokeData | null>(null);
  const [doctorSyncAt, setDoctorSyncAt] = useState<string | null>(null);
  const [smokeSyncAt, setSmokeSyncAt] = useState<string | null>(null);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);

  const t = copy[locale];
  const activeRepo = workspace?.current_repo || boot?.active_repo || "";
  const reportUrl = boot?.report_url || "/report";
  const hasActiveRepo = Boolean(activeRepo);

  useEffect(() => {
    void (async () => {
      const payload = await readJson<BootstrapPayload>("/api/bootstrap");
      setBoot(payload);
      setWorkspace(payload.workspace);
      setSummary(payload.summary ?? null);
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
      if (payload.workspace) {
        setWorkspace(payload.workspace);
      }
      if (hasSummaryField(payload)) {
        setSummary(payload.summary ?? null);
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
      workspace: payload.workspace || current?.workspace || workspace || { kind: "workspace_projects", message: "", current_repo: payload.active_repo, project_count: 0, projects: [] },
      summary:
        hasSummaryField(payload)
          ? payload.summary ?? null
          : current?.summary ?? summary ?? null,
    }));
    setRepoPath(payload.repo_input || payload.active_repo || "");
  }

  function syncWorkspace(payload: ActionPayload) {
    if (payload.workspace) {
      setWorkspace(payload.workspace);
    }
    if (hasSummaryField(payload)) {
      setSummary(payload.summary ?? null);
    }
  }

  function appendActivity(action: ActionKind, messageText: string) {
    const entry: ActivityEntry = {
      id: Date.now(),
      action,
      message: messageText,
      timestamp: new Date().toISOString(),
    };
    setActivity((current) => [entry, ...current].slice(0, 8));
  }

  function applyPayload(action: ActionKind, payload: ActionPayload) {
    syncBoot(payload);
    syncWorkspace(payload);
    setMessage(payload.message);
    setResultTitle(payload.title);
    setResultBody(payload.result);
    setResultAction(action);
    setResultData(payload.data ?? null);
    appendActivity(action, payload.message);

    if (action === "doctor" && payload.data) {
      setDoctorData(payload.data as DoctorData);
      setDoctorSyncAt(new Date().toISOString());
    }
    if (action === "provider-smoke" && payload.data) {
      setSmokeData(payload.data as ProviderSmokeData);
      setSmokeSyncAt(new Date().toISOString());
    }
    if (action === "import" || action === "index" || action === "workspace-use") {
      void refreshDoctorSnapshot();
    }
    if (action === "remember") {
      setNote("");
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
      const queryAction: ActionKind =
        mode === "query" ? "query" : mode === "multi" ? "multi" : mode;
      applyPayload(queryAction, payload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  async function handleWorkspaceUse(project: string) {
    try {
      setBusy("workspace-use");
      const payload = await readJson<ActionPayload>("/api/workspace/use", {
        method: "POST",
        body: JSON.stringify({ project }),
      });
      applyPayload("workspace-use", payload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  async function handleRemember(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setBusy("remember");
      const payload = await readJson<ActionPayload>("/api/workspace/remember", {
        method: "POST",
        body: JSON.stringify({ note }),
      });
      applyPayload("remember", payload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  async function handleClearNotes() {
    try {
      setBusy("clear-notes");
      const payload = await readJson<ActionPayload>("/api/workspace/clear-notes", {
        method: "POST",
        body: JSON.stringify({}),
      });
      applyPayload("clear-notes", payload);
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
  const workspaceProjects = workspace?.projects || [];
  const summaryBlocks = [
    { title: t.manualNotes, items: summary?.manual_notes || [] },
    { title: t.recentAsks, items: summary?.recent_queries || [] },
    { title: t.hotFiles, items: summary?.top_files || [] },
    { title: t.nextThread, items: summary?.next_questions || [] },
  ];
  const workspaceQueryData = resultAction === "multi" && isWorkspaceQueryData(resultData) ? resultData : null;
  const comparison = workspaceQueryData?.comparison;
  const bestMatch = comparison?.best_match ?? null;
  const sharedHotspots = comparison?.shared_hotspots || [];
  const comparisonNotes = comparison?.notes || [];
  const globalEvidence = comparison?.global_evidence || [];
  const workspaceErrors = workspaceQueryData?.errors || [];

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
          <div className="brand-lockup">
            <img className="brand-mark" src={markUrl} alt="RepoBrain mark" />
            <div className="brand-copy">
              <span className="brand-kicker">grounded codebase memory</span>
              <h1 className="brand-wordmark" aria-label={t.brand}>
                <span className="brand-word brand-word-repo">Repo</span>
                <span className="brand-word brand-word-brain">Brain</span>
              </h1>
              <p className="lead">{t.subtitle}</p>
            </div>
          </div>
          <div className="brand-rail" aria-label="RepoBrain capabilities">
            <span className="rail-pill">{labelForAction(locale, "query")}</span>
            <span className="rail-pill">{labelForAction(locale, "trace")}</span>
            <span className="rail-pill">{labelForAction(locale, "multi")}</span>
            <span className="rail-pill">{t.review}</span>
            <span className="rail-pill">{t.ship}</span>
          </div>
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
            <select id="modeSelect" value={mode} onChange={(event) => setMode(event.target.value as QueryMode)}>
              <option value="query">{labelForAction(locale, "query")}</option>
              <option value="trace">{labelForAction(locale, "trace")}</option>
              <option value="impact">{labelForAction(locale, "impact")}</option>
              <option value="targets">{labelForAction(locale, "targets")}</option>
              <option value="multi">{labelForAction(locale, "multi")}</option>
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

      <section className="memory-grid">
        <article className="panel-card">
          <div className="section-heading">
            <div>
              <h2>{t.workspaceTitle}</h2>
              <p className="section-copy">{t.workspaceHint}</p>
            </div>
            <span className="mini-pill">{workspaceProjects.length}</span>
          </div>
          {workspaceProjects.length > 0 ? (
            <div className="status-list">
              {workspaceProjects.map((project) => (
                <article key={project.repo_root} className={`status-item ${project.active ? "good" : "neutral"}`}>
                  <div className="status-row">
                    <strong>
                      {project.name}
                      {project.active ? ` · ${t.activeLabel}` : ""}
                    </strong>
                    <button
                      className="ghost-button small-button"
                      disabled={project.active || busy === "workspace-use"}
                      onClick={() => void handleWorkspaceUse(project.repo_root)}
                      type="button"
                    >
                      {busy === "workspace-use" && !project.active ? t.loading : t.useRepo}
                    </button>
                  </div>
                  <p>{project.repo_root}</p>
                  <small>{project.summary || t.noSummary}</small>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">{t.noWorkspace}</div>
          )}
        </article>

        <article className="panel-card">
          <div className="section-heading">
            <div>
              <h2>{t.memoryTitle}</h2>
              <p className="section-copy">{t.memoryHint}</p>
            </div>
            <span className="mini-pill">
              {t.updatedAt}: {formatTimestamp(locale, summary?.updated_at || null)}
            </span>
          </div>
          <p className="muted-copy">{summary?.summary || t.noSummary}</p>
          <form className="panel-form" onSubmit={handleRemember}>
            <label htmlFor="memoryNote">{t.rememberNote}</label>
            <textarea
              id="memoryNote"
              placeholder={t.notePlaceholder}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              disabled={!hasActiveRepo}
            />
            <div className="memory-form-row">
              <button className="primary-button" disabled={!hasActiveRepo || busy === "remember" || !note.trim()} type="submit">
                {busy === "remember" ? t.loading : t.saveNote}
              </button>
              <button
                className="outline-button"
                disabled={!hasActiveRepo || busy === "clear-notes"}
                onClick={() => void handleClearNotes()}
                type="button"
              >
                {busy === "clear-notes" ? t.loading : t.clearNotes}
              </button>
            </div>
          </form>
          <div className="memory-stack">
            {summaryBlocks.map((block) => (
              <article key={block.title} className="subpanel-card inset">
                <div className="subpanel-head">
                  <h3>{block.title}</h3>
                  <span className="mini-pill">{block.items.length}</span>
                </div>
                {block.items.length > 0 ? (
                  <ul className="summary-list">
                    {block.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="empty-state compact-empty">{t.noSummary}</div>
                )}
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="status-grid">
        <article className="panel-card">
          <div className="section-heading">
            <div>
              <h2>{t.diagnosticsTitle}</h2>
              <p className="section-copy">{t.diagnosticsHint}</p>
            </div>
            <span className="mini-pill">
              {t.lastSync}: {formatTimestamp(locale, doctorSyncAt)}
            </span>
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
                  <p>
                    {t.failover}: {lastFailoverText}
                  </p>
                </article>
                <article className="compact-card">
                  <span className="eyebrow">{t.remoteProviders}</span>
                  <strong>{yesNo(locale, doctorData.security?.remote_providers_enabled)}</strong>
                  <p>
                    {t.networkRequired}: {yesNo(locale, doctorData.security?.network_required)}
                  </p>
                </article>
                <article className="compact-card">
                  <span className="eyebrow">{t.localStorageOnly}</span>
                  <strong>{yesNo(locale, doctorData.security?.local_storage_only)}</strong>
                  <p>
                    {t.parserPosture}: {parserEntries.length || 0}
                  </p>
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
                            {t.status}: {detail.ready ? t.ready : t.notReady} | {t.networkRequired}:{" "}
                            {yesNo(locale, detail.requires_network)}
                          </p>
                          <small>
                            {t.warnings}: {formatWarnings(locale, detail.warnings)}
                          </small>
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
            <span className="mini-pill">
              {t.lastSync}: {formatTimestamp(locale, smokeSyncAt)}
            </span>
          </div>

          <div className="subpanel-card inset">
            <div className="subpanel-head">
              <h3>{t.providerSmoke}</h3>
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
                    {t.vectors}: {smokeData.embedding_smoke?.vector_count ?? 0} | {t.dimensions}:{" "}
                    {smokeData.embedding_smoke?.dimensions ?? 0}
                  </small>
                </article>
                <article className={`metric-card ${toneForStatus(smokeData.reranker_smoke?.status)}`}>
                  <span>{t.reranker}</span>
                  <strong>{smokeData.reranker_smoke?.status || t.unavailable}</strong>
                  <small>
                    {t.score}: {smokeData.reranker_smoke?.score ?? t.unavailable}
                  </small>
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
        {workspaceQueryData ? (
          <div className="result-stack">
            <div className="compact-grid result-summary-grid">
              <article className="compact-card">
                <span>{t.bestMatch}</span>
                <strong>{bestMatch?.name || t.unavailable}</strong>
                <p>
                  {bestMatch
                    ? `#${bestMatch.global_rank ?? "?"} | ${bestMatch.intent} | ${bestMatch.evidence_score.toFixed(3)}`
                    : t.noSummary}
                </p>
              </article>
              <article className="compact-card">
                <span>{t.citationScore}</span>
                <strong>{bestMatch?.evidence_score?.toFixed(3) || t.unavailable}</strong>
                <p>{bestMatch?.summary || t.noSummary}</p>
              </article>
              <article className="compact-card">
                <span>{t.activeRank}</span>
                <strong>{comparison?.active_rank ?? t.unavailable}</strong>
                <p>
                  {workspaceQueryData.current_repo || t.none}
                </p>
              </article>
            </div>

            <div className="subpanel-grid result-summary-grid">
              <article className="subpanel-card">
                <div className="subpanel-head">
                  <h3>{t.comparisonNotes}</h3>
                  <span className="mini-pill">{comparisonNotes.length}</span>
                </div>
                {comparisonNotes.length > 0 ? (
                  <ul className="summary-list">
                    {comparisonNotes.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="empty-state compact-empty">{t.noSummary}</div>
                )}
              </article>

              <article className="subpanel-card">
                <div className="subpanel-head">
                  <h3>{t.evidenceLeaders}</h3>
                  <span className="mini-pill">{globalEvidence.length}</span>
                </div>
                {globalEvidence.length > 0 ? (
                  <div className="citation-list">
                    {globalEvidence.map((citation) => (
                      <article
                        key={`${citation.repo_root}:${citation.file_path}:${citation.start_line}:${citation.end_line}:${citation.rank}`}
                        className="citation-item"
                      >
                        <div className="citation-meta">
                          <strong className="citation-path">
                            #{citation.rank ?? "?"} {citation.name}
                            {citation.active ? ` · ${t.activeLabel}` : ""} · {citation.file_path}:{citation.start_line}-
                            {citation.end_line}
                            {citation.symbol_name ? `::${citation.symbol_name}` : ""}
                          </strong>
                          <span>{citation.score.toFixed(3)}</span>
                        </div>
                        <p className="citation-preview">{citation.preview || t.noSummary}</p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state compact-empty">{t.noWarnings}</div>
                )}
              </article>

              <article className="subpanel-card">
                <div className="subpanel-head">
                  <h3>{t.sharedHotspots}</h3>
                  <span className="mini-pill">{sharedHotspots.length}</span>
                </div>
                {sharedHotspots.length > 0 ? (
                  <ul className="summary-list">
                    {sharedHotspots.map((item) => (
                      <li key={`${item.label}:${item.count}`}>
                        {item.label} · {item.count} repo · {item.repos.join(" | ")}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="empty-state compact-empty">{t.noWarnings}</div>
                )}
              </article>

              <article className="subpanel-card">
                <div className="subpanel-head">
                  <h3>{t.workspaceErrors}</h3>
                  <span className="mini-pill">{workspaceErrors.length}</span>
                </div>
                {workspaceErrors.length > 0 ? (
                  <div className="status-list">
                    {workspaceErrors.map((item) => (
                      <article key={`${item.repo_root}:${item.error}`} className="status-item bad">
                        <div className="status-row">
                          <strong>{item.name}</strong>
                          <span>{item.repo_root}</span>
                        </div>
                        <p>{item.error}</p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state compact-empty">{t.noWarnings}</div>
                )}
              </article>
            </div>

            <div className="status-list result-workspace-list">
              {workspaceQueryData.results.map((item) => (
                <article key={item.repo_root} className={`status-item ${item.active ? "good" : "neutral"}`}>
                  <div className="status-row">
                    <strong>
                      {item.name}
                      {item.active ? ` · ${t.activeLabel}` : ""}
                    </strong>
                    <span>
                      #{item.global_rank ?? "?"} | {item.intent} | {item.evidence_score.toFixed(3)} /{" "}
                      {item.confidence.toFixed(3)}
                    </span>
                  </div>
                  <p>{item.summary}</p>
                  <small>{item.repo_root}</small>
                  {item.memory_summary ? (
                    <div className="inline-pills">
                      <span className="inline-pill">{t.repoMemory}</span>
                      <span className="inline-pill neutral">{item.memory_summary}</span>
                    </div>
                  ) : null}
                  {item.citations.length > 0 ? (
                    <div className="citation-list">
                      {item.citations.map((citation) => (
                        <article
                          key={`${item.repo_root}:${citation.file_path}:${citation.start_line}:${citation.end_line}`}
                          className="citation-item"
                        >
                          <div className="citation-meta">
                            <strong className="citation-path">
                              {citation.file_path}:{citation.start_line}-{citation.end_line}
                              {citation.symbol_name ? `::${citation.symbol_name}` : ""}
                            </strong>
                            <span>{citation.score.toFixed(3)}</span>
                          </div>
                          <p className="citation-preview">{citation.preview || t.noSummary}</p>
                        </article>
                      ))}
                    </div>
                  ) : null}
                  {item.top_files.length > 0 ? (
                    <div className="result-meta-block">
                      <span className="eyebrow">{t.hotFiles}</span>
                      <ul className="summary-list">
                        {item.top_files.map((path) => (
                          <li key={path}>{path}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {item.next_questions.length > 0 ? (
                    <div className="result-meta-block">
                      <span className="eyebrow">{t.nextThread}</span>
                      <ul className="summary-list">
                        {item.next_questions.map((questionText) => (
                          <li key={questionText}>{questionText}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </article>
              ))}
            </div>

            <article className="subpanel-card inset">
              <div className="subpanel-head">
                <h3>{t.rawTranscript}</h3>
                <span className="mini-pill">{workspaceQueryData.results.length}</span>
              </div>
              <pre>{resultBody || t.emptyResult}</pre>
            </article>
          </div>
        ) : (
          <pre>{resultBody || t.emptyResult}</pre>
        )}
      </section>
    </main>
  );
}
