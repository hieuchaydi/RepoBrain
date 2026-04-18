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

export type Locale = 'en' | 'vi' | 'zh'

export type LocalizedText = Record<Locale, string>

export type DocEntry = {
  id: string
  title: LocalizedText
  eyebrow: LocalizedText
  path: string
  summary: LocalizedText
  audience: LocalizedText
  tags: string[]
  content: string
}

export type CommandEntry = {
  category: LocalizedText
  command: string
  summary: LocalizedText
  result: LocalizedText
}

export type SurfaceEntry = {
  title: LocalizedText
  description: LocalizedText
  detail: LocalizedText
}

export type RepoMapEntry = {
  path: string
  summary: LocalizedText
}

export type StatusEntry = {
  label: LocalizedText
  state: 'pass' | 'pending' | 'info'
  detail: LocalizedText
}

export type FaqEntry = {
  question: LocalizedText
  answer: LocalizedText
}

export type UiCopy = {
  sidebarIntro: LocalizedText
  searchPlaceholder: LocalizedText
  languageLabel: LocalizedText
  themeLabel: LocalizedText
  lightMode: LocalizedText
  darkMode: LocalizedText
  searchScope: LocalizedText
  docsUnit: LocalizedText
  commandsMatch: LocalizedText
  faqMatch: LocalizedText
  currentFocus: LocalizedText
  noDocumentSelected: LocalizedText
  pickDocumentHint: LocalizedText
  heroEyebrow: LocalizedText
  heroLead: LocalizedText
  heroPrimary: LocalizedText
  heroSecondary: LocalizedText
  spotlightEyebrow: LocalizedText
  surfacesEyebrow: LocalizedText
  surfacesTitle: LocalizedText
  surfacesBody: LocalizedText
  quickstartEyebrow: LocalizedText
  quickstartTitle: LocalizedText
  quickstartBody: LocalizedText
  readingOrderTitle: LocalizedText
  readingOrderItems: Record<Locale, string[]>
  calloutDocs: LocalizedText
  calloutDoctor: LocalizedText
  calloutCleanup: LocalizedText
  commandsEyebrow: LocalizedText
  commandsTitle: LocalizedText
  commandsBody: LocalizedText
  repoMapEyebrow: LocalizedText
  repoMapTitle: LocalizedText
  repoMapBody: LocalizedText
  docsEyebrow: LocalizedText
  docsTitle: LocalizedText
  docsBody: LocalizedText
  readerEyebrow: LocalizedText
  readerBody: LocalizedText
  originalMarkdownNote: LocalizedText
  sourceFile: LocalizedText
  bestFor: LocalizedText
  switchDocument: LocalizedText
  noDocMatches: LocalizedText
  releaseEyebrow: LocalizedText
  releaseTitle: LocalizedText
  releaseBody: LocalizedText
  releaseRemote: LocalizedText
  releaseHuman: LocalizedText
  releaseNext: LocalizedText
  faqEyebrow: LocalizedText
  faqTitle: LocalizedText
  faqBody: LocalizedText
  footerBody: LocalizedText
  footerTop: LocalizedText
  footerReader: LocalizedText
  footerRelease: LocalizedText
  statusPass: LocalizedText
  statusPending: LocalizedText
  statusInfo: LocalizedText
}

const t = (en: string, vi: string, zh: string): LocalizedText => ({ en, vi, zh })

export const localeOptions = [
  { code: 'en' as const, short: 'EN', nativeLabel: 'English' },
  { code: 'vi' as const, short: 'VI', nativeLabel: 'Tiếng Việt' },
  { code: 'zh' as const, short: '中', nativeLabel: '中文' },
]

export const uiCopy: UiCopy = {
  sidebarIntro: t(
    'A friendlier frontend for understanding RepoBrain without hopping across markdown files and release notes.',
    'Frontend dễ đọc hơn để hiểu RepoBrain mà không phải nhảy qua lại giữa markdown và ghi chú release.',
    '一个更友好的前端入口，帮助你理解 RepoBrain，而不必在一堆 markdown 和发布记录之间来回切换。',
  ),
  searchPlaceholder: t(
    'Search docs, commands, or release notes',
    'Tìm docs, lệnh, hoặc ghi chú release',
    '搜索文档、命令或发布说明',
  ),
  languageLabel: t('Language', 'Ngôn ngữ', '语言'),
  themeLabel: t('Appearance', 'Giao diện', '外观'),
  lightMode: t('Light', 'Sáng', '浅色'),
  darkMode: t('Dark', 'Tối', '深色'),
  searchScope: t('Search scope', 'Phạm vi tìm kiếm', '搜索范围'),
  docsUnit: t('docs', 'tài liệu', '文档'),
  commandsMatch: t('commands match', 'lệnh khớp', '条命令匹配'),
  faqMatch: t('FAQ entries match', 'mục FAQ khớp', '条 FAQ 匹配'),
  currentFocus: t('Current focus', 'Tiêu điểm hiện tại', '当前焦点'),
  noDocumentSelected: t('No document selected', 'Chưa chọn tài liệu', '尚未选择文档'),
  pickDocumentHint: t(
    'Pick a document from the library below',
    'Chọn một tài liệu trong thư viện bên dưới',
    '请从下面的文档库里选择一个文档',
  ),
  heroEyebrow: t('RepoBrain documentation frontend', 'Frontend tài liệu cho RepoBrain', 'RepoBrain 文档前端'),
  heroLead: t(
    'RepoBrain is a local-first codebase memory engine that helps AI coding assistants gather context before they generate code. This frontend turns the repository into a cleaner, easier reading experience for teammates, reviewers, and new users.',
    'RepoBrain là một codebase memory engine theo hướng local-first, giúp AI coding assistant thu thập ngữ cảnh trước khi sinh code. Frontend này biến repository thành một trải nghiệm đọc rõ ràng hơn cho teammate, reviewer và người mới.',
    'RepoBrain 是一个 local-first 的代码库记忆引擎，帮助 AI 编码助手在生成代码前先拿到正确上下文。这个前端把仓库整理成更清晰、更易读的文档体验，方便队友、评审者和新用户理解项目。',
  ),
  heroPrimary: t('Explore docs', 'Xem tài liệu', '浏览文档'),
  heroSecondary: t('Follow quickstart', 'Đi theo quickstart', '查看快速开始'),
  spotlightEyebrow: t('Why this repo matters', 'Điểm đáng chú ý của repo', '这个仓库为什么值得看'),
  surfacesEyebrow: t('Product surfaces', 'Các bề mặt sản phẩm', '产品形态'),
  surfacesTitle: t('One repo, several ways to use it', 'Một repo, nhiều cách sử dụng', '一个仓库，多种使用方式'),
  surfacesBody: t(
    'RepoBrain is no longer just a CLI experiment. The repository now includes a browser UI, ship checks, release validation, a docs frontend, and an MCP-style transport for assistant tooling.',
    'RepoBrain không còn chỉ là một thử nghiệm CLI. Repository hiện đã có browser UI, ship checks, release validation, docs frontend và transport kiểu MCP cho công cụ AI assistant.',
    'RepoBrain 已经不只是一个 CLI 实验。仓库现在同时包含浏览器界面、ship 检查、发布校验、文档前端，以及面向助手工具的 MCP 风格传输层。',
  ),
  quickstartEyebrow: t('Quickstart', 'Quickstart', '快速开始'),
  quickstartTitle: t(
    'How to understand the repo in one sitting',
    'Cách hiểu repo trong một lần đọc',
    '如何在一次阅读里快速理解这个仓库',
  ),
  quickstartBody: t(
    'This path is the shortest route from a clean clone to meaningful RepoBrain usage. It is also the easiest path for onboarding a new teammate.',
    'Đây là đường ngắn nhất từ một clean clone tới lúc dùng RepoBrain có ý nghĩa. Nó cũng là lộ trình dễ nhất để onboard một teammate mới.',
    '这是从全新 clone 到真正用起来 RepoBrain 的最短路径，也最适合给新成员做 onboarding。',
  ),
  readingOrderTitle: t('Recommended reading order', 'Thứ tự đọc gợi ý', '推荐阅读顺序'),
  readingOrderItems: {
    en: [
      '`Vision` for the why.',
      '`Install Guide` and `Run Guide` for day-one usage.',
      '`CLI Reference` and `Architecture` for behavior and design.',
      '`Production Readiness` and `Release Checklist` before demos or tags.',
    ],
    vi: [
      '`Vision` để hiểu tại sao dự án tồn tại.',
      '`Install Guide` và `Run Guide` để dùng trong ngày đầu tiên.',
      '`CLI Reference` và `Architecture` để hiểu hành vi và thiết kế.',
      '`Production Readiness` và `Release Checklist` trước khi demo hoặc gắn tag.',
    ],
    zh: [
      '`Vision` 先看项目为什么存在。',
      '`Install Guide` 和 `Run Guide` 用来快速上手。',
      '`CLI Reference` 和 `Architecture` 用来理解行为与设计。',
      '`Production Readiness` 和 `Release Checklist` 适合在演示或打 tag 前阅读。',
    ],
  },
  calloutDocs: t(
    'Use the docs library below to open any important source markdown inside this UI.',
    'Dùng thư viện docs bên dưới để mở trực tiếp các file markdown quan trọng ngay trong giao diện này.',
    '直接使用下面的文档库，在这个界面里打开重要的源 markdown 文件。',
  ),
  calloutDoctor: t(
    'Use `doctor`, `provider-smoke`, and `release-check` before claiming readiness.',
    'Dùng `doctor`, `provider-smoke` và `release-check` trước khi nói là hệ thống đã sẵn sàng.',
    '在声称系统已经就绪之前，先跑 `doctor`、`provider-smoke` 和 `release-check`。',
  ),
  calloutCleanup: t(
    'Use `demo-clean` before a live session so the repo feels intentional instead of cluttered.',
    'Dùng `demo-clean` trước buổi live demo để repo trông gọn gàng và có chủ đích hơn.',
    '在现场演示前运行 `demo-clean`，让仓库看起来更整洁、更有准备，而不是一堆临时文件。',
  ),
  commandsEyebrow: t('Command catalog', 'Danh mục lệnh', '命令目录'),
  commandsTitle: t(
    'What people actually run',
    'Những lệnh mọi người thực sự dùng',
    '大家实际会运行的命令',
  ),
  commandsBody: t(
    'These are the commands that matter most in onboarding, demos, release checks, and day-to-day investigation.',
    'Đây là những lệnh quan trọng nhất trong onboarding, demo, release check và lúc điều tra hằng ngày.',
    '这些命令最常出现在 onboarding、演示、发布检查以及日常排查中。',
  ),
  repoMapEyebrow: t('Repo map', 'Bản đồ repo', '仓库地图'),
  repoMapTitle: t(
    'Where to look when you need source, UX, or release logic',
    'Nên nhìn vào đâu khi cần source, UX hoặc logic phát hành',
    '当你需要看源码、UX 或发布逻辑时该先看哪里',
  ),
  repoMapBody: t(
    'RepoBrain mixes Python, React, docs, tests, and release automation. This map gives contributors a cleaner mental model of the top-level structure.',
    'RepoBrain trộn Python, React, docs, tests và release automation. Bản đồ này giúp contributor có mô hình tư duy rõ hơn về cấu trúc cấp cao của repo.',
    'RepoBrain 同时包含 Python、React、文档、测试和发布自动化。这个地图能帮助贡献者快速建立对顶层结构的清晰认知。',
  ),
  docsEyebrow: t('Docs library', 'Thư viện docs', '文档库'),
  docsTitle: t(
    'Open the repo docs without leaving the frontend',
    'Mở docs của repo mà không cần rời frontend',
    '不离开前端界面就能阅读仓库文档',
  ),
  docsBody: t(
    'Pick any important markdown source and read it below in the reading room. Search helps when you only remember a topic, not a file name.',
    'Chọn bất kỳ file markdown quan trọng nào và đọc ngay ở reading room bên dưới. Search giúp ích khi bạn chỉ nhớ chủ đề chứ không nhớ tên file.',
    '选择任意重要的 markdown 源文件，并在下面的阅读区直接查看。当你只记得主题、不记得文件名时，搜索会很有帮助。',
  ),
  readerEyebrow: t('Reading room', 'Reading room', '阅读区'),
  readerBody: t(
    'This section renders source markdown directly from the repository so the docs frontend stays aligned with the actual project documents.',
    'Phần này render trực tiếp markdown nguồn từ repository để frontend tài liệu luôn đồng bộ với tài liệu thật của dự án.',
    '这一部分直接渲染仓库里的源 markdown，因此文档前端会始终与项目真实文档保持一致。',
  ),
  originalMarkdownNote: t(
    'Source markdown stays in its original repository language below.',
    'Markdown gốc bên dưới vẫn giữ nguyên ngôn ngữ gốc của repository.',
    '下面展示的 markdown 保持仓库中的原始语言，不做机器改写。',
  ),
  sourceFile: t('Source file', 'File nguồn', '源文件'),
  bestFor: t('Best for', 'Phù hợp nhất cho', '最适合'),
  switchDocument: t('Switch document', 'Đổi tài liệu', '切换文档'),
  noDocMatches: t(
    'No document matches the current search. Clear the search box to reopen the full docs library.',
    'Không có tài liệu nào khớp với tìm kiếm hiện tại. Hãy xóa từ khóa để mở lại toàn bộ thư viện docs.',
    '当前搜索没有匹配的文档。清空搜索词即可重新看到完整文档库。',
  ),
  releaseEyebrow: t('Release state', 'Trạng thái release', '发布状态'),
  releaseTitle: t(
    'What is done locally, and what still needs real-world validation',
    'Những gì đã xong cục bộ và những gì vẫn cần kiểm chứng thật',
    '哪些工作已经在本地完成，哪些还需要真实环境验证',
  ),
  releaseBody: t(
    'RepoBrain is already much stronger locally. The biggest remaining uncertainty is no longer packaging logic, but remote workflow execution and real provider access.',
    'RepoBrain hiện đã mạnh hơn rất nhiều ở local. Điểm chưa chắc chắn lớn nhất không còn là packaging logic nữa mà là remote workflow và quyền truy cập provider thật.',
    'RepoBrain 在本地已经成熟很多。现在最大的未知不再是打包逻辑，而是远程 workflow 执行以及真实 provider 的访问能力。',
  ),
  releaseRemote: t(
    'Remote publish validation still depends on GitHub workflow access and real credentials. That part cannot be honestly marked done from UI work alone.',
    'Kiểm chứng publish ở môi trường remote vẫn phụ thuộc vào quyền GitHub workflow và credential thật. Phần này không thể trung thực mà đánh dấu là done chỉ nhờ làm UI.',
    '远程发布验证仍然依赖 GitHub workflow 权限和真实凭据。这部分不能仅靠 UI 工作就被诚实地标记为完成。',
  ),
  releaseHuman: t(
    'The local product is now easier to explain to humans, which makes future demos, onboarding, and OSS storytelling materially better.',
    'Sản phẩm local giờ đã dễ giải thích hơn cho con người, điều này giúp demo, onboarding và câu chuyện OSS sau này tốt hơn hẳn.',
    '本地产品现在更容易向人解释，这会显著提升后续的演示、onboarding 和开源叙事。',
  ),
  releaseNext: t(
    'Once remote auth is available, the next practical move is to push `master`, trigger the release workflow with `publish=false`, and inspect the produced artifacts.',
    'Khi có remote auth, bước hợp lý tiếp theo là push `master`, kích hoạt release workflow với `publish=false`, rồi kiểm tra artifact sinh ra.',
    '一旦拿到远程认证，下一步就应该 push `master`，用 `publish=false` 触发发布 workflow，然后检查生成的 artifact。',
  ),
  faqEyebrow: t('FAQ', 'FAQ', '常见问题'),
  faqTitle: t('Questions teammates ask first', 'Những câu hỏi teammate hay hỏi đầu tiên', '团队最先会问的问题'),
  faqBody: t(
    'These answers are tuned for onboarding conversations, project reviews, and demo preparation.',
    'Các câu trả lời này được viết để phù hợp với onboarding, review dự án và chuẩn bị demo.',
    '这些回答主要针对 onboarding、项目评审和演示准备场景。',
  ),
  footerBody: t(
    'Built as a readable docs frontend for the RepoBrain repository. Use it alongside the source docs, not instead of them.',
    'Được xây như một frontend tài liệu dễ đọc cho repository RepoBrain. Hãy dùng nó song song với docs nguồn, không phải thay thế hoàn toàn.',
    '这是为 RepoBrain 仓库构建的可读性更强的文档前端。请把它作为源文档的补充，而不是替代品。',
  ),
  footerTop: t('Back to top', 'Lên đầu trang', '回到顶部'),
  footerReader: t('Open reading room', 'Mở reading room', '打开阅读区'),
  footerRelease: t('Check release state', 'Xem trạng thái release', '查看发布状态'),
  statusPass: t('pass', 'pass', '通过'),
  statusPending: t('pending', 'chờ', '待完成'),
  statusInfo: t('info', 'thông tin', '信息'),
}

export const navigationSections = [
  { id: 'overview', label: t('Overview', 'Tổng quan', '概览') },
  { id: 'surfaces', label: t('Product Surfaces', 'Bề mặt sản phẩm', '产品形态') },
  { id: 'quickstart', label: t('Quickstart', 'Quickstart', '快速开始') },
  { id: 'commands', label: t('Command Catalog', 'Danh mục lệnh', '命令目录') },
  { id: 'repo-map', label: t('Repo Map', 'Bản đồ repo', '仓库地图') },
  { id: 'docs-library', label: t('Docs Library', 'Thư viện docs', '文档库') },
  { id: 'reader', label: t('Reading Room', 'Reading room', '阅读区') },
  { id: 'release-state', label: t('Release State', 'Trạng thái release', '发布状态') },
  { id: 'faq', label: t('FAQ', 'FAQ', '常见问题') },
]

export const heroMetrics = [
  {
    value: t('CLI + Web + MCP', 'CLI + Web + MCP', 'CLI + Web + MCP'),
    label: t('Ways to use RepoBrain', 'Các cách dùng RepoBrain', 'RepoBrain 的使用方式'),
  },
  {
    value: t('Local-first', 'Local-first', 'Local-first'),
    label: t('Default security posture', 'Tư thế bảo mật mặc định', '默认安全姿态'),
  },
  {
    value: t('0.5.x track', 'Nhánh 0.5.x', '0.5.x 路线'),
    label: t('Current integration line', 'Hướng tích hợp hiện tại', '当前集成路线'),
  },
  {
    value: t('Docs reader', 'Trình đọc docs', '文档阅读器'),
    label: t('Built for faster onboarding', 'Tối ưu cho onboarding nhanh', '为更快 onboarding 而做'),
  },
]

export const surfaces: SurfaceEntry[] = [
  {
    title: t('Grounded CLI', 'CLI có grounding', 'Grounded CLI'),
    description: t(
      'Start with `init`, `review`, `index`, and `query` to answer codebase questions with evidence.',
      'Bắt đầu bằng `init`, `review`, `index` và `query` để trả lời câu hỏi về codebase bằng bằng chứng.',
      '从 `init`、`review`、`index` 和 `query` 开始，用证据回答关于代码库的问题。',
    ),
    detail: t(
      'The CLI is still the fastest path for engineers who want concrete file paths, snippets, edit targets, and ship checks.',
      'CLI vẫn là con đường nhanh nhất cho kỹ sư cần file path cụ thể, snippet, edit target và ship check.',
      '对于想要具体文件路径、片段、编辑目标和 ship 检查的工程师来说，CLI 仍然是最快的入口。',
    ),
  },
  {
    title: t('Browser UI', 'Giao diện trình duyệt', '浏览器界面'),
    description: t(
      'Use `repobrain serve-web --open` when you want a friendly local interface for import, review, doctor, and provider smoke.',
      'Dùng `repobrain serve-web --open` khi bạn muốn giao diện local thân thiện cho import, review, doctor và provider smoke.',
      '当你需要一个更友好的本地界面来做导入、review、doctor 和 provider smoke 时，使用 `repobrain serve-web --open`。',
    ),
    detail: t(
      'The React UI is local-only and already ships inside the main RepoBrain package through `webapp/dist`.',
      'UI React này chạy local-only và đã được đóng gói sẵn trong package chính qua `webapp/dist`.',
      '这个 React 界面是纯本地的，并且已经通过 `webapp/dist` 一起打包进主 RepoBrain 包中。',
    ),
  },
  {
    title: t('Release safety', 'An toàn phát hành', '发布安全'),
    description: t(
      'Use `release-check`, `python -m build`, and `demo-clean` to keep packaging and demo flows predictable.',
      'Dùng `release-check`, `python -m build` và `demo-clean` để giữ quy trình đóng gói và demo ổn định, dễ đoán.',
      '使用 `release-check`、`python -m build` 和 `demo-clean`，让打包与演示流程更可控、更可预期。',
    ),
    detail: t(
      'This track validates built artifacts, frontend packaging, and safe cleanup of test/build clutter before a live session.',
      'Nhánh này kiểm tra artifact build, frontend packaging và việc dọn rác test/build an toàn trước buổi live.',
      '这条路线会校验构建产物、前端打包情况，以及在现场演示前安全清理测试/构建杂项。',
    ),
  },
  {
    title: t('Agent transport', 'Transport cho agent', 'Agent 传输层'),
    description: t(
      'Use `serve-mcp` to expose RepoBrain tools to coding assistants that speak MCP-style stdio transports.',
      'Dùng `serve-mcp` để mở công cụ RepoBrain cho coding assistant có thể nói chuyện bằng stdio transport kiểu MCP.',
      '使用 `serve-mcp` 将 RepoBrain 工具暴露给支持 MCP 风格 stdio 传输的编码助手。',
    ),
    detail: t(
      'RepoBrain exists to improve context gathering before code generation, especially for multi-file or flow-tracing tasks.',
      'RepoBrain tồn tại để cải thiện bước thu thập ngữ cảnh trước khi generate code, nhất là với tác vụ nhiều file hoặc trace flow.',
      'RepoBrain 的核心目标是在生成代码之前先提升上下文收集质量，尤其适合多文件和流程追踪任务。',
    ),
  },
]

export const quickstartSteps = [
  {
    title: t('Install the dev stack', 'Cài bộ dev stack', '安装开发环境'),
    body: t(
      'Create a virtual environment, install the editable package, then keep everything local by default.',
      'Tạo virtual environment, cài editable package, rồi giữ mặc định mọi thứ ở local.',
      '先创建虚拟环境，再安装 editable package，默认保持所有流程在本地完成。',
    ),
    command: 'python -m pip install -e ".[dev,tree-sitter,mcp]"',
  },
  {
    title: t('Initialize one repo once', 'Khởi tạo repo một lần', '初始化一次仓库'),
    body: t(
      'Run `repobrain init --repo <path>` and let RepoBrain remember the active project for later commands.',
      'Chạy `repobrain init --repo <path>` để RepoBrain nhớ active project cho các lệnh sau.',
      '运行 `repobrain init --repo <path>`，让 RepoBrain 记住当前项目，后续命令就能复用。',
    ),
    command: 'repobrain init --repo "C:\\path\\to\\your-project" --format text',
  },
  {
    title: t('Scan, then index', 'Quét trước, index sau', '先扫描，再建立索引'),
    body: t(
      'Use `review` to understand the repo quickly, then build the local memory index for grounded retrieval.',
      'Dùng `review` để hiểu repo nhanh, rồi build local memory index cho grounded retrieval.',
      '先用 `review` 快速理解仓库，再构建本地 memory index，用于 grounded retrieval。',
    ),
    command: 'repobrain review --format text\nrepobrain index --format text',
  },
  {
    title: t('Ask operational questions', 'Đặt câu hỏi vận hành', '提出实际问题'),
    body: t(
      'Use `query`, `trace`, and `targets` when you need evidence for where logic lives and what is safest to touch next.',
      'Dùng `query`, `trace` và `targets` khi bạn cần bằng chứng logic nằm ở đâu và nên chạm vào file nào tiếp theo.',
      '当你需要知道逻辑在哪、下一步改哪个文件最安全时，用 `query`、`trace` 和 `targets`。',
    ),
    command: 'repobrain query "Where is payment retry logic implemented?" --format text',
  },
  {
    title: t('Close with ship and release gates', 'Chốt bằng ship và release gate', '最后通过 ship 与发布门禁收尾'),
    body: t(
      'Use `ship`, `release-check`, and `demo-clean` when moving from development toward demo or release.',
      'Dùng `ship`, `release-check` và `demo-clean` khi chuyển từ giai đoạn development sang demo hoặc release.',
      '当你从开发阶段走向演示或发布时，用 `ship`、`release-check` 和 `demo-clean` 收尾。',
    ),
    command: 'repobrain ship --format text\nrepobrain release-check --require-dist --format text\nrepobrain demo-clean --format text',
  },
]

export const commandCatalog: CommandEntry[] = [
  {
    category: t('Setup', 'Thiết lập', '初始化'),
    command: 'repobrain init --repo "<path>" --format text',
    summary: t(
      'Create local RepoBrain state and remember the active project.',
      'Tạo local state cho RepoBrain và ghi nhớ active project.',
      '创建 RepoBrain 的本地状态，并记住当前激活项目。',
    ),
    result: t(
      'Generates `.repobrain/`, `repobrain.toml`, and an active-repo pointer.',
      'Sinh ra `.repobrain/`, `repobrain.toml` và con trỏ active-repo.',
      '生成 `.repobrain/`、`repobrain.toml` 以及 active-repo 指针。',
    ),
  },
  {
    category: t('Exploration', 'Khám phá', '探索'),
    command: 'repobrain review --format text',
    summary: t(
      'Get the fastest risk-oriented scan of a repo before indexing.',
      'Nhận bản scan định hướng rủi ro nhanh nhất của repo trước khi index.',
      '在建立索引前，先拿到一份面向风险的快速扫描结果。',
    ),
    result: t(
      'Shows security, production, and code-quality findings in plain English.',
      'Hiển thị các phát hiện về security, production và code quality bằng ngôn ngữ dễ đọc.',
      '用易读语言展示安全、生产和代码质量方面的主要发现。',
    ),
  },
  {
    category: t('Exploration', 'Khám phá', '探索'),
    command: 'repobrain index --format text',
    summary: t(
      'Build the local metadata and vector index used by retrieval flows.',
      'Xây metadata local và vector index dùng cho các luồng truy xuất.',
      '构建本地元数据和向量索引，为检索流程提供基础。',
    ),
    result: t(
      'Reports files, chunks, symbols, edges, and parser usage stats.',
      'Báo cáo files, chunks, symbols, edges và thống kê parser usage.',
      '输出文件、chunks、symbols、edges 以及 parser 使用统计。',
    ),
  },
  {
    category: t('Retrieval', 'Truy xuất', '检索'),
    command: 'repobrain query "<question>" --format text',
    summary: t(
      'Answer locate-style questions with top files, snippets, and confidence.',
      'Trả lời câu hỏi kiểu locate bằng top files, snippets và confidence.',
      '用 top files、snippets 和 confidence 回答定位类问题。',
    ),
    result: t(
      'Returns grounded retrieval evidence instead of a vague repo summary.',
      'Trả về bằng chứng grounded retrieval thay vì một bản tóm tắt mơ hồ về repo.',
      '返回有依据的检索证据，而不是模糊的仓库概述。',
    ),
  },
  {
    category: t('Retrieval', 'Truy xuất', '检索'),
    command: 'repobrain trace "<question>" --format text',
    summary: t(
      'Bias the engine toward route-to-service or job-to-handler flows.',
      'Thiên engine về các luồng route-to-service hoặc job-to-handler.',
      '让引擎更偏向 route-to-service 或 job-to-handler 的流程追踪。',
    ),
    result: t(
      'Highlights likely call chains and dependency edges.',
      'Làm nổi bật call chain khả dĩ và dependency edges.',
      '突出展示可能的调用链和依赖边。',
    ),
  },
  {
    category: t('Retrieval', 'Truy xuất', '检索'),
    command: 'repobrain targets "<question>" --format text',
    summary: t(
      'Rank the safest files to inspect or edit next for a requested change.',
      'Xếp hạng các file an toàn nhất để inspect hoặc sửa tiếp cho một thay đổi được yêu cầu.',
      '为某个需求变更排序出最安全的下一步查看或修改文件。',
    ),
    result: t(
      'Returns edit targets with explicit rationale.',
      'Trả về edit targets kèm lý do rõ ràng.',
      '返回带明确理由的 edit targets。',
    ),
  },
  {
    category: t('Operations', 'Vận hành', '运维'),
    command: 'repobrain doctor --format text',
    summary: t(
      'Inspect provider readiness, parser posture, and index health.',
      'Kiểm tra độ sẵn sàng của provider, trạng thái parser và sức khỏe index.',
      '检查 provider 就绪度、parser 状态和索引健康度。',
    ),
    result: t(
      'Confirms whether the current local configuration is actually usable.',
      'Xác nhận cấu hình local hiện tại có thực sự dùng được hay không.',
      '确认当前本地配置是否真的可用。',
    ),
  },
  {
    category: t('Operations', 'Vận hành', '运维'),
    command: 'repobrain provider-smoke --format text',
    summary: t(
      'Run a direct embedding/reranker smoke check through configured providers.',
      'Chạy smoke check trực tiếp embedding/reranker qua provider đã cấu hình.',
      '通过已配置 provider 直接运行 embedding/reranker 的 smoke check。',
    ),
    result: t(
      'Validates the real provider path before you trust it in production flows.',
      'Kiểm chứng đường đi provider thật trước khi tin nó trong production flow.',
      '在你把它用于生产流程之前，先验证真实 provider 路径。',
    ),
  },
  {
    category: t('Operations', 'Vận hành', '运维'),
    command: 'repobrain ship --format text',
    summary: t(
      'Run a higher-level production-readiness gate across review, benchmark, and health signals.',
      'Chạy gate production-readiness ở mức cao hơn, gom review, benchmark và health signals.',
      '运行更高层的 production-readiness 门禁，综合 review、benchmark 和健康信号。',
    ),
    result: t(
      'Summarizes whether the project is blocked, cautionary, or ready.',
      'Tóm tắt dự án đang bị chặn, cần cẩn trọng hay đã sẵn sàng.',
      '总结项目当前是被阻塞、需谨慎，还是已经就绪。',
    ),
  },
  {
    category: t('Docs', 'Tài liệu', '文档'),
    command: 'repobrain report --open',
    summary: t(
      'Generate and open the local HTML report/dashboard.',
      'Sinh và mở report/dashboard HTML cục bộ.',
      '生成并打开本地 HTML 报告/看板。',
    ),
    result: t(
      'Good for demos, screenshots, and non-terminal teammates.',
      'Phù hợp cho demo, chụp màn hình và teammate không thích terminal.',
      '适合做演示、截图，或给不常用终端的队友使用。',
    ),
  },
  {
    category: t('Web', 'Web', 'Web'),
    command: 'repobrain serve-web --open',
    summary: t(
      'Start the browser UI for import, review, question-answering, and diagnostics.',
      'Mở browser UI cho import, review, hỏi đáp và diagnostics.',
      '启动浏览器界面，用于导入、review、问答和诊断。',
    ),
    result: t(
      'Serves the built React frontend from `webapp/dist`.',
      'Phục vụ frontend React đã build từ `webapp/dist`.',
      '直接从 `webapp/dist` 提供已构建的 React 前端。',
    ),
  },
  {
    category: t('Release', 'Phát hành', '发布'),
    command: 'python -m build',
    summary: t(
      'Build the wheel and sdist artifacts that the release workflow expects.',
      'Build wheel và sdist artifact mà release workflow đang chờ.',
      '构建发布 workflow 所需要的 wheel 和 sdist artifact。',
    ),
    result: t(
      'Creates `dist/*.whl` and `dist/*.tar.gz` for artifact validation.',
      'Tạo `dist/*.whl` và `dist/*.tar.gz` để kiểm tra artifact.',
      '生成 `dist/*.whl` 与 `dist/*.tar.gz` 以供 artifact 校验。',
    ),
  },
  {
    category: t('Release', 'Phát hành', '发布'),
    command: 'repobrain release-check --require-dist --format text',
    summary: t(
      'Validate version alignment and built artifact contents before publishing.',
      'Kiểm tra version alignment và nội dung artifact đã build trước khi publish.',
      '在发布前校验版本一致性和构建 artifact 内容。',
    ),
    result: t(
      'Confirms the wheel and sdist include the React frontend assets.',
      'Xác nhận wheel và sdist có chứa frontend assets của React.',
      '确认 wheel 和 sdist 都包含 React 前端资源。',
    ),
  },
  {
    category: t('Demo', 'Demo', '演示'),
    command: 'repobrain demo-clean --format text',
    summary: t(
      'Remove temporary build/test clutter without breaking the browser demo.',
      'Xóa rác build/test tạm thời mà không làm hỏng browser demo.',
      '清理临时的 build/test 杂项，同时不破坏浏览器演示。',
    ),
    result: t(
      'Preserves `webapp/dist` and the root `.repobrain` workspace state by default.',
      'Mặc định giữ lại `webapp/dist` và state `.repobrain` ở thư mục gốc.',
      '默认保留 `webapp/dist` 和根目录下的 `.repobrain` 工作区状态。',
    ),
  },
]

export const repoMap: RepoMapEntry[] = [
  {
    path: 'src/repobrain',
    summary: t(
      'Python package with the engine, CLI, review flow, provider adapters, release checks, and web server.',
      'Python package chứa engine, CLI, review flow, provider adapters, release checks và web server.',
      'Python 包，包含引擎、CLI、review 流程、provider 适配器、release 检查和 web server。',
    ),
  },
  {
    path: 'webapp',
    summary: t(
      'React frontend for the local RepoBrain browser UI that ships inside the package as built assets.',
      'Frontend React cho browser UI local của RepoBrain, được đóng gói cùng package dưới dạng built assets.',
      '本地 RepoBrain 浏览器界面的 React 前端，会作为构建资源一起打包进主项目。',
    ),
  },
  {
    path: 'docs',
    summary: t(
      'Primary markdown documentation set covering install, run, CLI, architecture, release, evaluation, and product direction.',
      'Bộ markdown tài liệu chính, bao gồm cài đặt, chạy, CLI, kiến trúc, phát hành, đánh giá và định hướng sản phẩm.',
      '核心 markdown 文档集合，覆盖安装、运行、CLI、架构、发布、评估与产品方向。',
    ),
  },
  {
    path: 'tests',
    summary: t(
      'Pytest suite for CLI, providers, release validation, review flows, and web routes.',
      'Bộ pytest cho CLI, providers, release validation, review flows và web routes.',
      '覆盖 CLI、providers、release 校验、review 流程和 web routes 的 pytest 测试集。',
    ),
  },
  {
    path: '.github/workflows',
    summary: t(
      'Automation for CI and release flows, including strict release artifact validation.',
      'Automation cho CI và release flows, bao gồm strict validation cho release artifact.',
      'CI 与发布流程的自动化目录，其中包含严格的 release artifact 校验。',
    ),
  },
  {
    path: 'docs-for-repobrain',
    summary: t(
      'This documentation frontend, built to make RepoBrain easier to read and onboard without opening every markdown file manually.',
      'Frontend tài liệu này được làm để RepoBrain dễ đọc và dễ onboard hơn mà không phải mở tay từng file markdown.',
      '这个文档前端就是为了让 RepoBrain 更容易阅读和 onboarding，而不必手动打开每个 markdown 文件。',
    ),
  },
]

export const releaseStatus: StatusEntry[] = [
  {
    label: t('Local packaging fixes', 'Sửa lỗi đóng gói local', '本地打包修复'),
    state: 'pass',
    detail: t(
      'Wheel packaging now includes `webapp/dist`, and invalid metadata blockers were already fixed earlier in the branch history.',
      'Wheel hiện đã đóng gói cả `webapp/dist`, và các blocker metadata không hợp lệ cũng đã được sửa từ trước trong lịch sử nhánh.',
      '`webapp/dist` 现在已经被正确打进 wheel，之前的无效 metadata 阻塞也已在更早的分支历史中修复。',
    ),
  },
  {
    label: t('Release validation tooling', 'Công cụ kiểm tra phát hành', '发布校验工具'),
    state: 'pass',
    detail: t(
      '`repobrain release-check` and `repobrain demo-clean` are available locally and documented for operator use.',
      '`repobrain release-check` và `repobrain demo-clean` đã dùng được ở local và đã có tài liệu cho người vận hành.',
      '`repobrain release-check` 和 `repobrain demo-clean` 已经可以在本地使用，并且有面向操作者的文档说明。',
    ),
  },
  {
    label: t('Docs frontend', 'Frontend tài liệu', '文档前端'),
    state: 'info',
    detail: t(
      'This docs app is the new human-friendly frontend for understanding the repo, commands, and release posture.',
      'App tài liệu này là frontend thân thiện hơn với con người để hiểu repo, lệnh và trạng thái release.',
      '这个文档应用是新的面向人类的前端，用来理解仓库、命令以及发布状态。',
    ),
  },
  {
    label: t('Remote release workflow', 'Release workflow từ xa', '远程发布 workflow'),
    state: 'pending',
    detail: t(
      'Still depends on GitHub auth and remote workflow execution, so it cannot be declared complete until that path actually runs.',
      'Vẫn phụ thuộc vào GitHub auth và việc chạy workflow từ xa, nên chưa thể coi là hoàn tất cho tới khi đường đó chạy thật.',
      '仍然依赖 GitHub 认证和远程 workflow 执行，因此在这条路径真正跑通之前，不能算已经完成。',
    ),
  },
  {
    label: t('Live provider smoke', 'Smoke test provider thật', '真实 provider smoke'),
    state: 'pending',
    detail: t(
      'Still depends on real API keys and provider access beyond the local mocked/default path.',
      'Vẫn phụ thuộc vào API key thật và quyền truy cập provider ngoài đường local mặc định/mocked.',
      '仍然依赖真实 API key 与 provider 访问能力，超出了本地默认或 mock 路径。',
    ),
  },
]

export const faqs: FaqEntry[] = [
  {
    question: t(
      'What problem is RepoBrain actually solving?',
      'RepoBrain thực sự giải quyết vấn đề gì?',
      'RepoBrain 到底在解决什么问题？',
    ),
    answer: t(
      'RepoBrain reduces bad code generation by fixing the step before code generation: finding the right files, tracing real flows, surfacing evidence, and lowering confidence when the evidence is weak.',
      'RepoBrain giảm việc sinh code sai bằng cách sửa đúng bước trước khi generate code: tìm đúng file, trace đúng flow, đưa bằng chứng ra rõ ràng và hạ confidence khi bằng chứng yếu.',
      'RepoBrain 通过修复“生成代码之前”的那一步来减少错误代码生成：找到正确文件、追踪真实流程、展示证据，并在证据不足时主动降低置信度。',
    ),
  },
  {
    question: t(
      'Should I start with `review` or `index`?',
      'Nên bắt đầu bằng `review` hay `index`?',
      '我应该先用 `review` 还是 `index`？',
    ),
    answer: t(
      'Start with `review` when you need a quick human summary of risks. Start with `index` when you are ready for grounded retrieval, tracing, and edit-target ranking.',
      'Bắt đầu với `review` khi bạn cần một bản tóm tắt rủi ro nhanh cho con người. Bắt đầu với `index` khi bạn đã sẵn sàng cho grounded retrieval, trace và xếp hạng edit target.',
      '如果你想先快速得到一份面向人的风险摘要，就从 `review` 开始。如果你已经准备进入 grounded retrieval、trace 和 edit target 排序，就从 `index` 开始。',
    ),
  },
  {
    question: t(
      'When does the browser UI matter?',
      'Khi nào browser UI thực sự hữu ích?',
      '浏览器界面什么时候真正有价值？',
    ),
    answer: t(
      'Use the browser UI when you want a local-first experience for demos, onboarding, or teammates who prefer forms and panels over terminal commands.',
      'Dùng browser UI khi bạn muốn trải nghiệm local-first cho demo, onboarding hoặc cho teammate thích form và panel hơn là terminal commands.',
      '当你需要一个适合演示、onboarding，或者更适合不喜欢命令行的队友使用的 local-first 界面时，就用浏览器 UI。',
    ),
  },
  {
    question: t(
      'How do I know whether remote providers are safe to use?',
      'Làm sao biết remote providers có an toàn để dùng không?',
      '我怎么判断远程 providers 是否可以安全使用？',
    ),
    answer: t(
      'Treat remote providers as opt-in. Use `repobrain doctor` and `repobrain provider-smoke` first, and remember RepoBrain stays local-first until you explicitly switch providers in `repobrain.toml`.',
      'Hãy coi remote providers là opt-in. Chạy `repobrain doctor` và `repobrain provider-smoke` trước, và nhớ rằng RepoBrain vẫn local-first cho tới khi bạn chủ động đổi provider trong `repobrain.toml`.',
      '把远程 providers 视为显式 opt-in。先跑 `repobrain doctor` 和 `repobrain provider-smoke`，并记住：在你明确修改 `repobrain.toml` 之前，RepoBrain 默认仍然是 local-first。',
    ),
  },
  {
    question: t(
      'Why is there a dedicated `demo-clean` command?',
      'Vì sao lại có lệnh `demo-clean` riêng?',
      '为什么会有一个专门的 `demo-clean` 命令？',
    ),
    answer: t(
      'The repo accumulates heavy temporary folders during test/build cycles on Windows. `demo-clean` removes that clutter safely without deleting the frontend assets needed by `serve-web`.',
      'Repo tích tụ rất nhiều thư mục tạm trong quá trình test/build trên Windows. `demo-clean` xóa phần rác đó một cách an toàn mà không xóa frontend assets cần cho `serve-web`.',
      '这个仓库在 Windows 上跑测试和构建时会积累很多临时目录。`demo-clean` 能安全清掉这些杂项，同时不会删掉 `serve-web` 所需要的前端资源。',
    ),
  },
]

export const docsLibrary: DocEntry[] = [
  {
    id: 'vision',
    title: t('Vision', 'Tầm nhìn', '愿景'),
    eyebrow: t('Product direction', 'Định hướng sản phẩm', '产品方向'),
    path: 'docs/vision.md',
    summary: t(
      'Why RepoBrain exists, what behavior it is trying to change in coding assistants, and what success looks like.',
      'Vì sao RepoBrain tồn tại, nó đang cố thay đổi hành vi nào của coding assistant, và thế nào là thành công.',
      '为什么 RepoBrain 存在、它想改变编码助手的哪些行为，以及成功应该是什么样子。',
    ),
    audience: t('Founders, reviewers, new contributors', 'Founder, reviewer, contributor mới', '创始人、评审者、新贡献者'),
    tags: ['product', 'direction', 'why'],
    content: visionDoc,
  },
  {
    id: 'install',
    title: t('Install Guide', 'Hướng dẫn cài đặt', '安装指南'),
    eyebrow: t('Get started', 'Bắt đầu', '开始使用'),
    path: 'docs/install.md',
    summary: t(
      'Environment setup, package installation, and the minimum path to first use.',
      'Thiết lập môi trường, cài package và con đường ngắn nhất để dùng lần đầu.',
      '环境配置、包安装，以及第一次用起来的最短路径。',
    ),
    audience: t('Anyone onboarding to the repo', 'Bất kỳ ai đang onboard vào repo', '所有正在上手这个仓库的人'),
    tags: ['install', 'onboarding', 'setup'],
    content: installDoc,
  },
  {
    id: 'run',
    title: t('Run Guide', 'Hướng dẫn chạy', '运行指南'),
    eyebrow: t('Daily workflow', 'Luồng làm việc hằng ngày', '日常工作流'),
    path: 'docs/run.md',
    summary: t(
      'How to run RepoBrain from CLI, browser UI, report mode, MCP mode, and demo prep flows.',
      'Cách chạy RepoBrain từ CLI, browser UI, report mode, MCP mode và các luồng chuẩn bị demo.',
      '如何通过 CLI、浏览器界面、report 模式、MCP 模式以及演示准备流程来运行 RepoBrain。',
    ),
    audience: t('Users and operators', 'Người dùng và người vận hành', '用户与操作者'),
    tags: ['run', 'workflow', 'demo'],
    content: runDoc,
  },
  {
    id: 'cli',
    title: t('CLI Reference', 'Tham chiếu CLI', 'CLI 参考'),
    eyebrow: t('Command surface', 'Bề mặt lệnh', '命令表面'),
    path: 'docs/cli.md',
    summary: t(
      'Descriptions of every primary command, what it returns, and how the tools fit together.',
      'Mô tả từng lệnh chính, những gì nó trả về và cách các công cụ khớp với nhau.',
      '每个核心命令的说明、返回内容，以及这些工具之间如何配合。',
    ),
    audience: t('Power users and maintainers', 'Power user và maintainer', '高级用户与维护者'),
    tags: ['cli', 'commands', 'reference'],
    content: cliDoc,
  },
  {
    id: 'architecture',
    title: t('Architecture', 'Kiến trúc', '架构'),
    eyebrow: t('System design', 'Thiết kế hệ thống', '系统设计'),
    path: 'docs/architecture.md',
    summary: t(
      'The retrieval engine, indexing model, grounding flow, and major design tradeoffs behind RepoBrain.',
      'Retrieval engine, mô hình indexing, grounding flow và các tradeoff thiết kế chính của RepoBrain.',
      'RepoBrain 背后的检索引擎、索引模型、grounding 流程以及主要设计取舍。',
    ),
    audience: t('Engineers reading the core design', 'Kỹ sư muốn đọc thiết kế lõi', '阅读核心设计的工程师'),
    tags: ['architecture', 'engine', 'design'],
    content: architectureDoc,
  },
  {
    id: 'mcp',
    title: t('MCP', 'MCP', 'MCP'),
    eyebrow: t('Agent integration', 'Tích hợp agent', 'Agent 集成'),
    path: 'docs/mcp.md',
    summary: t(
      'How RepoBrain exposes tools over a stdio transport for coding assistants and automation layers.',
      'Cách RepoBrain mở công cụ qua stdio transport cho coding assistant và các lớp automation.',
      'RepoBrain 如何通过 stdio transport 暴露工具，供编码助手和自动化层使用。',
    ),
    audience: t('Tooling engineers and agent builders', 'Kỹ sư tooling và người xây agent', '工具工程师与 agent 构建者'),
    tags: ['mcp', 'agent', 'integration'],
    content: mcpDoc,
  },
  {
    id: 'ux',
    title: t('User Experience', 'Trải nghiệm người dùng', '用户体验'),
    eyebrow: t('Interaction design', 'Thiết kế tương tác', '交互设计'),
    path: 'docs/ux.md',
    summary: t(
      'What the human-facing product should feel like across CLI, report, and browser surfaces.',
      'Trải nghiệm sản phẩm hướng con người nên như thế nào trên CLI, report và browser UI.',
      '面向人的产品体验在 CLI、report 和浏览器界面上应该呈现成什么样。',
    ),
    audience: t('Product and frontend contributors', 'Contributor về product và frontend', '产品与前端贡献者'),
    tags: ['ux', 'frontend', 'design'],
    content: uxDoc,
  },
  {
    id: 'evaluation',
    title: t('Evaluation', 'Đánh giá', '评估'),
    eyebrow: t('Quality signals', 'Tín hiệu chất lượng', '质量信号'),
    path: 'docs/evaluation.md',
    summary: t(
      'How retrieval quality is measured and what metrics matter for RepoBrain confidence.',
      'Cách đo chất lượng retrieval và metric nào quan trọng đối với confidence của RepoBrain.',
      '如何衡量检索质量，以及哪些指标会影响 RepoBrain 的置信度。',
    ),
    audience: t('Engineers tuning relevance and safety', 'Kỹ sư tinh chỉnh relevance và safety', '调优相关性与安全性的工程师'),
    tags: ['evaluation', 'benchmark', 'quality'],
    content: evaluationDoc,
  },
  {
    id: 'production-readiness',
    title: t('Production Readiness', 'Sẵn sàng production', '生产就绪'),
    eyebrow: t('Operator checklist', 'Checklist vận hành', '操作者清单'),
    path: 'docs/production-readiness.md',
    summary: t(
      'The bridge between "it works locally" and "it is safe enough to ship or demo seriously".',
      'Cầu nối giữa "chạy được ở local" và "đủ an toàn để ship hoặc demo nghiêm túc".',
      '连接“本地能跑”与“已经足够安全，可以认真发布或演示”之间的那座桥。',
    ),
    audience: t('Operators and release owners', 'Người vận hành và chủ release', '操作者与发布负责人'),
    tags: ['production', 'readiness', 'ship'],
    content: productionReadinessDoc,
  },
  {
    id: 'release-checklist',
    title: t('Release Checklist', 'Checklist phát hành', '发布检查清单'),
    eyebrow: t('Publish flow', 'Luồng publish', '发布流程'),
    path: 'docs/release-checklist.md',
    summary: t(
      'What to verify before tagging or publishing, including artifact validation and frontend packaging.',
      'Những gì cần kiểm tra trước khi gắn tag hoặc publish, bao gồm artifact validation và frontend packaging.',
      '在打 tag 或正式发布前需要验证的事项，包括 artifact 校验和前端打包。',
    ),
    audience: t('Release owners', 'Người phụ trách release', '发布负责人'),
    tags: ['release', 'checklist', 'publish'],
    content: releaseChecklistDoc,
  },
  {
    id: 'demo-script',
    title: t('Demo Script', 'Kịch bản demo', '演示脚本'),
    eyebrow: t('Show the product well', 'Demo sản phẩm cho đẹp', '把产品讲清楚'),
    path: 'docs/demo-script.md',
    summary: t(
      'A practical sequence for live demos that keeps the story grounded and legible to non-experts.',
      'Một chuỗi thao tác thực tế cho live demo, giúp câu chuyện vẫn grounded và dễ hiểu với người không chuyên.',
      '一套适合现场演示的实际顺序，让叙事既 grounded，又能让非专家看懂。',
    ),
    audience: t('Demo presenters and OSS launch prep', 'Người demo và người chuẩn bị OSS launch', '演示者与 OSS 发布准备者'),
    tags: ['demo', 'presentation', 'script'],
    content: demoScriptDoc,
  },
  {
    id: 'roadmap',
    title: t('Roadmap', 'Lộ trình', '路线图'),
    eyebrow: t('Release track', 'Nhánh phát triển', '发布路线'),
    path: 'ROADMAP.md',
    summary: t(
      'The staged release path from MVP toward a stable 1.0 codebase memory product.',
      'Lộ trình phát hành theo giai đoạn từ MVP tới một sản phẩm codebase memory ổn định ở 1.0.',
      '从 MVP 逐步走向稳定 1.0 代码库记忆产品的阶段性发布路线。',
    ),
    audience: t('Anyone planning future work', 'Bất kỳ ai đang lên kế hoạch tương lai', '所有正在规划未来工作的人'),
    tags: ['roadmap', 'versions', 'future'],
    content: roadmapDoc,
  },
]
