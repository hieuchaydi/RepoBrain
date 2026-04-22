const repoDocs = import.meta.glob('../docs/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

const repoDoc = (filename: string): string => {
  const content = repoDocs[`../docs/${filename}`]

  if (!content) {
    throw new Error(`Missing repository doc: ${filename}`)
  }

  return content
}

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
  spotlightItems: Record<Locale, string[]>
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
const lines = (...entries: string[]) => entries.join('\n')

export const localeOptions = [
  { code: 'en' as const, short: 'EN', nativeLabel: 'English' },
  { code: 'vi' as const, short: 'VI', nativeLabel: 'Tiếng Việt' },
  { code: 'zh' as const, short: '中', nativeLabel: '中文' },
]

export const uiCopy: UiCopy = {
  sidebarIntro: t(
    'A documentation view for RepoBrain that keeps install, operations, and source reading in one place.',
    'Một giao diện tài liệu cho RepoBrain, gom cài đặt, vận hành và đọc nội dung vào cùng một chỗ.',
    'RepoBrain 的文档视图，把安装、运行和阅读内容收拢到同一个入口里。',
  ),
  searchPlaceholder: t(
    'Search documents, commands, or release notes',
    'Tìm tài liệu, lệnh hoặc ghi chú phát hành',
    '搜索文档、命令或发布说明',
  ),
  languageLabel: t('Language', 'Ngôn ngữ', '语言'),
  themeLabel: t('Appearance', 'Giao diện', '外观'),
  lightMode: t('Light', 'Sáng', '浅色'),
  darkMode: t('Dark', 'Tối', '深色'),
  searchScope: t('Search scope', 'Phạm vi tìm kiếm', '搜索范围'),
  docsUnit: t('documents', 'tài liệu', '文档'),
  commandsMatch: t('matching commands', 'lệnh khớp', '匹配的命令'),
  faqMatch: t('matching answers', 'mục hỏi đáp khớp', '匹配的问题'),
  currentFocus: t('Current focus', 'Tiêu điểm hiện tại', '当前焦点'),
  noDocumentSelected: t('No document selected', 'Chưa chọn tài liệu', '尚未选择文档'),
  pickDocumentHint: t(
    'Pick a document from the library below',
    'Chọn một tài liệu trong thư viện bên dưới',
    '请从下面的文档库里选择一个文档',
  ),
  heroEyebrow: t('RepoBrain documentation', 'Tài liệu RepoBrain', 'RepoBrain 文档'),
  heroLead: t(
    'RepoBrain is a local-first codebase memory engine for collecting grounded context before an assistant writes code. This page reorganizes the repository into a more legible operational manual.',
    'RepoBrain là một bộ máy ghi nhớ codebase ưu tiên cục bộ, dùng để thu thập ngữ cảnh có căn cứ trước khi trợ lý AI sửa mã. Trang này sắp xếp lại repository thành một bộ tài liệu vận hành dễ đọc hơn.',
    'RepoBrain 是一个本地优先的代码库记忆引擎，用来在助手改代码前先收集有依据的上下文。这个页面把仓库重新整理成更清晰的操作型文档。',
  ),
  heroPrimary: t('Explore documents', 'Xem tài liệu', '查看文档'),
  heroSecondary: t('Open quickstart', 'Mở phần bắt đầu nhanh', '打开快速开始'),
  spotlightEyebrow: t('What matters first', 'Điểm cần nắm trước', '优先要点'),
  spotlightItems: {
    en: [
      'Grounded retrieval over code, symbols, snippets, and edges.',
      'One toolset exposed through CLI, local web UI, report, and MCP transport.',
      'Release validation and cleanup flows already exist in the operator path.',
      'The product value is in safer context gathering before edits happen.',
    ],
    vi: [
      'Truy xuất có căn cứ trên mã nguồn, symbol, snippet và quan hệ phụ thuộc.',
      'Cùng một bộ công cụ được mở ra qua CLI, giao diện web cục bộ, báo cáo HTML và kết nối MCP.',
      'Luồng kiểm tra phát hành và dọn môi trường demo đã nằm sẵn trong sản phẩm.',
      'Giá trị cốt lõi nằm ở việc thu thập ngữ cảnh an toàn hơn trước khi chỉnh sửa mã.',
    ],
    zh: [
      '围绕代码、符号、片段和依赖边做有依据的检索。',
      '同一套能力同时通过 CLI、本地网页界面、HTML 报告和 MCP 连接暴露出来。',
      '发布校验与演示清理已经进入操作者的标准路径。',
      '核心价值在于先把上下文收集扎实，再让助手改代码。',
    ],
  },
  surfacesEyebrow: t('Product surfaces', 'Các bề mặt sử dụng', '使用形态'),
  surfacesTitle: t('One repository, several operator entry points', 'Một repository, nhiều điểm vào cho người dùng', '一个仓库，多个使用入口'),
  surfacesBody: t(
    'RepoBrain is no longer only a CLI. The repository now carries the command-line workflow, a local browser UI, a report view, release checks, and an MCP-facing transport.',
    'RepoBrain không còn chỉ là một CLI. Repository hiện bao gồm luồng dòng lệnh, giao diện trình duyệt cục bộ, báo cáo HTML, kiểm tra phát hành và kết nối cho MCP.',
    'RepoBrain 现在不只是一个 CLI。仓库同时包含命令行流程、本地网页界面、HTML 报告、发布检查以及面向 MCP 的连接方式。',
  ),
  quickstartEyebrow: t('Quickstart', 'Bắt đầu nhanh', '快速开始'),
  quickstartTitle: t(
    'The shortest path from a clean checkout to useful context',
    'Con đường ngắn nhất từ một bản clone mới tới ngữ cảnh sử dụng được',
    '从全新检出到拿到可用上下文的最短路径',
  ),
  quickstartBody: t(
    'Use this sequence when you want a dependable first session: install, initialize one repository, build the index, ask questions, then run the safety gates.',
    'Dùng chuỗi này khi bạn cần một buổi làm quen đáng tin cậy: cài đặt, khởi tạo repository, lập chỉ mục, đặt câu hỏi rồi mới chạy các cổng kiểm tra an toàn.',
    '当你需要一条可靠的首次使用路径时，就按这个顺序走：安装、初始化仓库、建立索引、提问，最后再跑安全门禁。',
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
      '`Tầm nhìn` để hiểu dự án này tồn tại nhằm giải quyết việc gì.',
      '`Hướng dẫn cài đặt` và `Hướng dẫn vận hành` cho ngày đầu tiên.',
      '`Tham chiếu CLI` và `Kiến trúc` để nắm hành vi và thiết kế.',
      '`Sẵn sàng vận hành` và `Danh mục kiểm tra phát hành` trước khi demo hoặc gắn thẻ.',
    ],
    zh: [
      '`愿景` 先回答这个项目为什么存在。',
      '`安装指南` 和 `运行指南` 用来完成第一天上手。',
      '`CLI 参考` 和 `架构` 用来理解行为与设计。',
      '`生产就绪` 与 `发布检查清单` 适合在演示或打标签前阅读。',
    ],
  },
  calloutDocs: t(
    'Use the library below to move between the main project documents without leaving the page.',
    'Dùng thư viện bên dưới để đi giữa các tài liệu chính của dự án mà không phải rời trang.',
    '用下面的文档库在主要项目文档之间切换，不必离开当前页面。',
  ),
  calloutDoctor: t(
    'Use `doctor`, `provider-smoke`, and `release-check` before you claim readiness.',
    'Chạy `doctor`, `provider-smoke` và `release-check` trước khi kết luận hệ thống đã sẵn sàng.',
    '在判断系统已经就绪之前，先运行 `doctor`、`provider-smoke` 和 `release-check`。',
  ),
  calloutCleanup: t(
    'Use `demo-clean` before a live session so the repository state looks deliberate and repeatable.',
    'Chạy `demo-clean` trước buổi trình diễn để trạng thái repository gọn gàng và lặp lại được.',
    '在正式演示前运行 `demo-clean`，让仓库状态保持整洁并且可重复。',
  ),
  commandsEyebrow: t('Command catalog', 'Danh mục lệnh', '命令目录'),
  commandsTitle: t(
    'Operational commands worth remembering',
    'Những lệnh vận hành đáng nhớ',
    '值得记住的操作命令',
  ),
  commandsBody: t(
    'These commands matter in day-one setup, repo investigation, release checks, and live demo preparation.',
    'Đây là các lệnh quan trọng cho ngày đầu, cho việc đọc repo, cho kiểm tra phát hành và cho chuẩn bị trình diễn.',
    '这些命令覆盖第一天上手、仓库排查、发布检查和现场演示准备。',
  ),
  repoMapEyebrow: t('Repo map', 'Bản đồ repo', '仓库地图'),
  repoMapTitle: t(
    'Where to look when you need source, UX, or release logic',
    'Nên nhìn vào đâu khi cần mã nguồn, trải nghiệm hoặc logic phát hành',
    '当你需要查看源码、体验或发布逻辑时该先看哪里',
  ),
  repoMapBody: t(
    'RepoBrain mixes Python, React, documentation, tests, and release automation. This map keeps the top-level structure understandable.',
    'RepoBrain kết hợp Python, React, tài liệu, kiểm thử và tự động hóa phát hành. Bản đồ này giúp phần cấu trúc cấp cao dễ theo dõi hơn.',
    'RepoBrain 同时包含 Python、React、文档、测试和发布自动化。这个地图让顶层结构更容易理解。',
  ),
  docsEyebrow: t('Document library', 'Thư viện tài liệu', '文档库'),
  docsTitle: t(
    'Read the core project documents in one curated place',
    'Đọc các tài liệu cốt lõi của dự án trong một chỗ đã được biên tập',
    '在一个整理过的界面里阅读项目核心文档',
  ),
  docsBody: t(
    'Select a document, review its summary, then open the reader below. The reader stays aligned with the selected language instead of mixing interface copy and source text.',
    'Chọn một tài liệu, xem tóm tắt rồi mở phần đọc bên dưới. Trình đọc sẽ bám theo ngôn ngữ đang chọn thay vì trộn lẫn nhãn giao diện và nội dung nguồn.',
    '先选文档、看摘要，再打开下面的阅读区。阅读内容会跟随当前语言，而不是把界面文案和源文档混在一起。',
  ),
  readerEyebrow: t('Reading room', 'Phòng đọc', '阅读区'),
  readerBody: t(
    'The reader follows the selected language. It uses localized reading content when available and falls back to the source markdown when it is not.',
    'Trình đọc sẽ đi theo ngôn ngữ đang chọn. Bản tiếng Anh hiển thị markdown nguồn; các ngôn ngữ khác hiển thị bản đọc đã biên tập từ cùng bộ tài liệu.',
    '阅读区会跟随当前语言。英文显示仓库原始 markdown；其他语言显示基于同一套文档整理出来的阅读版。',
  ),
  originalMarkdownNote: t(
    'Reader content follows the selected language. It prefers localized reading versions and falls back to the repository markdown when no localized entry exists.',
    'Nội dung bên phải luôn theo ngôn ngữ đang chọn. Bản tiếng Anh dùng markdown của repository; các bản còn lại dùng nội dung biên tập từ cùng bộ tài liệu.',
    '右侧内容始终跟随当前语言。英文使用仓库原始 markdown；其他语言使用基于同一套文档整理的阅读内容。',
  ),
  sourceFile: t('Source file', 'File nguồn', '源文件'),
  bestFor: t('Best for', 'Phù hợp nhất cho', '最适合'),
  switchDocument: t('Switch document', 'Đổi tài liệu', '切换文档'),
  noDocMatches: t(
    'No document matches the current filter. Clear the search box to reopen the full library.',
    'Không có tài liệu nào khớp với bộ lọc hiện tại. Hãy xóa ô tìm kiếm để mở lại toàn bộ thư viện.',
    '当前筛选没有匹配的文档。清空搜索框即可重新看到完整文档库。',
  ),
  releaseEyebrow: t('Release state', 'Trạng thái phát hành', '发布状态'),
  releaseTitle: t(
    'What is verified locally, and what still needs real-world validation',
    'Những gì đã kiểm chứng ở máy cục bộ và những gì vẫn cần xác minh ở môi trường thật',
    '哪些事项已经在本地验证完成，哪些仍需要真实环境确认',
  ),
  releaseBody: t(
    'Local packaging and documentation have moved forward. The remaining uncertainty sits in remote workflow execution and access to real providers.',
    'Đóng gói cục bộ và tài liệu đã tiến thêm một bước. Phần chưa chắc chắn còn lại nằm ở workflow từ xa và quyền truy cập provider thật.',
    '本地打包和文档已经向前推进。剩下的不确定性主要在远程工作流执行和真实 provider 访问上。',
  ),
  releaseRemote: t(
    'Remote publish validation still depends on GitHub workflow access and real credentials. UI work alone cannot close that gap.',
    'Việc xác minh phát hành từ xa vẫn phụ thuộc vào quyền GitHub Actions và thông tin xác thực thật. Chỉ làm UI thì chưa thể coi phần này là xong.',
    '远程发布验证仍然依赖 GitHub Actions 权限和真实凭据。仅靠 UI 调整并不能把这一项算作完成。',
  ),
  releaseHuman: t(
    'The current docs surface is mainly about making the local product easier to understand, review, and present to other engineers.',
    'Bề mặt tài liệu hiện tại chủ yếu nhằm giúp sản phẩm cục bộ dễ hiểu hơn, dễ rà soát hơn và dễ trình bày hơn với kỹ sư khác.',
    '当前这层文档界面的目标，主要是让本地产品更容易被工程师理解、评审和讲清楚。',
  ),
  releaseNext: t(
    'Once remote auth is available, the next practical step is to trigger the release workflow with publish disabled and inspect the generated artifacts.',
    'Khi có quyền truy cập từ xa, bước thực tế tiếp theo là kích hoạt workflow phát hành ở chế độ không công bố và kiểm tra bộ tạo phẩm sinh ra.',
    '一旦远程认证可用，下一步就是用关闭发布的方式触发发布工作流，并检查生成的产物。',
  ),
  faqEyebrow: t('FAQ', 'Hỏi đáp', '常见问题'),
  faqTitle: t('Questions people ask first', 'Những câu hỏi thường được hỏi đầu tiên', '最常先被问到的问题'),
  faqBody: t(
    'These answers are tuned for initial walkthroughs, project reviews, and demo preparation.',
    'Các câu trả lời này được viết cho buổi làm quen đầu tiên, cho lúc rà soát dự án và cho chuẩn bị trình diễn.',
    '这些回答主要面向首次讲解、项目评审和演示准备。',
  ),
  footerBody: t(
    'Built as a readable documentation surface for the RepoBrain repository. Use it to orient yourself quickly, then drop into the source material when needed.',
    'Đây là một lớp tài liệu dễ đọc cho repository RepoBrain. Hãy dùng nó để định hướng nhanh, rồi đi xuống tài liệu nguồn khi cần chi tiết.',
    '这是一层更易读的 RepoBrain 文档界面。先用它快速建立方向感，需要细节时再进入源文档。',
  ),
  footerTop: t('Back to top', 'Lên đầu trang', '回到顶部'),
  footerReader: t('Open reader', 'Mở trình đọc', '打开阅读区'),
  footerRelease: t('Check release state', 'Xem trạng thái phát hành', '查看发布状态'),
  statusPass: t('pass', 'pass', '通过'),
  statusPending: t('pending', 'chờ xác minh', '待验证'),
  statusInfo: t('info', 'thông tin', '信息'),
}

export const navigationSections = [
  { id: 'overview', label: t('Overview', 'Tổng', '概览') },
  { id: 'surfaces', label: t('Surfaces', 'Mặt', '形态') },
  { id: 'quickstart', label: t('Start', 'Nhanh', '开始') },
  { id: 'commands', label: t('Commands', 'Lệnh', '命令') },
  { id: 'repo-map', label: t('Map', 'Map', '地图') },
  { id: 'docs-library', label: t('Docs', 'Docs', '文档') },
  { id: 'reader', label: t('Reader', 'Đọc', '阅读') },
  { id: 'release-state', label: t('Release', 'Phát', '发布') },
  { id: 'faq', label: t('FAQ', 'FAQ', 'FAQ') },
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
    title: t('Install the development stack', 'Cài môi trường phát triển', '安装开发环境'),
    body: t(
      'Create a virtual environment, install the editable package, and keep the first run fully local.',
      'Tạo virtual environment, cài gói editable và giữ toàn bộ lần chạy đầu ở máy cục bộ.',
      '先创建虚拟环境，安装 editable 包，并把第一次运行完整留在本地。',
    ),
    command: 'python -m pip install --cache-dir .pip-cache -e .',
  },
  {
    title: t('Initialize one repository', 'Khởi tạo repository', '初始化仓库'),
    body: t(
      'Run `repobrain init --repo <path>` once so later commands can reuse the active project.',
      'Chạy `repobrain init --repo <path>` một lần để các lệnh sau dùng lại đúng repository đang làm việc.',
      '先运行一次 `repobrain init --repo <path>`，让后续命令复用当前仓库上下文。',
    ),
    command: 'repobrain first-look --repo "C:\\path\\to\\your-project" --no-report --format text',
  },
  {
    title: t('Scan, then index', 'Quét trước, lập chỉ mục sau', '先扫描，再建索引'),
    body: t(
      'Use `review` for a quick risk-oriented read, then build the local index for grounded retrieval.',
      'Dùng `review` để đọc nhanh theo hướng rủi ro, rồi lập chỉ mục cục bộ cho truy xuất có căn cứ.',
      '先用 `review` 做一次面向风险的快速阅读，再建立本地索引，支撑有依据的检索。',
    ),
    command: 'repobrain review --format text\nrepobrain index --format text',
  },
  {
    title: t('Ask grounded questions', 'Đặt câu hỏi có căn cứ', '提出有依据的问题'),
    body: t(
      'Use `query`, `trace`, and `targets` when you need evidence for where logic lives and what is safest to touch next.',
      'Dùng `query`, `trace` và `targets` khi bạn cần biết logic nằm ở đâu và bước chỉnh sửa tiếp theo nên đụng vào tệp nào.',
      '当你需要知道逻辑位于哪里，以及下一步该碰哪个文件最稳时，就用 `query`、`trace` 和 `targets`。',
    ),
    command: 'repobrain query "Where is payment retry logic implemented?" --format text',
  },
  {
    title: t('Close with release gates', 'Khép lại bằng cổng kiểm tra', '最后跑发布门禁'),
    body: t(
      'Use `ship`, `release-check`, and `demo-clean` before you move from development into demo or release work.',
      'Chạy `ship`, `release-check` và `demo-clean` trước khi chuyển từ phát triển sang trình diễn hoặc phát hành.',
      '当你准备从开发阶段进入演示或发布阶段时，用 `ship`、`release-check` 和 `demo-clean` 收尾。',
    ),
    command: 'repobrain ship --format text\nrepobrain release-check --require-dist --format text\nrepobrain demo-clean --format text',
  },
]

export const commandCatalog: CommandEntry[] = [
  {
    category: t('Demo', 'Demo', '演示'),
    command: 'repobrain first-look --repo "<path>" --format text',
    summary: t(
      'Run the no-VPS/no-key first session: init, index, starter questions, and local report.',
      'Chạy phiên đầu tiên không cần VPS/API key: init, index, câu hỏi mẫu, và report local.',
      '运行不需要 VPS 或 API key 的首次会话：初始化、索引、示例问题和本地报告。',
    ),
    result: t(
      'Prints a shareable local demo summary and writes `.repobrain/report.html`.',
      'In ra tóm tắt demo local để chia sẻ và ghi `.repobrain/report.html`.',
      '输出可分享的本地演示摘要，并写入 `.repobrain/report.html`。',
    ),
  },
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
    state: 'pass',
    detail: t(
      'The docs frontend now pulls operational docs plus planning and progress notes from the repository markdown set.',
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
  {
    label: t('Current sprint ETA', 'ETA sprint hiện tại', '当前 sprint ETA'),
    state: 'info',
    detail: t(
      'Next local hardening checkpoint is estimated for April 22, 2026. Remote release validation still depends on GitHub workflow access and live provider credentials.',
      'Mốc hardening local tiếp theo dự kiến vào ngày 22 tháng 4 năm 2026. Phần xác minh phát hành từ xa vẫn phụ thuộc vào quyền truy cập GitHub workflow và thông tin provider thật.',
      '下一个本地加固检查点预计在 2026 年 4 月 22 日。远程发布验证仍然依赖 GitHub workflow 访问权限和真实 provider 凭据。',
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

export const localizedDocContent: Record<string, Partial<Record<Locale, string>>> = {
  vision: {
    vi: lines(
      '# Tầm nhìn',
      '',
      'RepoBrain được xây để cải thiện bước thu thập ngữ cảnh trước khi trợ lý AI đọc, trả lời hoặc sửa mã.',
      '',
      '## Trọng tâm tài liệu',
      '- Xác định vấn đề gốc: trợ lý thường sai khi không định vị đúng tệp, đúng luồng và đúng bằng chứng.',
      '- Mô tả người dùng mục tiêu: kỹ sư, người rà soát và cộng tác viên mới cần hiểu repository nhanh nhưng vẫn có căn cứ.',
      '- Nêu luận điểm sản phẩm: ưu tiên truy xuất có dẫn chứng, giảm tự tin khi bằng chứng yếu và giữ dữ liệu ở máy cục bộ.',
      '- Làm rõ những việc RepoBrain chưa cố giải quyết trong phiên bản đầu.',
      '',
      '## Khi nên đọc',
      'Đọc tài liệu này trước khi xem kiến trúc hoặc đánh giá chất lượng. Nó giúp thống nhất kỳ vọng về việc RepoBrain phải làm tốt điều gì.',
    ),
    zh: lines(
      '# 愿景',
      '',
      'RepoBrain 的目标，是先把助手改代码之前的上下文收集阶段做好。',
      '',
      '## 文档重点',
      '- 说明根本问题：当助手无法找准文件、调用链和证据时，回答与修改都会失真。',
      '- 定义目标读者：需要快速理解仓库、同时又不能脱离证据的工程师、评审者和新贡献者。',
      '- 给出产品论点：优先做有依据的检索，在证据不足时主动降低自信，并坚持本地优先。',
      '- 说明一代版本不打算解决的范围，避免把产品边界说得过宽。',
      '',
      '## 适合什么时候读',
      '在看架构、评估质量或准备演示之前先读这一篇，可以先把项目目标讲清楚。',
    ),
  },
  install: {
    en: lines(
      '# Installation Guide',
      '',
      '## Windows PowerShell',
      '',
      '```powershell',
      'cd C:\\Users\\ASUS\\Desktop\\new-AI',
      'python -m venv venv',
      'Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass',
      '.\\venv\\Scripts\\Activate.ps1',
      'python -m pip install --upgrade pip',
      'python -m pip install --cache-dir .pip-cache -e .',
      '```',
      '',
      '## Linux Or macOS',
      '',
      '```bash',
      'cd /path/to/new-AI',
      'python -m venv .venv',
      '. .venv/bin/activate',
      'python -m pip install --upgrade pip',
      'python -m pip install --cache-dir .pip-cache -e .',
      '```',
      '',
      '## Verify',
      '',
      '```powershell',
      'repobrain doctor --format text',
      'repobrain index --format text',
      'repobrain query "Where is RepoBrain CLI implemented?" --format text',
      'repobrain report --format text',
      'repobrain chat',
      '```',
    ),
    vi: lines(
      '# Hướng dẫn cài đặt',
      '',
      '## Windows PowerShell',
      '',
      '```powershell',
      'cd C:\\Users\\ASUS\\Desktop\\new-AI',
      'python -m venv venv',
      'Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass',
      '.\\venv\\Scripts\\Activate.ps1',
      'python -m pip install --upgrade pip',
      'python -m pip install --cache-dir .pip-cache -e .',
      '```',
      '',
      '## Linux Hoặc macOS',
      '',
      '```bash',
      'cd /path/to/new-AI',
      'python -m venv .venv',
      '. .venv/bin/activate',
      'python -m pip install --upgrade pip',
      'python -m pip install --cache-dir .pip-cache -e .',
      '```',
      '',
      '## Kiểm Tra',
      '',
      '```powershell',
      'repobrain doctor --format text',
      'repobrain index --format text',
      'repobrain query "Where is RepoBrain CLI implemented?" --format text',
      'repobrain report --format text',
      'repobrain chat',
      '```',
    ),
    zh: lines(
      '# 安装指南',
      '',
      '## Windows PowerShell',
      '',
      '```powershell',
      'cd C:\\Users\\ASUS\\Desktop\\new-AI',
      'python -m venv venv',
      'Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass',
      '.\\venv\\Scripts\\Activate.ps1',
      'python -m pip install --upgrade pip',
      'python -m pip install --cache-dir .pip-cache -e .',
      '```',
      '',
      '## Linux 或 macOS',
      '',
      '```bash',
      'cd /path/to/new-AI',
      'python -m venv .venv',
      '. .venv/bin/activate',
      'python -m pip install --upgrade pip',
      'python -m pip install --cache-dir .pip-cache -e .',
      '```',
      '',
      '## 验证',
      '',
      '```powershell',
      'repobrain doctor --format text',
      'repobrain index --format text',
      'repobrain query "Where is RepoBrain CLI implemented?" --format text',
      'repobrain report --format text',
      'repobrain chat',
      '```',
    ),
  },
  run: {
    vi: lines(
      '# Hướng dẫn vận hành',
      '',
      'Tài liệu này mô tả cách khởi tạo một repository, lập chỉ mục và dùng các chế độ chạy chính của RepoBrain.',
      '',
      '## Luồng cơ bản',
      '- Khởi tạo repository bằng init.',
      '- Lập chỉ mục bằng index.',
      '- Kiểm tra tình trạng cấu hình bằng doctor và provider-smoke.',
      '- Đặt câu hỏi bằng query, trace, impact hoặc targets.',
      '',
      '## Các chế độ sử dụng',
      '- Chat cục bộ cho vòng hỏi đáp nhanh.',
      '- Báo cáo HTML khi cần chia sẻ cho người không thích terminal.',
      '- Giao diện trình duyệt khi cần biểu mẫu và bảng điều khiển.',
      '- Kết nối kiểu MCP khi muốn cấp công cụ cho trợ lý lập trình.',
      '',
      '## Khi nên đọc',
      'Đây là tài liệu nên mở ngay sau phần cài đặt, vì nó nối từ môi trường đã sẵn sàng sang cách dùng hằng ngày.',
    ),
    zh: lines(
      '# 运行指南',
      '',
      '这一篇说明如何初始化仓库、建立索引，并使用 RepoBrain 的几个主要运行模式。',
      '',
      '## 基本流程',
      '- 先用 init 记录目标仓库。',
      '- 再用 index 建立本地索引。',
      '- 用 doctor 和 provider-smoke 检查配置状态。',
      '- 需要查问题时，使用 query、trace、impact 或 targets。',
      '',
      '## 主要使用方式',
      '- 本地聊天循环适合快速问答。',
      '- HTML 报告适合给不常用终端的人查看。',
      '- 浏览器界面适合导入、查看和诊断。',
      '- MCP 风格连接适合给编程助手提供工具能力。',
      '',
      '## 适合什么时候读',
      '安装完成后就应该继续读这一篇，因为它把环境准备阶段连接到日常使用阶段。',
    ),
  },
  cli: {
    vi: lines(
      '# Tham chiếu CLI',
      '',
      'Đây là tài liệu tra cứu tập trung cho toàn bộ bề mặt lệnh của RepoBrain.',
      '',
      '## Nhóm lệnh chính',
      '- Khởi tạo và lập chỉ mục: init, index.',
      '- Khảo sát repository: review, query, trace, impact, targets.',
      '- Kiểm tra vận hành: doctor, provider-smoke, ship.',
      '- Giao diện cho người dùng: chat, report, serve-web, serve-mcp.',
      '- Phát hành và dọn môi trường: release-check, demo-clean.',
      '',
      '## Cách dùng hiệu quả',
      'Không cần đọc toàn bộ theo thứ tự. Hãy dùng tài liệu này như bảng tham chiếu khi bạn đã biết mình cần lệnh nào và muốn xem hành vi cụ thể của nó.',
    ),
    zh: lines(
      '# CLI 参考',
      '',
      '这一篇集中列出 RepoBrain 的命令行能力，适合作为查阅手册使用。',
      '',
      '## 主要命令分组',
      '- 初始化与建索引：init、index。',
      '- 仓库排查：review、query、trace、impact、targets。',
      '- 运维检查：doctor、provider-smoke、ship。',
      '- 面向人的界面：chat、report、serve-web、serve-mcp。',
      '- 发布与清理：release-check、demo-clean。',
      '',
      '## 推荐用法',
      '这一篇不必从头读到尾。更适合在你已经知道要找哪条命令时，回头查看细节和返回结果。',
    ),
  },
  architecture: {
    vi: lines(
      '# Kiến trúc',
      '',
      'Tài liệu kiến trúc giải thích RepoBrain xử lý dữ liệu như thế nào từ lúc thu nạp mã nguồn tới lúc trả về bằng chứng truy xuất.',
      '',
      '## Nội dung chính',
      '- Cách hệ thống thu nạp mã nguồn và trích xuất đơn vị phân tích.',
      '- Cấu trúc lưu trữ cho metadata, vector và trạng thái làm việc.',
      '- Luồng truy xuất từ câu hỏi tới tệp, snippet và mối quan hệ phụ thuộc.',
      '- Mô hình tin cậy và các điểm mở rộng cho parser, provider và lớp tích hợp.',
      '',
      '## Khi nên đọc',
      'Mở tài liệu này khi bạn cần hiểu vì sao RepoBrain trả về một kết quả nhất định hoặc khi muốn chỉnh sửa lõi hệ thống.',
    ),
    zh: lines(
      '# 架构',
      '',
      '架构文档解释 RepoBrain 如何从源码摄取一路走到返回检索证据。',
      '',
      '## 主要内容',
      '- 系统如何摄取代码并提取可分析单元。',
      '- 元数据、向量与运行状态的存储结构。',
      '- 从问题到文件、代码片段和依赖边的检索链路。',
      '- 可信模型，以及 parser、provider 和集成层的扩展点。',
      '',
      '## 适合什么时候读',
      '当你需要理解某个结果为什么会被召回，或者准备改动核心逻辑时，就应该读这一篇。',
    ),
  },
  mcp: {
    vi: lines(
      '# MCP',
      '',
      'Tài liệu này mô tả cách RepoBrain mở các khả năng của mình qua giao thức kiểu stdio để công cụ bên ngoài gọi tới.',
      '',
      '## Nội dung chính',
      '- Danh sách công cụ được công bố, như lập chỉ mục, truy vấn và phân tích tác động.',
      '- Kiểu đầu vào đầu ra mong đợi của từng công cụ.',
      '- Cách kết nối qua kênh stdio để trợ lý lập trình hoặc lớp tự động hóa sử dụng.',
      '',
      '## Khi nên đọc',
      'Đọc tài liệu này nếu bạn đang tích hợp RepoBrain vào một agent, một plugin hoặc một lớp orchestration bên ngoài.',
    ),
    zh: lines(
      '# MCP',
      '',
      '这一篇说明 RepoBrain 如何通过 stdio 风格的协议把能力暴露给外部工具。',
      '',
      '## 主要内容',
      '- 对外提供的工具列表，例如建索引、检索、影响分析和编辑目标建议。',
      '- 每个工具的输入输出约定。',
      '- 如何通过 stdio 通道接入，让编程助手或自动化层调用这些能力。',
      '',
      '## 适合什么时候读',
      '如果你正在把 RepoBrain 接到 agent、插件或其他编排层，这一篇就是优先级很高的材料。',
    ),
  },
  ux: {
    vi: lines(
      '# Trải nghiệm người dùng',
      '',
      'Tài liệu này không nói về giao diện đẹp hay xấu, mà nói về cách RepoBrain nên cư xử với người dùng ở từng bề mặt.',
      '',
      '## Nội dung chính',
      '- Tiêu chuẩn trải nghiệm cho terminal, chat và báo cáo HTML.',
      '- Cách thiết kế luồng một chạm để người mới không phải nhớ quá nhiều lệnh.',
      '- Yêu cầu của giao diện trình duyệt khi nhập repository, xem kết quả và chuẩn bị trình diễn.',
      '- Lộ trình làm quen được khuyến nghị cho người dùng mới.',
      '',
      '## Khi nên đọc',
      'Nên đọc tài liệu này khi bạn sửa giao diện, câu chữ, trạng thái hiển thị hoặc hành vi hướng dẫn người dùng.',
    ),
    zh: lines(
      '# 用户体验',
      '',
      '这篇文档讨论的不是视觉好不好看，而是 RepoBrain 在不同界面上该如何对待用户。',
      '',
      '## 主要内容',
      '- 终端、聊天与 HTML 报告的体验标准。',
      '- 一键式流程如何降低新用户的记忆负担。',
      '- 浏览器界面在导入仓库、查看结果和准备演示时应该满足什么要求。',
      '- 面向新用户的推荐上手路径。',
      '',
      '## 适合什么时候读',
      '当你修改界面、文案、状态反馈或引导流程时，应该先看这一篇。',
    ),
  },
  evaluation: {
    vi: lines(
      '# Đánh giá',
      '',
      'Tài liệu này mô tả cách RepoBrain đo chất lượng truy xuất thay vì chỉ dựa vào cảm giác sử dụng.',
      '',
      '## Nội dung chính',
      '- Chọn repository mẫu để đo theo cùng một mặt bằng.',
      '- Các chỉ số quan trọng cho độ đúng, độ hữu ích và độ an toàn của kết quả.',
      '- Bộ câu hỏi chấp nhận dùng để kiểm tra hồi quy.',
      '- Các dạng lỗi cần tiếp tục theo dõi theo thời gian.',
      '',
      '## Khi nên đọc',
      'Đọc khi bạn thay đổi thuật toán truy xuất, parser, provider hoặc tiêu chí xếp hạng kết quả.',
    ),
    zh: lines(
      '# 评估',
      '',
      '这一篇说明 RepoBrain 如何衡量检索质量，而不是只靠主观体验下结论。',
      '',
      '## 主要内容',
      '- 用哪些样本仓库来做对比。',
      '- 结果准确性、可用性和安全性分别看哪些指标。',
      '- 哪些验收问题适合作为回归测试。',
      '- 长期需要追踪的失败模式。',
      '',
      '## 适合什么时候读',
      '当你调整检索算法、parser、provider 或结果排序逻辑时，就应该先看这篇。',
    ),
  },
  'production-readiness': {
    vi: lines(
      '# Sẵn sàng vận hành',
      '',
      'Tài liệu này trả lời một câu hỏi thực tế: RepoBrain đã ở mức nào giữa chạy được cục bộ và đủ an toàn để trình diễn hoặc phát hành nghiêm túc.',
      '',
      '## Nội dung chính',
      '- Tình trạng sẵn sàng hiện tại theo từng nhóm năng lực.',
      '- Các cổng kiểm tra cho phát hành mã nguồn mở.',
      '- Các tiêu chí an toàn khi chạy thực tế và các cột mốc nên hoàn thành tiếp theo.',
      '- Kết luận phát hành ở cuối tài liệu.',
      '',
      '## Khi nên đọc',
      'Mở tài liệu này khi bạn cần quyết định có nên demo, gắn thẻ hay công bố một trạng thái build nào đó hay chưa.',
    ),
    zh: lines(
      '# 生产就绪',
      '',
      '这篇文档回答一个现实问题：RepoBrain 现在处在本地能跑和足够安全可以认真演示或发布之间的哪个位置。',
      '',
      '## 主要内容',
      '- 当前就绪状态按能力分组展开说明。',
      '- 面向开源发布的检查门禁。',
      '- 真实运行时的安全要求，以及下一批应完成的里程碑。',
      '- 文末给出发布判断。',
      '',
      '## 适合什么时候读',
      '当你要决定某个构建是否已经可以演示、打标签或公开发布时，这一篇最有用。',
    ),
  },
  'release-checklist': {
    vi: lines(
      '# Danh mục kiểm tra phát hành',
      '',
      'Đây là danh sách các việc cần xác minh trước khi gắn thẻ hoặc công bố một bản phát hành.',
      '',
      '## Nội dung chính',
      '- Các bước cần hoàn thành trước khi phát hành.',
      '- Cách chạy workflow thủ công trên GitHub khi cần xác minh từ xa.',
      '- Quy trình gắn thẻ và cách quay lui nếu có sự cố.',
      '',
      '## Cách dùng',
      'Dùng tài liệu này như danh sách kiểm tra thao tác cuối cùng. Nó không thay thế tài liệu vận hành, nhưng giúp tránh sót bước ngay trước thời điểm công bố.',
    ),
    zh: lines(
      '# 发布检查清单',
      '',
      '这一篇是发布前的核对表，用来确认打标签或正式发布之前没有漏掉关键步骤。',
      '',
      '## 主要内容',
      '- 发布前必须完成的检查项。',
      '- 需要远程验证时，如何手动触发 GitHub 工作流。',
      '- 打标签流程，以及出问题时如何回退。',
      '',
      '## 使用方式',
      '把它当作最后一道核对表使用。它不替代运维文档，但能减少临门一脚时的遗漏。',
    ),
  },
  'demo-script': {
    vi: lines(
      '# Kịch bản trình diễn',
      '',
      'Tài liệu này giúp buổi trình diễn RepoBrain đi theo một trình tự rõ ràng, không lan man và không rơi vào chi tiết khó theo dõi.',
      '',
      '## Nội dung chính',
      '- Mục tiêu của buổi trình diễn.',
      '- Thứ tự thao tác nên đi qua khi trình bày sản phẩm.',
      '- Các ý cần nhấn mạnh để người xem hiểu đúng giá trị của RepoBrain.',
      '- Lưu ý về hình ảnh và khả năng tiếp cận trong lúc demo.',
      '',
      '## Khi nên đọc',
      'Mở tài liệu này trước buổi demo nội bộ, buổi giới thiệu công khai hoặc khi cần kể câu chuyện sản phẩm một cách có kỷ luật.',
    ),
    zh: lines(
      '# 演示脚本',
      '',
      '这一篇帮助演示 RepoBrain 时保持节奏清晰，避免话题发散，也避免陷入难以跟上的细节。',
      '',
      '## 主要内容',
      '- 演示目标是什么。',
      '- 展示产品时建议按什么顺序操作。',
      '- 哪些要点必须讲清楚，观众才能理解 RepoBrain 的价值。',
      '- 演示画面与可访问性方面的注意事项。',
      '',
      '## 适合什么时候读',
      '在内部演示、公开介绍或准备正式讲述产品故事前，先看这一篇会更稳。',
    ),
  },
  roadmap: {
    vi: lines(
      '# Lộ trình',
      '',
      'Tài liệu này mô tả các giai đoạn phát triển của RepoBrain từ nền tảng ban đầu tới mục tiêu 1.0 đáng tin cậy.',
      '',
      '## Nội dung chính',
      '- Các chặng phát triển theo từng nhánh phiên bản.',
      '- Những năng lực đã được ưu tiên ở từng giai đoạn, từ nền tảng, chất lượng truy xuất tới tích hợp hệ sinh thái.',
      '- Các hạng mục bị hoãn sang giai đoạn sau 1.0.',
      '',
      '## Khi nên đọc',
      'Đọc khi bạn cần hiểu thứ tự ưu tiên của dự án, chuẩn bị đề xuất tính năng mới hoặc đánh giá xem một thay đổi có đúng hướng phát triển hay không.',
    ),
    zh: lines(
      '# 路线图',
      '',
      '这篇文档描述 RepoBrain 从早期基础阶段走向可信 1.0 的阶段性路线。',
      '',
      '## 主要内容',
      '- 各个版本阶段分别关注什么。',
      '- 从基础能力、检索质量到生态集成的优先级如何推进。',
      '- 哪些事项被明确延后到 1.0 之后。',
      '',
      '## 适合什么时候读',
      '当你需要理解项目优先级、准备新功能提案或判断某个改动是否符合整体方向时，应该先读这一篇。',
    ),
  },
}

export const docsLibrary: DocEntry[] = [
  {
    id: 'vision',
    title: t('Vision', 'Tầm nhìn', '愿景'),
    eyebrow: t('Product direction', 'Định hướng sản phẩm', '产品方向'),
    path: 'docs-for-repobrain/docs/vision.md',
    summary: t(
      'Why RepoBrain exists, what behavior it is trying to change in coding assistants, and what success looks like.',
      'Vì sao RepoBrain tồn tại, nó đang cố thay đổi hành vi nào của coding assistant, và thế nào là thành công.',
      '为什么 RepoBrain 存在、它想改变编码助手的哪些行为，以及成功应该是什么样子。',
    ),
    audience: t('Founders, reviewers, new contributors', 'Founder, reviewer, contributor mới', '创始人、评审者、新贡献者'),
    tags: ['product', 'direction', 'why'],
    content: repoDoc('vision.md'),
  },
  {
    id: 'install',
    title: t('Install Guide', 'Hướng dẫn cài đặt', '安装指南'),
    eyebrow: t('Get started', 'Bắt đầu', '开始使用'),
    path: 'docs-for-repobrain/docs/install.md',
    summary: t(
      'Environment setup, package installation, and the minimum path to first use.',
      'Thiết lập môi trường, cài package và con đường ngắn nhất để dùng lần đầu.',
      '环境配置、包安装，以及第一次用起来的最短路径。',
    ),
    audience: t('Anyone onboarding to the repo', 'Bất kỳ ai đang onboard vào repo', '所有正在上手这个仓库的人'),
    tags: ['install', 'onboarding', 'setup'],
    content: repoDoc('install.md'),
  },
  {
    id: 'run',
    title: t('Run Guide', 'Hướng dẫn chạy', '运行指南'),
    eyebrow: t('Daily workflow', 'Luồng làm việc hằng ngày', '日常工作流'),
    path: 'docs-for-repobrain/docs/run.md',
    summary: t(
      'How to run RepoBrain from CLI, browser UI, report mode, MCP mode, and demo prep flows.',
      'Cách chạy RepoBrain từ CLI, browser UI, report mode, MCP mode và các luồng chuẩn bị demo.',
      '如何通过 CLI、浏览器界面、report 模式、MCP 模式以及演示准备流程来运行 RepoBrain。',
    ),
    audience: t('Users and operators', 'Người dùng và người vận hành', '用户与操作者'),
    tags: ['run', 'workflow', 'demo'],
    content: repoDoc('run.md'),
  },
  {
    id: 'docker',
    title: t('Docker Setup', 'Docker setup', 'Docker setup'),
    eyebrow: t('Container workflow', 'Container workflow', 'Container workflow'),
    path: 'docs-for-repobrain/docs/docker.md',
    summary: t(
      'How to run RepoBrain as a Docker web UI or interactive CLI, including provider setup from the browser.',
      'Cach chay RepoBrain bang Docker web UI hoac CLI, kem cau hinh provider tu browser.',
      'How to run RepoBrain with Docker web UI or CLI, including provider setup.',
    ),
    audience: t('Operators and Docker users', 'Nguoi dung Docker', 'Docker users'),
    tags: ['docker', 'setup', 'providers'],
    content: repoDoc('docker.md'),
  },
  {
    id: 'cli',
    title: t('CLI Reference', 'Tham chiếu CLI', 'CLI 参考'),
    eyebrow: t('Command surface', 'Bề mặt lệnh', '命令表面'),
    path: 'docs-for-repobrain/docs/cli.md',
    summary: t(
      'Descriptions of every primary command, what it returns, and how the tools fit together.',
      'Mô tả từng lệnh chính, những gì nó trả về và cách các công cụ khớp với nhau.',
      '每个核心命令的说明、返回内容，以及这些工具之间如何配合。',
    ),
    audience: t('Power users and maintainers', 'Power user và maintainer', '高级用户与维护者'),
    tags: ['cli', 'commands', 'reference'],
    content: repoDoc('cli.md'),
  },
  {
    id: 'architecture',
    title: t('Architecture', 'Kiến trúc', '架构'),
    eyebrow: t('System design', 'Thiết kế hệ thống', '系统设计'),
    path: 'docs-for-repobrain/docs/architecture.md',
    summary: t(
      'The retrieval engine, indexing model, grounding flow, and major design tradeoffs behind RepoBrain.',
      'Retrieval engine, mô hình indexing, grounding flow và các tradeoff thiết kế chính của RepoBrain.',
      'RepoBrain 背后的检索引擎、索引模型、grounding 流程以及主要设计取舍。',
    ),
    audience: t('Engineers reading the core design', 'Kỹ sư muốn đọc thiết kế lõi', '阅读核心设计的工程师'),
    tags: ['architecture', 'engine', 'design'],
    content: repoDoc('architecture.md'),
  },
  {
    id: 'mcp',
    title: t('MCP', 'MCP', 'MCP'),
    eyebrow: t('Agent integration', 'Tích hợp agent', 'Agent 集成'),
    path: 'docs-for-repobrain/docs/mcp.md',
    summary: t(
      'How RepoBrain exposes tools over a stdio transport for coding assistants and automation layers.',
      'Cách RepoBrain mở công cụ qua stdio transport cho coding assistant và các lớp automation.',
      'RepoBrain 如何通过 stdio transport 暴露工具，供编码助手和自动化层使用。',
    ),
    audience: t('Tooling engineers and agent builders', 'Kỹ sư tooling và người xây agent', '工具工程师与 agent 构建者'),
    tags: ['mcp', 'agent', 'integration'],
    content: repoDoc('mcp.md'),
  },
  {
    id: 'ux',
    title: t('User Experience', 'Trải nghiệm người dùng', '用户体验'),
    eyebrow: t('Interaction design', 'Thiết kế tương tác', '交互设计'),
    path: 'docs-for-repobrain/docs/ux.md',
    summary: t(
      'What the human-facing product should feel like across CLI, report, and browser surfaces.',
      'Trải nghiệm sản phẩm hướng con người nên như thế nào trên CLI, report và browser UI.',
      '面向人的产品体验在 CLI、report 和浏览器界面上应该呈现成什么样。',
    ),
    audience: t('Product and frontend contributors', 'Contributor về product và frontend', '产品与前端贡献者'),
    tags: ['ux', 'frontend', 'design'],
    content: repoDoc('ux.md'),
  },
  {
    id: 'evaluation',
    title: t('Evaluation', 'Đánh giá', '评估'),
    eyebrow: t('Quality signals', 'Tín hiệu chất lượng', '质量信号'),
    path: 'docs-for-repobrain/docs/evaluation.md',
    summary: t(
      'How retrieval quality is measured and what metrics matter for RepoBrain confidence.',
      'Cách đo chất lượng retrieval và metric nào quan trọng đối với confidence của RepoBrain.',
      '如何衡量检索质量，以及哪些指标会影响 RepoBrain 的置信度。',
    ),
    audience: t('Engineers tuning relevance and safety', 'Kỹ sư tinh chỉnh relevance và safety', '调优相关性与安全性的工程师'),
    tags: ['evaluation', 'benchmark', 'quality'],
    content: repoDoc('evaluation.md'),
  },
  {
    id: 'production-readiness',
    title: t('Production Readiness', 'Sẵn sàng production', '生产就绪'),
    eyebrow: t('Operator checklist', 'Checklist vận hành', '操作者清单'),
    path: 'docs-for-repobrain/docs/production-readiness.md',
    summary: t(
      'The bridge between "it works locally" and "it is safe enough to ship or demo seriously".',
      'Cầu nối giữa "chạy được ở local" và "đủ an toàn để ship hoặc demo nghiêm túc".',
      '连接“本地能跑”与“已经足够安全，可以认真发布或演示”之间的那座桥。',
    ),
    audience: t('Operators and release owners', 'Người vận hành và chủ release', '操作者与发布负责人'),
    tags: ['production', 'readiness', 'ship'],
    content: repoDoc('production-readiness.md'),
  },
  {
    id: 'release-checklist',
    title: t('Release Checklist', 'Checklist phát hành', '发布检查清单'),
    eyebrow: t('Publish flow', 'Luồng publish', '发布流程'),
    path: 'docs-for-repobrain/docs/release-checklist.md',
    summary: t(
      'What to verify before tagging or publishing, including artifact validation and frontend packaging.',
      'Những gì cần kiểm tra trước khi gắn tag hoặc publish, bao gồm artifact validation và frontend packaging.',
      '在打 tag 或正式发布前需要验证的事项，包括 artifact 校验和前端打包。',
    ),
    audience: t('Release owners', 'Người phụ trách release', '发布负责人'),
    tags: ['release', 'checklist', 'publish'],
    content: repoDoc('release-checklist.md'),
  },
  {
    id: 'release-prep',
    title: t('Release Prep Notes', 'Ghi chú chuẩn bị release', '发布准备记录'),
    eyebrow: t('Current readiness snapshot', 'Ảnh chụp readiness hiện tại', '当前就绪快照'),
    path: 'docs-for-repobrain/docs/release-prep-2026-04-20.md',
    summary: t(
      'A dated project health review with strengths, weaknesses, verification results, and release-note direction.',
      'Bản đánh giá sức khỏe dự án theo ngày, gồm điểm mạnh, điểm yếu, kết quả kiểm tra và hướng viết release note.',
      '按日期记录的项目健康评估，包含优势、短板、验证结果和发布说明方向。',
    ),
    audience: t('Release owners and maintainers', 'Chủ release và maintainer', '发布负责人和维护者'),
    tags: ['release', 'readiness', 'notes'],
    content: repoDoc('release-prep-2026-04-20.md'),
  },
  {
    id: 'demo-script',
    title: t('Demo Script', 'Kịch bản demo', '演示脚本'),
    eyebrow: t('Show the product well', 'Demo sản phẩm cho đẹp', '把产品讲清楚'),
    path: 'docs-for-repobrain/docs/demo-script.md',
    summary: t(
      'A practical sequence for live demos that keeps the story grounded and legible to non-experts.',
      'Một chuỗi thao tác thực tế cho live demo, giúp câu chuyện vẫn grounded và dễ hiểu với người không chuyên.',
      '一套适合现场演示的实际顺序，让叙事既 grounded，又能让非专家看懂。',
    ),
    audience: t('Demo presenters and OSS launch prep', 'Người demo và người chuẩn bị OSS launch', '演示者与 OSS 发布准备者'),
    tags: ['demo', 'presentation', 'script'],
    content: repoDoc('demo-script.md'),
  },
  {
    id: 'meeting-status',
    title: t('Meeting Status', 'Trạng thái cuộc họp', '会议状态'),
    eyebrow: t('Current sprint snapshot', 'Ảnh chụp sprint hiện tại', '当前 sprint 快照'),
    path: 'docs-for-repobrain/docs/meeting-status-2026-04-19.md',
    summary: t(
      'A meeting-style status note that answers what is done, what is in progress, what is blocked, and the current ETA.',
      'Ghi chú trạng thái kiểu cuộc họp, trả lời phần nào đã xong, phần nào đang làm, phần nào bị chặn và ETA hiện tại.',
      '一份会议式状态记录，说明哪些已完成、哪些进行中、哪些被阻塞，以及当前 ETA。',
    ),
    audience: t('Maintainers, reviewers, and planning sessions', 'Maintainer, reviewer và các buổi lập kế hoạch', '维护者、评审者与计划会议'),
    tags: ['status', 'meeting', 'plan', 'eta'],
    content: repoDoc('meeting-status-2026-04-19.md'),
  },
  {
    id: 'product-spec',
    title: t('Product Spec', 'Đặc tả sản phẩm', '产品规格'),
    eyebrow: t('Scope and user jobs', 'Phạm vi và nhu cầu người dùng', '范围与用户任务'),
    path: 'docs-for-repobrain/docs/product-spec.md',
    summary: t(
      'The one-sentence pitch, target users, v1 scope, non-goals, and success criteria for RepoBrain.',
      'Câu giới thiệu ngắn, người dùng mục tiêu, phạm vi v1, non-goals và tiêu chí thành công của RepoBrain.',
      'RepoBrain 的一句话定位、目标用户、v1 范围、非目标和成功标准。',
    ),
    audience: t('Product, engineering, and OSS reviewers', 'Product, kỹ thuật và reviewer mã nguồn mở', '产品、工程与开源评审者'),
    tags: ['product', 'scope', 'spec'],
    content: repoDoc('product-spec.md'),
  },
  {
    id: 'config',
    title: t('Configuration', 'Cấu hình', '配置'),
    eyebrow: t('Runtime setup', 'Thiết lập runtime', '运行时设置'),
    path: 'docs-for-repobrain/docs/config.md',
    summary: t(
      'Explains `repobrain.toml`, indexing limits, parser toggles, provider choices, and environment expectations.',
      'Giải thích `repobrain.toml`, giới hạn index, công tắc parser, lựa chọn provider và kỳ vọng môi trường.',
      '解释 `repobrain.toml`、索引限制、parser 开关、provider 选择和环境要求。',
    ),
    audience: t('Operators and maintainers', 'Người vận hành và maintainer', '操作者与维护者'),
    tags: ['config', 'providers', 'runtime'],
    content: repoDoc('config.md'),
  },
  {
    id: 'contracts',
    title: t('Contracts', 'Hợp đồng giao tiếp', '接口契约'),
    eyebrow: t('Public shapes', 'Dạng dữ liệu công khai', '公开结构'),
    path: 'docs-for-repobrain/docs/contracts.md',
    summary: t(
      'Defines CLI, MCP, payload, and diagnostics contracts so integrations can depend on stable shapes.',
      'Định nghĩa hợp đồng CLI, MCP, payload và diagnostics để các tích hợp có thể dựa vào dạng dữ liệu ổn định.',
      '定义 CLI、MCP、payload 和 diagnostics 契约，让集成方可以依赖稳定结构。',
    ),
    audience: t('Integrators and maintainers', 'Người tích hợp và maintainer', '集成者与维护者'),
    tags: ['contracts', 'api', 'mcp', 'cli'],
    content: repoDoc('contracts.md'),
  },
  {
    id: 'decision-log',
    title: t('Decision Log', 'Nhật ký quyết định', '决策日志'),
    eyebrow: t('Architecture decisions', 'Quyết định kiến trúc', '架构决策'),
    path: 'docs-for-repobrain/docs/decision-log.md',
    summary: t(
      'Records the major technical choices behind RepoBrain and the tradeoffs accepted by the project.',
      'Ghi lại các lựa chọn kỹ thuật quan trọng phía sau RepoBrain và những tradeoff dự án đã chấp nhận.',
      '记录 RepoBrain 背后的主要技术选择，以及项目接受的取舍。',
    ),
    audience: t('Engineers reading project history', 'Kỹ sư cần đọc lịch sử dự án', '阅读项目历史的工程师'),
    tags: ['decisions', 'architecture', 'tradeoffs'],
    content: repoDoc('decision-log.md'),
  },
  {
    id: 'implementation-plan',
    title: t('Implementation Plan', 'Kế hoạch triển khai', '实施计划'),
    eyebrow: t('Legacy execution plan', 'Kế hoạch thực thi cũ', '旧执行计划'),
    path: 'docs-for-repobrain/docs/implementation-plan.md',
    summary: t(
      'The older multi-epic implementation plan that framed indexing, retrieval, harness, providers, and OSS polish work.',
      'Kế hoạch triển khai nhiều epic trước đây, bao quát indexing, retrieval, harness, provider và phần hoàn thiện mã nguồn mở.',
      '早期的多 epic 实施计划，覆盖 indexing、retrieval、harness、provider 和开源打磨工作。',
    ),
    audience: t('Maintainers comparing old plan versus current state', 'Maintainer cần so sánh kế hoạch cũ với trạng thái hiện tại', '需要对比旧计划与当前状态的维护者'),
    tags: ['plan', 'implementation', 'history'],
    content: repoDoc('implementation-plan.md'),
  },
  {
    id: 'backlog',
    title: t('Backlog', 'Việc tồn đọng', '待办清单'),
    eyebrow: t('Open work', 'Việc còn mở', '未完成工作'),
    path: 'docs-for-repobrain/docs/backlog.md',
    summary: t(
      'Prioritized backlog items grouped by urgency, including retrieval, parser, release, and UX follow-ups.',
      'Các hạng mục backlog được ưu tiên theo mức khẩn cấp, gồm retrieval, parser, release và UX follow-up.',
      '按紧急程度排序的待办项，包含 retrieval、parser、release 和 UX 后续工作。',
    ),
    audience: t('Maintainers planning next tasks', 'Maintainer đang lên kế hoạch việc tiếp theo', '规划下一步任务的维护者'),
    tags: ['backlog', 'priorities', 'tasks'],
    content: repoDoc('backlog.md'),
  },
  {
    id: 'releases',
    title: t('Releases', 'Bản phát hành', '发布版本'),
    eyebrow: t('Version line strategy', 'Chiến lược nhánh phiên bản', '版本线策略'),
    path: 'docs-for-repobrain/docs/releases.md',
    summary: t(
      'Explains what each release line is meant to prove, from MVP through a stable 1.0 trustable product.',
      'Giải thích mỗi nhánh phát hành cần chứng minh điều gì, từ MVP tới sản phẩm 1.0 ổn định và đáng tin.',
      '说明每条发布线要证明什么，从 MVP 到稳定可信的 1.0 产品。',
    ),
    audience: t('Release owners and roadmap readers', 'Chủ release và người đọc roadmap', '发布负责人和路线图读者'),
    tags: ['releases', 'versions', 'strategy'],
    content: repoDoc('releases.md'),
  },
  {
    id: 'roadmap',
    title: t('Roadmap', 'Lộ trình', '路线图'),
    eyebrow: t('Release track', 'Nhánh phát triển', '发布路线'),
    path: 'docs-for-repobrain/docs/roadmap.md',
    summary: t(
      'The staged release path from MVP toward a stable 1.0 codebase memory product.',
      'Lộ trình phát hành theo giai đoạn từ MVP tới một sản phẩm codebase memory ổn định ở 1.0.',
      '从 MVP 逐步走向稳定 1.0 代码库记忆产品的阶段性发布路线。',
    ),
    audience: t('Anyone planning future work', 'Bất kỳ ai đang lên kế hoạch tương lai', '所有正在规划未来工作的人'),
    tags: ['roadmap', 'versions', 'future'],
    content: repoDoc('roadmap.md'),
  },
  {
    id: 'self-review',
    title: t('Self Review', 'Tự đánh giá', '自我评审'),
    eyebrow: t('Internal assessment', 'Đánh giá nội bộ', '内部评估'),
    path: 'docs-for-repobrain/docs/self-review.md',
    summary: t(
      'A candid assessment of strengths, thin spots, technical debt, and release risks in the current product.',
      'Đánh giá thẳng thắn về điểm mạnh, điểm mỏng, nợ kỹ thuật và rủi ro phát hành của sản phẩm hiện tại.',
      '对当前产品的优势、薄弱点、技术债和发布风险做出的坦诚评估。',
    ),
    audience: t('Maintainers and reviewers', 'Maintainer và reviewer', '维护者与评审者'),
    tags: ['review', 'risks', 'debt'],
    content: repoDoc('self-review.md'),
  },
  {
    id: 'model-provider-roadmap',
    title: t('Model Provider Roadmap', 'Lo trinh model provider', 'Model provider roadmap'),
    eyebrow: t('Next provider work', 'Provider tiep theo', 'Next provider work'),
    path: 'docs-for-repobrain/docs/model-provider-roadmap.md',
    summary: t(
      'Follow-up plan for expanding model providers, starting with Groq model selection.',
      'Ke hoach tiep theo de mo rong provider, bat dau voi Groq model selection.',
      'Follow-up plan for expanding model providers, starting with Groq.',
    ),
    audience: t('Maintainers planning provider work', 'Maintainer lap ke hoach provider', 'Provider maintainers'),
    tags: ['providers', 'groq', 'roadmap'],
    content: repoDoc('model-provider-roadmap.md'),
  },
  {
    id: 'review-vi',
    title: t('Vietnamese Review', 'Review tiếng Việt', '越南语评审'),
    eyebrow: t('Code and product review', 'Review code và sản phẩm', '代码与产品评审'),
    path: 'docs-for-repobrain/docs/review-vi.md',
    summary: t(
      'A Vietnamese technical review focused on findings, risks, regressions, and the fixes already landed.',
      'Bản review kỹ thuật tiếng Việt, tập trung vào finding, rủi ro, regression và các bản sửa đã có.',
      '一份越南语技术评审，关注发现项、风险、回归问题和已经落地的修复。',
    ),
    audience: t('Vietnamese-speaking maintainers and reviewers', 'Maintainer và reviewer dùng tiếng Việt', '使用越南语的维护者与评审者'),
    tags: ['review', 'vietnamese', 'findings'],
    content: repoDoc('review-vi.md'),
  },
  {
    id: 'hidemium-chatbot-plan',
    title: t('Project Plan Meeting Note', 'Ghi chú họp kế hoạch', '项目计划会议记录'),
    eyebrow: t('Plan review snapshot', 'Ảnh chụp review kế hoạch', '计划评审快照'),
    path: 'docs-for-repobrain/docs/hidemium-chatbot-plan.md',
    summary: t(
      'A meeting-style plan review that evaluates the old implementation plan, current reality, and the next three phases.',
      'Bản review kế hoạch kiểu cuộc họp, đánh giá kế hoạch triển khai cũ, thực tế hiện tại và ba giai đoạn tiếp theo.',
      '一份会议式计划评审，评估旧实施计划、当前现实和接下来的三个阶段。',
    ),
    audience: t('Planning sessions and maintainers', 'Các buổi lập kế hoạch và maintainer', '计划会议与维护者'),
    tags: ['plan', 'meeting', 'status'],
    content: repoDoc('hidemium-chatbot-plan.md'),
  },
  {
    id: 'gemini-fallback-handoff',
    title: t('Gemini Fallback Handoff', 'Bàn giao Gemini fallback', 'Gemini fallback 交接'),
    eyebrow: t('Feature handoff note', 'Ghi chú bàn giao tính năng', '功能交接记录'),
    path: 'docs-for-repobrain/docs/gemini-fallback-handoff.md',
    summary: t(
      'A detailed handoff covering Gemini rerank failover, the React browser frontend, verification, and branch context.',
      'Bản bàn giao chi tiết về Gemini rerank failover, frontend React trên trình duyệt, xác minh và ngữ cảnh branch.',
      '详细交接 Gemini rerank failover、React 浏览器前端、验证情况和分支上下文。',
    ),
    audience: t('Maintainers continuing release work', 'Maintainer tiếp tục phần release', '继续发布工作的维护者'),
    tags: ['handoff', 'gemini', 'release'],
    content: repoDoc('gemini-fallback-handoff.md'),
  },
  {
    id: 'progress-artifact-inspection',
    title: t('Artifact Inspection Progress', 'Tiến độ kiểm tra artifact', '构件检查进展'),
    eyebrow: t('Release follow-up', 'Theo dõi phát hành', '发布后续'),
    path: 'docs-for-repobrain/docs/progress-artifact-inspection-2026-04-18.md',
    summary: t(
      'Progress note for frontend asset builds, package build fixes, and strict artifact inspection work.',
      'Ghi chú tiến độ cho build asset frontend, sửa package build và kiểm tra artifact nghiêm ngặt.',
      '记录前端资源构建、包构建修复和严格构件检查工作的进展。',
    ),
    audience: t('Release owners and maintainers', 'Chủ release và maintainer', '发布负责人和维护者'),
    tags: ['progress', 'artifacts', 'release'],
    content: repoDoc('progress-artifact-inspection-2026-04-18.md'),
  },
  {
    id: 'progress-release-validation',
    title: t('Release Validation Progress', 'Tiến độ xác minh phát hành', '发布验证进展'),
    eyebrow: t('Release follow-up', 'Theo dõi phát hành', '发布后续'),
    path: 'docs-for-repobrain/docs/progress-release-validation-2026-04-18.md',
    summary: t(
      'Progress note for release-check work, documentation alignment, and the first release validation follow-up round.',
      'Ghi chú tiến độ cho release-check, đồng bộ tài liệu và vòng follow-up xác minh phát hành đầu tiên.',
      '记录 release-check、文档对齐和第一轮发布验证后续工作的进展。',
    ),
    audience: t('Release owners and maintainers', 'Chủ release và maintainer', '发布负责人和维护者'),
    tags: ['progress', 'release', 'validation'],
    content: repoDoc('progress-release-validation-2026-04-18.md'),
  },
  {
    id: 'progress-remote-release-validation',
    title: t('Remote Release Validation Progress', 'Tiến độ xác minh phát hành từ xa', '远程发布验证进展'),
    eyebrow: t('Remote release blocker note', 'Ghi chú blocker phát hành từ xa', '远程发布阻塞记录'),
    path: 'docs-for-repobrain/docs/progress-remote-release-validation-2026-04-18.md',
    summary: t(
      'Progress note for the remaining remote release workflow validation and live provider checks that still need external access.',
      'Ghi chú tiến độ cho phần xác minh workflow phát hành từ xa và kiểm tra provider thật còn cần quyền truy cập bên ngoài.',
      '记录剩余远程发布 workflow 验证和真实 provider 检查的进展，这些仍需要外部访问权限。',
    ),
    audience: t('Release owners and maintainers', 'Chủ release và maintainer', '发布负责人和维护者'),
    tags: ['progress', 'remote', 'release'],
    content: repoDoc('progress-remote-release-validation-2026-04-18.md'),
  },
]
