import { docsLibrary, type LocalizedText } from '../content'
import { t } from '../i18n/localize'

export type Theme = 'light' | 'dark'

export type DocsNavItem = {
  id: string
  label: LocalizedText
  docIds?: string[]
  href?: string
  scrollTarget?: string
}

export type DocsSidebarGroup = {
  id: string
  label: LocalizedText
  docIds: string[]
}

export const defaultLocale = 'en'
export const defaultTheme: Theme = 'dark'
export const defaultDocId = docsLibrary.find((entry) => entry.id === 'install')?.id ?? docsLibrary[0]?.id ?? ''
export const githubRepoUrl = 'https://github.com/hieuchaydi/RepoBrain'
export const quickstartDocIds = ['install', 'docker', 'run', 'config']

export const chromeUi = {
  navigation: t('Documentation navigation', 'Điều hướng tài liệu', '文档导航'),
  docsIndex: t('Docs index', 'Mục lục tài liệu', '文档目录'),
  repoLink: t('GitHub', 'GitHub', 'GitHub'),
  repoBrowse: t('Browse repository', 'Mở repository', '浏览仓库'),
  openGithub: t('Open on GitHub', 'Mở trên GitHub', '在 GitHub 打开'),
  searchShortcut: t('Ctrl K', 'Ctrl K', 'Ctrl K'),
  clearSearch: t('Clear', 'Xóa', '清除'),
  menuOpen: t('Open docs index', 'Mở mục lục tài liệu', '打开文档目录'),
  menuClose: t('Close docs index', 'Đóng mục lục tài liệu', '关闭文档目录'),
  source: t('Source file', 'Tệp nguồn', '源文件'),
  relatedDocs: t('Related documents', 'Tài liệu liên quan', '相关文档'),
  relatedDocsBody: t(
    'Keep reading from nearby documents in the same area.',
    'Đọc tiếp các tài liệu cùng nhóm để không đứt mạch.',
    '继续阅读同一领域的相关文档。',
  ),
  noResultsTitle: t('No matching documents', 'Không có tài liệu phù hợp', '没有匹配的文档'),
  noResultsBody: t(
    'Clear the current filter to reopen the full documentation set.',
    'Xóa bộ lọc hiện tại để mở lại toàn bộ tài liệu.',
    '清除当前筛选条件即可重新打开完整文档集。',
  ),
  sidebarFiltered: t('Filtering', 'Đang lọc', '正在筛选'),
  moreNotes: t('More notes', 'Ghi chú khác', '更多记录'),
  missingDocBody: t(
    'This localized version is being prepared. Use the GitHub source link if you need the original repository document now.',
    'Bản dịch cho tài liệu này đang được chuẩn bị. Nếu cần xem tài liệu nguồn ngay, hãy dùng liên kết GitHub phía trên.',
    '该文档的本地化版本正在准备中。如需立即查看源文档，请使用上方的 GitHub 链接。',
  ),
  terminalPreviewTitle: t('RepoBrain CLI in practice', 'RepoBrain CLI khi chạy thực tế', 'RepoBrain CLI 实际运行画面'),
  terminalPreviewBody: t(
    'A compact terminal view of the project flow: initialize, review, query, and close with release gates.',
    'Một khung terminal cô đọng luồng của dự án: khởi tạo, review, truy vấn rồi khép lại bằng cổng phát hành.',
    '一个紧凑的终端视图，展示项目流程：初始化、评审、查询，并用发布门禁收尾。',
  ),
  terminalPreviewAlt: t(
    'Terminal screenshot-style preview of RepoBrain CLI commands and grounded output.',
    'Ảnh minh họa kiểu terminal cho các lệnh RepoBrain CLI và kết quả có căn cứ.',
    'RepoBrain CLI 命令和有依据输出的终端截图式预览。',
  ),
} satisfies Record<string, LocalizedText>

export const docsNavItems: DocsNavItem[] = [
  {
    id: 'overview',
    label: t('Overview', 'Tổng quan', '概览'),
    docIds: ['vision', 'product-spec', 'meeting-status'],
  },
  {
    id: 'quickstart',
    label: t('Quickstart', 'Bắt đầu', '快速开始'),
    docIds: quickstartDocIds,
    scrollTarget: 'quickstart',
  },
  {
    id: 'reference',
    label: t('Reference', 'Tham chiếu', '参考'),
    docIds: ['cli', 'docker', 'contracts', 'architecture', 'mcp'],
  },
  {
    id: 'resources',
    label: t('Resources', 'Tài nguyên', '资源'),
    docIds: ['evaluation', 'ux', 'decision-log', 'demo-script'],
  },
  {
    id: 'release',
    label: t('Release', 'Phát hành', '发布'),
    docIds: ['production-readiness', 'release-checklist', 'release-prep', 'releases', 'roadmap', 'backlog'],
  },
]

export const docsSidebarGroups: DocsSidebarGroup[] = [
  {
    id: 'get-started',
    label: t('Get started', 'Bắt đầu', '开始'),
    docIds: ['vision', 'install', 'docker', 'run', 'cli', 'config'],
  },
  {
    id: 'use-repobrain',
    label: t('Use RepoBrain', 'Dùng RepoBrain', '使用 RepoBrain'),
    docIds: ['architecture', 'mcp', 'contracts', 'evaluation', 'ux', 'demo-script'],
  },
  {
    id: 'ship-and-release',
    label: t('Ship and release', 'Phát hành', '发布与交付'),
    docIds: ['production-readiness', 'release-checklist', 'release-prep', 'releases', 'roadmap', 'meeting-status'],
  },
  {
    id: 'project-notes',
    label: t('Project notes', 'Ghi chú dự án', '项目记录'),
    docIds: [
      'product-spec',
      'decision-log',
      'implementation-plan',
      'backlog',
      'self-review',
      'model-provider-roadmap',
      'review-vi',
      'hidemium-chatbot-plan',
      'gemini-fallback-handoff',
      'progress-artifact-inspection',
      'progress-release-validation',
      'progress-remote-release-validation',
      'auto-file-context-plan',
    ],
  },
]
