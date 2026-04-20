import { useEffect, useMemo, useState } from "react";
import markUrl from "./assets/repobrain-mark.svg";

type Locale = "en" | "vi" | "zh";
type Theme = "light" | "dark";
type QueryMode = "query" | "trace" | "impact" | "targets" | "multi";
type ActionKind =
  | "import"
  | "index"
  | "patch-review"
  | "review"
  | "ship"
  | "baseline"
  | "provider-smoke"
  | "doctor"
  | "gemini-config"
  | "groq-config"
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

type FileContextItem = {
  file_path: string;
  source: string;
  role: string;
  score?: number | null;
  reason: string;
  improvement: string;
  line_range?: string;
};

type FileContext = {
  kind: "file_context";
  action: string;
  summary: string;
  files: FileContextItem[];
  warnings: string[];
  next_steps: string[];
  memory_updated?: boolean;
  memory_summary?: string;
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

type SelectFolderPayload = {
  ok: boolean;
  repo_path: string;
  message: string;
};

type ActionPayload = {
  ok: boolean;
  active_repo: string;
  repo_input: string;
  message: string;
  title: string;
  result: string;
  report_url?: string;
  data?: DoctorData | ProviderSmokeData | WorkspaceQueryData | Record<string, unknown> | null;
  file_context?: FileContext | null;
  workspace?: WorkspacePayload;
  summary?: WorkspaceSummary | null;
};

type ActivityEntry = {
  id: number;
  action: ActionKind;
  message: string;
  timestamp: string;
};

type QueryPreset = {
  id: number;
  label: string;
  query: string;
  mode: QueryMode;
};

const baseCopy = {
  en: {
    brand: "RepoBrain",
    subtitle:
      "A local code intelligence workbench for importing repos, asking grounded questions, reviewing patches, and preparing releases.",
    language: "Language",
    theme: "Theme",
    light: "Light",
    dark: "Dark",
    activeRepo: "Active repo",
    none: "None",
    noActiveRepo: "No active repo yet. Import a project path below.",
    importTitle: "Project setup",
    projectPath: "Project path",
    projectPathPlaceholder: "C:\\path\\to\\your-project",
    chooseFolder: "Choose folder",
    importButton: "Import + Index",
    importHint:
      "Choose a local folder or paste a path. Import initializes RepoBrain state, stores the repo in the shared workspace, and builds the local index in one step.",
    actionsTitle: "Workflow actions",
    actionsHint:
      "Run the core checks from one place: re-index after changes, review risks, score ship readiness, save baselines, and verify providers.",
    index: "Re-index active repo",
    patchReview: "Patch review",
    patchReviewTitle: "Patch review guardrail",
    patchReviewHint:
      "Review the current patch, compare against a base ref, or inspect an explicit file list without leaving the browser UI.",
    patchBase: "Base ref",
    patchBasePlaceholder: "main",
    patchFiles: "Files",
    patchFilesPlaceholder: "backend/app/api/auth.py\nbackend/app/services/auth_service.py",
    patchReviewRun: "Run patch review",
    review: "Project review",
    ship: "Ship readiness",
    baseline: "Save baseline",
    providerSmoke: "Provider smoke",
    geminiSetup: "Gemini setup",
    geminiSetupHint:
      "Save a Gemini API key and model pool into the active repo for Docker or local runs.",
    geminiApiKey: "Gemini API key",
    geminiApiKeyPlaceholder: "AIza...",
    geminiModelPool: "Gemini model pool",
    geminiModelPoolPlaceholder: "gemini-2.5-flash,gemini-2.5-flash-lite,gemini-3-flash-preview",
    useGeminiEmbedding: "Use Gemini embedding",
    useGeminiReranker: "Use Gemini reranker",
    saveGeminiConfig: "Save Gemini config",
    groqSetup: "Groq setup",
    groqSetupHint:
      "Save a Groq API key and reranker model pool while keeping embeddings local.",
    groqApiKey: "Groq API key",
    groqApiKeyPlaceholder: "gsk_...",
    groqModelPool: "Groq model pool",
    groqModelPoolPlaceholder: "llama-3.3-70b-versatile,openai/gpt-oss-20b",
    useGroqReranker: "Use Groq reranker",
    saveGroqConfig: "Save Groq config",
    doctor: "Health check",
    openReport: "Open report",
    exportMarkdown: "Export .md",
    queryTitle: "Chat Query",
    mode: "Mode",
    question: "Question",
    questionPlaceholder: "Where is payment retry logic implemented?",
    run: "Run",
    presetsTitle: "Saved query presets",
    presetsHint: "Keep reusable prompts with mode attached, then load them in one click.",
    presetName: "Preset name",
    presetNamePlaceholder: "Auth callback trace",
    savePreset: "Save preset",
    noPresets: "No saved presets yet.",
    removePreset: "Remove",
    resultTitle: "Evidence result",
    focusTitle: "Start here",
    focusImportLabel: "Import project",
    focusImportHint: "Paste or choose your project folder, then run Import + Index.",
    focusQueryLabel: "Chat query",
    focusQueryHint: "Ask a question and switch mode when you need trace, impact, or targets.",
    focusAdvancedLabel: "Advanced tools",
    focusAdvancedHint: "Open patch review, ship checks, provider config, and repo memory panels.",
    showAdvanced: "Show advanced tools",
    hideAdvanced: "Hide advanced tools",
    crossRepoOverview: "Cross-repo overview",
    bestMatch: "Best match",
    activeRank: "Active rank",
    sharedHotspots: "Shared hotspots",
    comparisonNotes: "Comparison notes",
    evidenceLeaders: "Evidence leaders",
    citationScore: "Citation score",
    globalRank: "Global rank",
    citations: "Citations",
    autoFiles: "Auto-attached files",
    autoFilesHint:
      "RepoBrain found concrete files in this result, added them to repo memory, and ranked what to inspect next.",
    improve: "Improve",
    source: "Source",
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
    localOnly: "Local workbench",
    localOnlyHint:
      "The browser app talks to your local RepoBrain Python server only. No hosted backend is required.",
    reportHint:
      "Single-repo queries automatically reuse stored repo memory. Use Cross-repo mode to compare evidence across all tracked projects.",
    diagnosticsTitle: "Health and providers",
    diagnosticsHint:
      "Doctor posture and provider smoke stay visible here so release checks do not depend on scrolling through raw text output.",
    activityTitle: "Recent activity",
    activityHint: "RepoBrain keeps a short local timeline of what you just ran in this browser tab.",
    workspaceTitle: "Workspace",
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
    newcomerTitle: "Recommended workflow",
    newcomerHint:
      "RepoBrain is easier when the first run follows one path: import, ask, then review. The interface now keeps the next file context visible instead of hiding it in raw text.",
    newcomerImport: "Import + Index",
    newcomerImportHint: "Build the local map first so every result can cite real files.",
    newcomerAsk: "Ask or trace",
    newcomerAskHint: "Use Query for location, Trace for flows, Impact for blast radius, and Targets for edit planning.",
    newcomerReview: "Review with context",
    newcomerReviewHint: "Auto-attached files show what to open next and how to improve the patch.",
    footerTitle: "RepoBrain Workbench",
    footerBody: "Everything here talks to your local RepoBrain server and keeps project memory on this machine.",
    footerPrimary: "Start with Import + Index",
    footerSecondary: "Then run Patch Review",
    indexed: "Indexed",
    files: "Files",
    chunks: "Chunks",
    embedding: "Embedding",
    reranker: "Reranker",
    fallbackPool: "Reranker model pool",
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
    disabledUntilImport: "Import a repo to unlock checks, memory, and grounded queries.",
  },
  vi: {
    brand: "RepoBrain",
    subtitle:
      "Workbench phan tich code chay local de import repo, hoi co evidence, review patch, va chuan bi release.",
    language: "Ngon ngu",
    theme: "Giao dien",
    light: "Sang",
    dark: "Toi",
    activeRepo: "Repo dang active",
    none: "Chua co",
    noActiveRepo: "Chua co repo active. Hay import duong dan du an o ben duoi.",
    importTitle: "Thiet lap project",
    projectPath: "Duong dan du an",
    projectPathPlaceholder: "C:\\duong-dan\\toi\\du-an-cua-ban",
    chooseFolder: "Chon folder",
    importButton: "Import + Index",
    importHint:
      "Chon folder local hoac dan duong dan. Import se tao state RepoBrain, them repo vao workspace chung, va build local index trong mot buoc.",
    actionsTitle: "Workflow actions",
    actionsHint:
      "Chay cac check chinh o mot noi: index lai sau thay doi, review risk, cham diem ship readiness, luu baseline, va kiem tra provider.",
    index: "Index lai repo active",
    patchReview: "Patch review",
    patchReviewTitle: "Guardrail cho patch",
    patchReviewHint:
      "Review patch hien tai, so sanh voi base ref, hoac inspect mot danh sach file ro rang ngay trong browser UI.",
    patchBase: "Base ref",
    patchBasePlaceholder: "main",
    patchFiles: "Danh sach file",
    patchFilesPlaceholder: "backend/app/api/auth.py\nbackend/app/services/auth_service.py",
    patchReviewRun: "Chay patch review",
    review: "Project review",
    ship: "Ship readiness",
    baseline: "Luu baseline",
    providerSmoke: "Smoke provider",
    geminiSetup: "Cau hinh Gemini",
    geminiSetupHint:
      "Luu Gemini API key va model pool vao repo active de chay bang Docker hoac local.",
    geminiApiKey: "Gemini API key",
    geminiApiKeyPlaceholder: "AIza...",
    geminiModelPool: "Pool model Gemini",
    geminiModelPoolPlaceholder: "gemini-2.5-flash,gemini-2.5-flash-lite,gemini-3-flash-preview",
    useGeminiEmbedding: "Dung embedding Gemini",
    useGeminiReranker: "Dung reranker Gemini",
    saveGeminiConfig: "Luu cau hinh Gemini",
    groqSetup: "Cau hinh Groq",
    groqSetupHint:
      "Luu Groq API key va pool model reranker, trong khi embedding van chay local.",
    groqApiKey: "Groq API key",
    groqApiKeyPlaceholder: "gsk_...",
    groqModelPool: "Pool model Groq",
    groqModelPoolPlaceholder: "llama-3.3-70b-versatile,openai/gpt-oss-20b",
    useGroqReranker: "Dung reranker Groq",
    saveGroqConfig: "Luu cau hinh Groq",
    doctor: "Health check",
    openReport: "Mo report",
    queryTitle: "Chat Query",
    mode: "Che do",
    question: "Cau hoi",
    questionPlaceholder: "Logic payment retry nam o dau?",
    run: "Chay",
    resultTitle: "Ket qua evidence",
    focusTitle: "Bat dau tai day",
    focusImportLabel: "Import project",
    focusImportHint: "Dan duong dan hoac chon folder project, sau do bam Import + Index.",
    focusQueryLabel: "Chat query",
    focusQueryHint: "Dat cau hoi va doi mode khi can trace, impact, hoac targets.",
    focusAdvancedLabel: "Cong cu nang cao",
    focusAdvancedHint: "Mo patch review, ship checks, cau hinh provider, va panel repo memory.",
    showAdvanced: "Mo cong cu nang cao",
    hideAdvanced: "An cong cu nang cao",
    crossRepoOverview: "Tong quan da repo",
    bestMatch: "Repo dan dau",
    activeRank: "Hang repo active",
    sharedHotspots: "Hotspot chung",
    comparisonNotes: "Ghi chu so sanh",
    evidenceLeaders: "Evidence dan dau",
    citationScore: "Diem citation",
    globalRank: "Hang toan workspace",
    citations: "Citation",
    autoFiles: "File da tu dong them",
    autoFilesHint:
      "RepoBrain da tim thay file cu the trong ket qua nay, them vao repo memory, va xep hang viec can inspect tiep.",
    improve: "Cai thien",
    source: "Nguon",
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
    localOnly: "Workbench local",
    localOnlyHint:
      "Ung dung browser nay chi goi toi RepoBrain Python server dang chay local cua ban. Khong can hosted backend.",
    reportHint:
      "Query mot repo se tu dong tai su dung repo memory da luu. Dung Da repo de so sanh evidence tren tat ca project da track.",
    diagnosticsTitle: "Health va provider",
    diagnosticsHint:
      "Doctor posture va provider smoke duoc giu o day de luc release khong phai doc lai ca khoi text dai.",
    activityTitle: "Hoat dong gan day",
    activityHint: "RepoBrain giu mot timeline ngan cho nhung tac vu ban vua chay trong tab nay.",
    workspaceTitle: "Workspace",
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
    newcomerTitle: "Workflow nen dung",
    newcomerHint:
      "RepoBrain de dung hon khi lan dau chi theo mot duong: import, hoi, roi review. Giao dien se giu file context can xem tiep thay vi giau trong raw text.",
    newcomerImport: "Import + Index",
    newcomerImportHint: "Build ban do local truoc de moi ket qua co the cite file that.",
    newcomerAsk: "Hoi hoac trace",
    newcomerAskHint: "Dung Query de tim vi tri, Trace de xem flow, Impact de xem blast radius, Targets de lap ke hoach edit.",
    newcomerReview: "Review co context",
    newcomerReviewHint: "File auto-attached cho biet nen mo file nao tiep va cai thien theo huong nao.",
    footerTitle: "RepoBrain Workbench",
    footerBody: "Moi thu o day chi noi voi RepoBrain server local va giu project memory tren may nay.",
    footerPrimary: "Bat dau bang Import + Index",
    footerSecondary: "Sau do chay Patch Review",
    indexed: "Da index",
    files: "Files",
    chunks: "Chunks",
    embedding: "Embedding",
    reranker: "Reranker",
    fallbackPool: "Pool model reranker",
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
    disabledUntilImport: "Hay import repo truoc de mo khoa check, memory, va grounded query.",
  },
} as const;

const viOverrides: Partial<typeof baseCopy.en> = {
  subtitle:
    "Bàn làm việc phân tích code chạy cục bộ để import repo, hỏi có bằng chứng, review patch và chuẩn bị release.",
  language: "Ngôn ngữ",
  theme: "Giao diện",
  light: "Sáng",
  dark: "Tối",
  activeRepo: "Repo đang dùng",
  none: "Chưa có",
  noActiveRepo: "Chưa có repo đang dùng. Hãy import đường dẫn dự án trước.",
  importTitle: "Thiết lập dự án",
  projectPath: "Đường dẫn dự án",
  chooseFolder: "Chọn thư mục",
  importHint:
    "Chọn thư mục local hoặc dán đường dẫn. Import sẽ khởi tạo trạng thái RepoBrain, thêm repo vào workspace và build local index trong một bước.",
  actionsHint:
    "Chạy các kiểm tra chính ở một nơi: index lại sau thay đổi, review rủi ro, chấm điểm ship readiness, lưu baseline và kiểm tra provider.",
  index: "Index lại repo hiện tại",
  patchReviewTitle: "Hàng rào an toàn cho patch",
  patchReviewHint:
    "Review patch hiện tại, so sánh với base ref hoặc kiểm tra danh sách file cụ thể ngay trên giao diện web.",
  patchFiles: "Danh sách file",
  patchReviewRun: "Chạy patch review",
  baseline: "Lưu baseline",
  providerSmoke: "Smoke provider",
  geminiSetup: "Cấu hình Gemini",
  geminiSetupHint:
    "Lưu Gemini API key và model pool vào repo đang dùng để chạy Docker hoặc local.",
  geminiModelPool: "Gemini model pool",
  useGeminiEmbedding: "Dùng embedding Gemini",
  useGeminiReranker: "Dùng reranker Gemini",
  saveGeminiConfig: "Lưu cấu hình Gemini",
  groqSetup: "Cấu hình Groq",
  groqSetupHint:
    "Lưu Groq API key và pool model reranker, đồng thời giữ embedding chạy local.",
  groqModelPool: "Groq model pool",
  useGroqReranker: "Dùng reranker Groq",
  saveGroqConfig: "Lưu cấu hình Groq",
  doctor: "Kiểm tra sức khỏe",
  openReport: "Mở báo cáo",
  exportMarkdown: "Xuất .md",
  mode: "Chế độ",
  question: "Câu hỏi",
  questionPlaceholder: "Logic payment retry nằm ở đâu?",
  run: "Chạy",
  resultTitle: "Kết quả có bằng chứng",
  focusTitle: "Bắt đầu tại đây",
  focusImportHint: "Dán đường dẫn hoặc chọn thư mục dự án, sau đó bấm Import + Index.",
  focusQueryHint: "Đặt câu hỏi và đổi mode khi cần trace, impact hoặc targets.",
  focusAdvancedLabel: "Công cụ nâng cao",
  focusAdvancedHint: "Mở patch review, ship checks, cấu hình provider và panel repo memory.",
  showAdvanced: "Hiện công cụ nâng cao",
  hideAdvanced: "Ẩn công cụ nâng cao",
  crossRepoOverview: "Tổng quan đa repo",
  bestMatch: "Repo phù hợp nhất",
  activeRank: "Thứ hạng repo hiện tại",
  sharedHotspots: "Hotspot chung",
  comparisonNotes: "Ghi chú so sánh",
  evidenceLeaders: "Bằng chứng nổi bật",
  citationScore: "Điểm trích dẫn",
  globalRank: "Xếp hạng toàn workspace",
  citations: "Trích dẫn",
  autoFiles: "File tự đính kèm",
  autoFilesHint:
    "RepoBrain đã tìm thấy các file liên quan trong kết quả, thêm vào repo memory và xếp hạng thứ tự nên mở tiếp.",
  improve: "Hướng cải thiện",
  source: "Nguồn",
  repoMemory: "Bộ nhớ repo",
  rawTranscript: "Bản raw",
  workspaceErrors: "Lỗi workspace",
  emptyResult:
    "Chưa có kết quả. Hãy import repo, rồi chạy review, doctor, provider smoke hoặc hỏi một câu grounded.",
  loading: "Đang xử lý...",
  multiMode: "Đa repo",
  interfaceStatus: "Trạng thái giao diện",
  localOnly: "Workbench local",
  localOnlyHint:
    "Ứng dụng web này chỉ gọi tới RepoBrain Python server chạy local trên máy bạn, không cần backend hosted.",
  reportHint:
    "Query một repo sẽ tự dùng lại repo memory đã lưu. Dùng Đa repo để so sánh evidence giữa các dự án đã track.",
  diagnosticsTitle: "Sức khỏe và provider",
  diagnosticsHint:
    "Doctor posture và provider smoke luôn hiển thị tại đây để kiểm tra release không phụ thuộc vào đoạn text dài.",
  activityTitle: "Hoạt động gần đây",
  activityHint: "RepoBrain lưu timeline ngắn cho các tác vụ bạn vừa chạy trong tab này.",
  workspaceHint:
    "Các repo đã import sẽ được theo dõi tại đây. Bạn có thể đổi repo đang dùng ngay và hỏi tiếp mà không mất mạch.",
  memoryHint:
    "Lưu vài ghi chú quan trọng, rồi để RepoBrain giữ summary, hot files và câu hỏi kế tiếp cho lần truy vấn sau.",
  rememberNote: "Ghi chú bộ nhớ",
  saveNote: "Lưu ghi chú",
  clearNotes: "Xóa ghi chú",
  useRepo: "Dùng repo",
  activeLabel: "Đang dùng",
  noSummary: "Chưa có tóm tắt đã lưu.",
  manualNotes: "Ghi chú thủ công",
  recentAsks: "Câu hỏi gần đây",
  nextThread: "Luồng tiếp theo",
  updatedAt: "Cập nhật",
  noWorkspace: "Chưa có repo nào được theo dõi. Hãy import dự án đầu tiên để bắt đầu workspace liên tục.",
  noDiagnostics: "Hãy chạy Doctor sau khi import để có diagnostics có cấu trúc.",
  noSmoke: "Hãy chạy Provider Smoke để xem model active, trạng thái failover và sức khỏe provider.",
  noActivity: "Chưa có hoạt động nào trong phiên này.",
  newcomerTitle: "Quy trình đề xuất",
  newcomerHint:
    "RepoBrain dễ dùng nhất khi đi theo một đường: import, hỏi, rồi review. Giao diện giữ file context cần mở tiếp thay vì ẩn trong raw text.",
  newcomerAsk: "Hỏi hoặc trace",
  newcomerAskHint:
    "Dùng Query để tìm vị trí, Trace để theo luồng, Impact để xem blast radius và Targets để lập kế hoạch chỉnh sửa.",
  newcomerReview: "Review có ngữ cảnh",
  newcomerReviewHint: "File auto-attached cho biết nên mở file nào tiếp theo và cần cải thiện theo hướng nào.",
  footerBody: "Mọi thứ ở đây chỉ giao tiếp với RepoBrain server local và giữ project memory trên máy này.",
  footerPrimary: "Bắt đầu với Import + Index",
  footerSecondary: "Sau đó chạy Patch Review",
  indexed: "Đã index",
  fallbackPool: "Pool model reranker",
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
  dimensions: "Số chiều",
  activeBefore: "Model trước",
  activeAfter: "Model sau",
  lastSync: "Lần đồng bộ",
  unavailable: "Không khả dụng",
  yes: "Có",
  no: "Không",
  ready: "Sẵn sàng",
  notReady: "Chưa sẵn sàng",
  disabledUntilImport: "Hãy import repo để mở khóa kiểm tra, bộ nhớ và grounded query.",
};

const zhOverrides: Partial<typeof baseCopy.en> = {
  subtitle: "本地代码智能工作台，用于导入仓库、提出有依据的问题、审查补丁并准备发布。",
  language: "语言",
  theme: "主题",
  light: "浅色",
  dark: "深色",
  activeRepo: "当前仓库",
  none: "无",
  noActiveRepo: "当前还没有激活仓库。请先导入项目路径。",
  importTitle: "项目初始化",
  projectPath: "项目路径",
  chooseFolder: "选择文件夹",
  importButton: "导入并建索引",
  importHint: "选择本地文件夹或粘贴路径。导入会一次完成状态初始化、加入工作区以及本地索引构建。",
  actionsTitle: "工作流操作",
  actionsHint: "在一个地方完成核心检查：重建索引、审查风险、评估发布就绪度、保存基线和验证 provider。",
  index: "重建当前仓库索引",
  patchReview: "补丁审查",
  patchReviewTitle: "补丁审查护栏",
  patchReviewHint: "可直接在浏览器里审查当前补丁、对比基线分支，或指定文件列表检查。",
  patchBase: "基线分支",
  patchFiles: "文件列表",
  patchReviewRun: "执行补丁审查",
  review: "项目审查",
  ship: "发布就绪度",
  baseline: "保存基线",
  providerSmoke: "Provider 冒烟测试",
  geminiSetup: "Gemini 配置",
  geminiSetupHint: "把 Gemini API key 和模型池保存到当前仓库，支持 Docker 或本地运行。",
  geminiModelPool: "Gemini 模型池",
  useGeminiEmbedding: "使用 Gemini Embedding",
  useGeminiReranker: "使用 Gemini Reranker",
  saveGeminiConfig: "保存 Gemini 配置",
  groqSetup: "Groq 配置",
  groqSetupHint: "保存 Groq API key 与 reranker 模型池，同时保持 embedding 本地运行。",
  groqModelPool: "Groq 模型池",
  useGroqReranker: "使用 Groq Reranker",
  saveGroqConfig: "保存 Groq 配置",
  doctor: "健康检查",
  openReport: "打开报告",
  exportMarkdown: "导出 .md",
  queryTitle: "问答查询",
  mode: "模式",
  question: "问题",
  questionPlaceholder: "支付重试逻辑在哪里实现？",
  run: "运行",
  resultTitle: "证据结果",
  focusTitle: "从这里开始",
  focusImportLabel: "导入项目",
  focusImportHint: "先粘贴或选择项目目录，再执行“导入并建索引”。",
  focusQueryLabel: "问答查询",
  focusQueryHint: "先提问；需要时再切换到 trace、impact 或 targets。",
  focusAdvancedLabel: "高级工具",
  focusAdvancedHint: "展开补丁审查、发布检查、provider 配置和仓库记忆面板。",
  showAdvanced: "显示高级工具",
  hideAdvanced: "隐藏高级工具",
  crossRepoOverview: "跨仓库总览",
  bestMatch: "最佳匹配",
  activeRank: "当前仓库排名",
  sharedHotspots: "共享热点",
  comparisonNotes: "对比说明",
  evidenceLeaders: "证据领先项",
  citationScore: "引用分数",
  globalRank: "全局排名",
  citations: "引用",
  autoFiles: "自动附加文件",
  autoFilesHint: "RepoBrain 已识别相关文件并写入仓库记忆，同时给出优先查看顺序。",
  improve: "改进建议",
  source: "来源",
  repoMemory: "仓库记忆",
  rawTranscript: "原始输出",
  workspaceErrors: "工作区错误",
  emptyResult: "暂无结果。请先导入仓库，然后执行 review、doctor、provider smoke 或发起 grounded 问题。",
  loading: "处理中...",
  queryMode: "查询",
  traceMode: "追踪",
  impactMode: "影响",
  targetsMode: "目标",
  multiMode: "跨仓库",
  interfaceStatus: "界面状态",
  localOnly: "本地工作台",
  localOnlyHint: "此浏览器应用只连接你本机的 RepoBrain Python 服务，不依赖托管后端。",
  reportHint: "单仓库查询会自动复用仓库记忆。使用跨仓库模式可比较所有已跟踪项目的证据。",
  diagnosticsTitle: "健康与 Provider",
  diagnosticsHint: "Doctor 与 Provider smoke 保持可见，发布检查无需反复翻找原始文本。",
  activityTitle: "最近活动",
  activityHint: "RepoBrain 会在当前浏览器标签页保留一条简短的本地操作时间线。",
  workspaceTitle: "工作区",
  workspaceHint: "已导入仓库会持续跟踪，可快速切换当前仓库并保持查询上下文。",
  memoryTitle: "仓库记忆",
  memoryHint: "保存少量关键备注，让 RepoBrain 在下一次提问时继续带上摘要、热点文件和后续问题。",
  rememberNote: "记忆备注",
  notePlaceholder: "Auth callback 是关键集成链路。",
  saveNote: "保存备注",
  clearNotes: "清空备注",
  useRepo: "使用仓库",
  activeLabel: "当前",
  noSummary: "暂无已保存摘要。",
  manualNotes: "手动备注",
  recentAsks: "最近提问",
  hotFiles: "热点文件",
  nextThread: "下一步问题",
  updatedAt: "更新时间",
  noWorkspace: "还没有跟踪仓库。请先导入第一个项目。",
  noDiagnostics: "导入后运行 Doctor 以生成结构化诊断信息。",
  noSmoke: "运行 Provider Smoke 查看当前模型、故障切换状态和 provider 健康情况。",
  noActivity: "本次会话暂无活动。",
  newcomerTitle: "推荐流程",
  newcomerHint: "首次使用按一条路径最稳：导入、提问、再审查。界面会把下一步文件上下文直接展示出来。",
  newcomerImport: "导入并建索引",
  newcomerImportHint: "先建立本地代码地图，后续结果才能引用真实文件。",
  newcomerAsk: "提问或追踪",
  newcomerAskHint: "Query 用于定位；Trace 看流程；Impact 看影响范围；Targets 做修改规划。",
  newcomerReview: "结合上下文审查",
  newcomerReviewHint: "自动附加文件会告诉你下一步该打开什么，以及如何改进补丁。",
  footerTitle: "RepoBrain 工作台",
  footerBody: "这里的所有操作都连接本地 RepoBrain 服务，项目记忆保存在你的机器上。",
  footerPrimary: "先执行导入并建索引",
  footerSecondary: "然后执行补丁审查",
  indexed: "已索引",
  files: "文件",
  chunks: "分块",
  embedding: "Embedding",
  reranker: "Reranker",
  fallbackPool: "Reranker 模型池",
  singleModel: "单模型模式",
  failover: "最近故障切换",
  remoteProviders: "远程 Provider",
  networkRequired: "需要网络",
  localStorageOnly: "仅本地存储",
  parserPosture: "解析器状态",
  providerPosture: "Provider 状态",
  warnings: "警告",
  noWarnings: "无警告",
  status: "状态",
  score: "分数",
  vectors: "向量数",
  dimensions: "维度",
  activeBefore: "切换前",
  activeAfter: "切换后",
  lastSync: "最近同步",
  unavailable: "不可用",
  yes: "是",
  no: "否",
  ready: "就绪",
  notReady: "未就绪",
  disabledUntilImport: "请先导入仓库，再解锁检查、记忆和 grounded 查询。",
};

const copy: Record<Locale, typeof baseCopy.en> = {
  en: baseCopy.en,
  vi: { ...baseCopy.en, ...baseCopy.vi, ...viOverrides },
  zh: { ...baseCopy.en, ...zhOverrides },
};

function useLocale(): [Locale, (next: Locale) => void] {
  const [locale, setLocale] = useState<Locale>(() => {
    const saved = window.localStorage.getItem("repobrain-web-locale");
    if (saved === "en" || saved === "vi" || saved === "zh") {
      return saved;
    }
    const browserLocale = window.navigator.language.toLowerCase();
    if (browserLocale.startsWith("vi")) {
      return "vi";
    }
    if (browserLocale.startsWith("zh")) {
      return "zh";
    }
    return "en";
  });

  useEffect(() => {
    window.localStorage.setItem("repobrain-web-locale", locale);
    document.documentElement.lang = locale === "vi" ? "vi-VN" : locale === "zh" ? "zh-CN" : "en-US";
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
    case "patch-review":
      return t.patchReview;
    case "ship":
      return t.ship;
    case "baseline":
      return t.baseline;
    case "provider-smoke":
      return t.providerSmoke;
    case "doctor":
      return t.doctor;
    case "gemini-config":
      return t.geminiSetup;
    case "groq-config":
      return t.groqSetup;
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
  const languageTag = locale === "vi" ? "vi-VN" : locale === "zh" ? "zh-CN" : "en-US";
  return date.toLocaleTimeString(languageTag, {
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

function setNamedMetaTag(name: string, content: string) {
  let tag = document.head.querySelector(`meta[name="${name}"]`) as HTMLMetaElement | null;
  if (!tag) {
    tag = document.createElement("meta");
    tag.setAttribute("name", name);
    document.head.appendChild(tag);
  }
  tag.setAttribute("content", content);
}

function setPropertyMetaTag(property: string, content: string) {
  let tag = document.head.querySelector(`meta[property="${property}"]`) as HTMLMetaElement | null;
  if (!tag) {
    tag = document.createElement("meta");
    tag.setAttribute("property", property);
    document.head.appendChild(tag);
  }
  tag.setAttribute("content", content);
}

function sanitizeFilename(input: string): string {
  const cleaned = input
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return cleaned || "report";
}

const QUERY_PRESET_STORAGE_KEY = "repobrain-web-query-presets";
const MAX_QUERY_PRESETS = 8;

function loadQueryPresets(): QueryPreset[] {
  try {
    const raw = window.localStorage.getItem(QUERY_PRESET_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed
      .map((item) => {
        if (!item || typeof item !== "object") {
          return null;
        }
        const mode = item.mode;
        if (mode !== "query" && mode !== "trace" && mode !== "impact" && mode !== "targets" && mode !== "multi") {
          return null;
        }
        const label = String(item.label || "").trim();
        const query = String(item.query || "").trim();
        if (!label || !query) {
          return null;
        }
        return {
          id: Number(item.id) || Date.now(),
          label: label.slice(0, 64),
          query: query.slice(0, 400),
          mode,
        } as QueryPreset;
      })
      .filter((item): item is QueryPreset => item !== null)
      .slice(0, MAX_QUERY_PRESETS);
  } catch {
    return [];
  }
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
  const [patchBase, setPatchBase] = useState("");
  const [patchFiles, setPatchFiles] = useState("");
  const [note, setNote] = useState("");
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [geminiModelPool, setGeminiModelPool] = useState("gemini-2.5-flash,gemini-2.5-flash-lite,gemini-3-flash-preview");
  const [geminiUseEmbedding, setGeminiUseEmbedding] = useState(true);
  const [geminiUseReranker, setGeminiUseReranker] = useState(true);
  const [groqApiKey, setGroqApiKey] = useState("");
  const [groqModelPool, setGroqModelPool] = useState("llama-3.3-70b-versatile,openai/gpt-oss-20b");
  const [groqUseReranker, setGroqUseReranker] = useState(true);
  const [message, setMessage] = useState("");
  const [resultTitle, setResultTitle] = useState("");
  const [resultBody, setResultBody] = useState("");
  const [resultAction, setResultAction] = useState<ActionKind>("query");
  const [resultData, setResultData] = useState<ActionPayload["data"] | null>(null);
  const [fileContext, setFileContext] = useState<FileContext | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [doctorData, setDoctorData] = useState<DoctorData | null>(null);
  const [smokeData, setSmokeData] = useState<ProviderSmokeData | null>(null);
  const [doctorSyncAt, setDoctorSyncAt] = useState<string | null>(null);
  const [smokeSyncAt, setSmokeSyncAt] = useState<string | null>(null);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [queryPresetName, setQueryPresetName] = useState("");
  const [queryPresets, setQueryPresets] = useState<QueryPreset[]>(() => loadQueryPresets());

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

  useEffect(() => {
    try {
      window.localStorage.setItem(QUERY_PRESET_STORAGE_KEY, JSON.stringify(queryPresets.slice(0, MAX_QUERY_PRESETS)));
    } catch {
      // Keep the UI responsive even if storage is blocked.
    }
  }, [queryPresets]);

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
      locales: current?.locales || ["en", "vi", "zh"],
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
    setFileContext(payload.file_context ?? null);
    appendActivity(action, payload.message);
    if (
      action === "index" ||
      action === "patch-review" ||
      action === "review" ||
      action === "ship" ||
      action === "baseline" ||
      action === "provider-smoke" ||
      action === "doctor" ||
      action === "gemini-config" ||
      action === "groq-config" ||
      action === "workspace-use" ||
      action === "remember" ||
      action === "clear-notes"
    ) {
      setShowAdvanced(true);
    }

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
    if (action === "patch-review") {
      setPatchBase((current) => current.trim());
    }
    if (action === "remember") {
      setNote("");
    }
    if (action === "gemini-config") {
      setGeminiApiKey("");
      void refreshDoctorSnapshot();
    }
    if (action === "groq-config") {
      setGroqApiKey("");
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

  async function handleChooseFolder() {
    try {
      setBusy("choose-folder");
      const payload = await readJson<SelectFolderPayload>("/api/select-folder", {
        method: "POST",
        body: JSON.stringify({ initial_dir: repoPath }),
      });
      setRepoPath(payload.repo_path);
      setMessage(payload.message);
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

  function handleSavePreset() {
    const cleanedQuery = query.trim();
    if (!cleanedQuery) {
      return;
    }
    const inferredName = cleanedQuery.slice(0, 56);
    const cleanedName = (queryPresetName.trim() || inferredName).slice(0, 64);
    setQueryPresets((current) => {
      const deduped = current.filter((item) => !(item.mode === mode && item.query === cleanedQuery));
      const next: QueryPreset = {
        id: Date.now(),
        label: cleanedName,
        query: cleanedQuery,
        mode,
      };
      return [next, ...deduped].slice(0, MAX_QUERY_PRESETS);
    });
    setQueryPresetName("");
  }

  function handleApplyPreset(preset: QueryPreset) {
    setMode(preset.mode);
    setQuery(preset.query);
  }

  function handleRemovePreset(id: number) {
    setQueryPresets((current) => current.filter((item) => item.id !== id));
  }

  async function handlePatchReview(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setBusy("patch-review");
      const trimmedBase = patchBase.trim();
      const files = patchFiles
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
      const payload = await readJson<ActionPayload>("/api/patch-review", {
        method: "POST",
        body: JSON.stringify({
          base: files.length > 0 ? null : trimmedBase || null,
          files: files.length > 0 ? files : null,
        }),
      });
      applyPayload("patch-review", payload);
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

  function handleExportMarkdown() {
    const timestamp = new Date().toISOString();
    const title = resultTitle || t.resultTitle;
    const safeAction = sanitizeFilename(resultAction);
    const safeRepo = sanitizeFilename(activeRepo.split(/[\\/]/).pop() || "workspace");
    const messageBlock = message.trim() ? message.trim() : t.unavailable;
    const bodyBlock = resultBody.trim() ? resultBody.trim() : t.emptyResult;
    const fileSummary =
      attachedFiles.length > 0
        ? attachedFiles
            .map((item) => `- ${item.file_path}${item.line_range ? `:${item.line_range}` : ""} (${item.source})`)
            .join("\n")
        : "- none";
    const markdown = [
      "# RepoBrain Export",
      `- generated_at: ${timestamp}`,
      `- locale: ${locale}`,
      `- action: ${resultAction}`,
      `- title: ${title}`,
      `- active_repo: ${activeRepo || t.none}`,
      "",
      "## Message",
      messageBlock,
      "",
      "## Attached Files",
      fileSummary,
      "",
      "## Output",
      "```text",
      bodyBlock,
      "```",
      "",
    ].join("\n");
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `repobrain-${safeRepo}-${safeAction}-${timestamp.slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function handleGeminiConfig(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setBusy("gemini-config");
      const payload = await readJson<ActionPayload>("/api/providers/gemini", {
        method: "POST",
        body: JSON.stringify({
          api_key: geminiApiKey,
          model_pool: geminiModelPool,
          use_embedding: geminiUseEmbedding,
          use_reranker: geminiUseReranker,
          rerank_model: geminiModelPool.split(",").map((item) => item.trim()).filter(Boolean)[0] || "gemini-2.5-flash",
        }),
      });
      applyPayload("gemini-config", payload);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  async function handleGroqConfig(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setBusy("groq-config");
      const payload = await readJson<ActionPayload>("/api/providers/groq", {
        method: "POST",
        body: JSON.stringify({
          api_key: groqApiKey,
          model_pool: groqModelPool,
          use_reranker: groqUseReranker,
          rerank_model: groqModelPool.split(",").map((item) => item.trim()).filter(Boolean)[0] || "llama-3.3-70b-versatile",
        }),
      });
      applyPayload("groq-config", payload);
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
  const attachedFiles = fileContext?.files || [];
  const hasExportContent = Boolean(resultBody.trim() || message.trim() || attachedFiles.length > 0);

  useEffect(() => {
    const repoName = activeRepo.split(/[\\/]/).pop() || "";
    const seoByLocale: Record<Locale, { title: string; description: string }> = {
      en: {
        title: repoName ? `RepoBrain Workbench | ${repoName}` : "RepoBrain Workbench | Local Code Intelligence",
        description:
          "RepoBrain Workbench helps teams import repositories, run grounded chat queries, review patches, and track release readiness with local-first code intelligence.",
      },
      vi: {
        title: repoName ? `RepoBrain Workbench | ${repoName}` : "RepoBrain Workbench | Phan tich code local",
        description:
          "RepoBrain Workbench giup import repository, hoi chat query co bang chung, review patch va theo doi release readiness voi mo hinh local-first.",
      },
      zh: {
        title: repoName ? `RepoBrain Workbench | ${repoName}` : "RepoBrain Workbench | 本地代码智能",
        description:
          "RepoBrain Workbench 用于导入仓库、执行有依据的查询、审查补丁并跟踪发布就绪度，提供 local-first 的代码智能体验。",
      },
    };
    const seo = seoByLocale[locale];
    document.title = seo.title;
    setNamedMetaTag("description", seo.description);
    setNamedMetaTag("twitter:title", seo.title);
    setNamedMetaTag("twitter:description", seo.description);
    setNamedMetaTag("application-name", "RepoBrain Workbench");
    setPropertyMetaTag("og:title", seo.title);
    setPropertyMetaTag("og:description", seo.description);
  }, [locale, activeRepo]);

  return (
    <main className="app-shell">
      <header className="hero-grid" aria-label={t.brand}>
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
                <button
                  className={locale === "zh" ? "chip-button active" : "chip-button"}
                  onClick={() => setLocale("zh")}
                  type="button"
                >
                  中文
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
              <span className="brand-kicker">{t.localOnly}</span>
              <h1 id="app-title" className="brand-wordmark" aria-label={t.brand}>
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
          <div className="card-title-row">
            <span className="card-step-badge">1</span>
            <h2>{t.importTitle}</h2>
          </div>
          <form className="panel-form" onSubmit={handleImport}>
            <label htmlFor="repoPath">{t.projectPath}</label>
            <input
              id="repoPath"
              placeholder={t.projectPathPlaceholder}
              value={repoPath}
              onChange={(event) => setRepoPath(event.target.value)}
            />
            <div className="form-button-row">
              <button
                className="outline-button"
                disabled={busy === "choose-folder" || busy === "import"}
                onClick={() => void handleChooseFolder()}
                type="button"
              >
                {busy === "choose-folder" ? t.loading : t.chooseFolder}
              </button>
              <button className="primary-button" disabled={busy === "import" || busy === "choose-folder"} type="submit">
                {busy === "import" ? t.loading : t.importButton}
              </button>
            </div>
          </form>
          <p className="muted-copy">{t.importHint}</p>
          {!hasActiveRepo ? <div className="notice-box neutral">{t.disabledUntilImport}</div> : null}
        </article>
      </header>

      <section className="primary-flow-grid">
        <article className="panel-card query-card">
          <div className="card-title-row">
            <span className="card-step-badge">2</span>
            <h2>{t.queryTitle}</h2>
          </div>
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
            <div className="preset-panel">
              <div className="preset-panel-head">
                <strong>{t.presetsTitle}</strong>
                <span>{queryPresets.length}</span>
              </div>
              <p className="preset-help">{t.presetsHint}</p>
              <label htmlFor="queryPresetName">{t.presetName}</label>
              <div className="preset-save-row">
                <input
                  id="queryPresetName"
                  placeholder={t.presetNamePlaceholder}
                  value={queryPresetName}
                  onChange={(event) => setQueryPresetName(event.target.value)}
                />
                <button className="ghost-button small-button" disabled={!query.trim()} onClick={handleSavePreset} type="button">
                  {t.savePreset}
                </button>
              </div>
              {queryPresets.length > 0 ? (
                <div className="preset-chip-list">
                  {queryPresets.map((preset) => (
                    <article key={preset.id} className="preset-chip-item">
                      <button className="chip-button active" onClick={() => handleApplyPreset(preset)} type="button">
                        {preset.label}
                      </button>
                      <small>{labelForAction(locale, preset.mode)}</small>
                      <button className="ghost-button small-button" onClick={() => handleRemovePreset(preset.id)} type="button">
                        {t.removePreset}
                      </button>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-state compact-empty">{t.noPresets}</div>
              )}
            </div>
            <button className="primary-button" disabled={!hasActiveRepo || busy === "query"} type="submit">
              {busy === "query" ? t.loading : t.run}
            </button>
          </form>
          <p className="muted-copy">{t.reportHint}</p>
        </article>

        <article className="panel-card focus-card">
          <div className="section-heading">
            <div>
              <h2>{t.focusTitle}</h2>
              <p className="section-copy">{t.focusAdvancedHint}</p>
            </div>
          </div>
          <div className="focus-list">
            <article className="focus-item">
              <span className="focus-circle">1</span>
              <div>
                <strong>{t.focusImportLabel}</strong>
                <p>{t.focusImportHint}</p>
              </div>
            </article>
            <article className="focus-item">
              <span className="focus-circle">2</span>
              <div>
                <strong>{t.focusQueryLabel}</strong>
                <p>{t.focusQueryHint}</p>
              </div>
            </article>
            <article className="focus-item">
              <span className="focus-circle">3</span>
              <div>
                <strong>{t.focusAdvancedLabel}</strong>
                <p>{t.focusAdvancedHint}</p>
              </div>
            </article>
          </div>
          <div className="focus-actions">
            <button className="ghost-button" onClick={() => setShowAdvanced((current) => !current)} type="button">
              {showAdvanced ? t.hideAdvanced : t.showAdvanced}
            </button>
          </div>
          {message ? <div className="notice-box">{message}</div> : null}
        </article>
      </section>

      {showAdvanced ? (
        <section className="workspace-grid">
          <article className="panel-card maintenance-card">
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
          </article>

          <article className="panel-card patch-card">
            <div className="card-title-row">
              <span className="card-step-badge">3</span>
              <h2>{t.patchReviewTitle}</h2>
            </div>
            <form className="panel-form" onSubmit={handlePatchReview}>
              <label htmlFor="patchBase">{t.patchBase}</label>
              <input
                id="patchBase"
                placeholder={t.patchBasePlaceholder}
                value={patchBase}
                onChange={(event) => setPatchBase(event.target.value)}
                disabled={!hasActiveRepo || patchFiles.trim().length > 0}
              />
              <label htmlFor="patchFiles">{t.patchFiles}</label>
              <textarea
                id="patchFiles"
                placeholder={t.patchFilesPlaceholder}
                value={patchFiles}
                onChange={(event) => setPatchFiles(event.target.value)}
                disabled={!hasActiveRepo}
              />
              <button className="primary-button" disabled={!hasActiveRepo || busy === "patch-review"} type="submit">
                {busy === "patch-review" ? t.loading : t.patchReviewRun}
              </button>
            </form>
            <p className="muted-copy">{t.patchReviewHint}</p>
          </article>
        </section>
      ) : null}

      {showAdvanced ? (
        <>
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
                      {project.active ? ` - ${t.activeLabel}` : ""}
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

          <form className="subpanel-card inset provider-config-form" onSubmit={handleGeminiConfig}>
            <div className="subpanel-head">
              <div>
                <h3>{t.geminiSetup}</h3>
                <p>{t.geminiSetupHint}</p>
              </div>
              <span className="mini-pill">Docker</span>
            </div>
            <div className="panel-form">
              <label htmlFor="geminiApiKey">{t.geminiApiKey}</label>
              <input
                id="geminiApiKey"
                type="password"
                autoComplete="off"
                placeholder={t.geminiApiKeyPlaceholder}
                value={geminiApiKey}
                onChange={(event) => setGeminiApiKey(event.target.value)}
                disabled={!hasActiveRepo}
              />
              <label htmlFor="geminiModelPool">{t.geminiModelPool}</label>
              <input
                id="geminiModelPool"
                placeholder={t.geminiModelPoolPlaceholder}
                value={geminiModelPool}
                onChange={(event) => setGeminiModelPool(event.target.value)}
                disabled={!hasActiveRepo}
              />
              <div className="toggle-row">
                <label>
                  <input
                    type="checkbox"
                    checked={geminiUseEmbedding}
                    onChange={(event) => setGeminiUseEmbedding(event.target.checked)}
                    disabled={!hasActiveRepo}
                  />
                  <span>{t.useGeminiEmbedding}</span>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={geminiUseReranker}
                    onChange={(event) => setGeminiUseReranker(event.target.checked)}
                    disabled={!hasActiveRepo}
                  />
                  <span>{t.useGeminiReranker}</span>
                </label>
              </div>
              <button className="primary-button" disabled={!hasActiveRepo || busy === "gemini-config"} type="submit">
                {busy === "gemini-config" ? t.loading : t.saveGeminiConfig}
              </button>
            </div>
          </form>

          <form className="subpanel-card inset provider-config-form" onSubmit={handleGroqConfig}>
            <div className="subpanel-head">
              <div>
                <h3>{t.groqSetup}</h3>
                <p>{t.groqSetupHint}</p>
              </div>
              <span className="mini-pill">JSON</span>
            </div>
            <div className="panel-form">
              <label htmlFor="groqApiKey">{t.groqApiKey}</label>
              <input
                id="groqApiKey"
                type="password"
                autoComplete="off"
                placeholder={t.groqApiKeyPlaceholder}
                value={groqApiKey}
                onChange={(event) => setGroqApiKey(event.target.value)}
                disabled={!hasActiveRepo}
              />
              <label htmlFor="groqModelPool">{t.groqModelPool}</label>
              <input
                id="groqModelPool"
                placeholder={t.groqModelPoolPlaceholder}
                value={groqModelPool}
                onChange={(event) => setGroqModelPool(event.target.value)}
                disabled={!hasActiveRepo}
              />
              <div className="toggle-row single">
                <label>
                  <input
                    type="checkbox"
                    checked={groqUseReranker}
                    onChange={(event) => setGroqUseReranker(event.target.checked)}
                    disabled={!hasActiveRepo}
                  />
                  <span>{t.useGroqReranker}</span>
                </label>
              </div>
              <button className="primary-button" disabled={!hasActiveRepo || busy === "groq-config"} type="submit">
                {busy === "groq-config" ? t.loading : t.saveGroqConfig}
              </button>
            </div>
          </form>

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
        </>
      ) : null}

      <section className="result-card">
        <div className="result-header">
          <h2>{resultTitle || t.resultTitle}</h2>
          <div className="result-header-actions">
            <span className="result-chip">{resultBadge}</span>
            <button className="ghost-button small-button" disabled={!hasExportContent} onClick={handleExportMarkdown} type="button">
              {t.exportMarkdown}
            </button>
          </div>
        </div>
        {attachedFiles.length > 0 ? (
          <article className="subpanel-card attached-files-panel">
            <div className="subpanel-head">
              <div>
                <h3>{t.autoFiles}</h3>
                <p>{fileContext?.summary || t.autoFilesHint}</p>
              </div>
              <span className="mini-pill">{attachedFiles.length}</span>
            </div>
            <div className="attached-file-list">
              {attachedFiles.map((item) => (
                <article key={`${item.file_path}:${item.source}:${item.line_range || ""}`} className="attached-file-card">
                  <div className="citation-meta">
                    <strong className="citation-path">
                      {item.file_path}
                      {item.line_range ? `:${item.line_range}` : ""}
                    </strong>
                    <span>{item.score == null ? item.role : item.score.toFixed(3)}</span>
                  </div>
                  <div className="inline-pills">
                    <span className="inline-pill">
                      {t.source}: {item.source}
                    </span>
                    <span className="inline-pill neutral">{item.role}</span>
                  </div>
                  <p className="citation-preview">{item.reason || t.noSummary}</p>
                  <p className="improvement-copy">
                    <strong>{t.improve}:</strong> {item.improvement || t.noSummary}
                  </p>
                </article>
              ))}
            </div>
            {fileContext?.warnings?.length ? (
              <ul className="summary-list attached-warning-list">
                {fileContext.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : null}
          </article>
        ) : null}
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
                            {citation.active ? ` - ${t.activeLabel}` : ""} - {citation.file_path}:{citation.start_line}-
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
                        {item.label} - {item.count} repo - {item.repos.join(" | ")}
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
                      {item.active ? ` - ${t.activeLabel}` : ""}
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

      <footer className="app-footer">
        <div>
          <span className="eyebrow">{t.brand}</span>
          <h2>{t.footerTitle}</h2>
          <p>{t.footerBody}</p>
        </div>
        <div className="footer-action-row">
          <span>{t.footerPrimary}</span>
          <span>{t.footerSecondary}</span>
        </div>
      </footer>
    </main>
  );
}
