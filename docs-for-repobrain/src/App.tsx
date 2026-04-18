import {
  type ChangeEvent,
  startTransition,
  useDeferredValue,
  useEffect,
  useEffectEvent,
  useRef,
  useState,
} from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  ArrowRight,
  Binary,
  BookOpenText,
  Bot,
  Check,
  Command,
  Copy,
  GitBranch,
  Keyboard,
  LayoutDashboard,
  Link2,
  Menu,
  MoonStar,
  Search,
  ShieldCheck,
  Sparkles,
  SunMedium,
  TerminalSquare,
  Workflow,
  X,
} from 'lucide-react'
import { RepoBrainLogo } from './components/RepoBrainLogo'
import {
  commandCatalog,
  docsLibrary,
  faqs,
  localizedDocContent,
  localeOptions,
  navigationSections,
  quickstartSteps,
  releaseStatus,
  repoMap,
  surfaces,
  uiCopy,
  type Locale,
  type LocalizedText,
} from './content'
import './App.css'

type Theme = 'light' | 'dark'
type StatusState = (typeof releaseStatus)[number]['state']

const sectionIcons = [Sparkles, TerminalSquare, Workflow, LayoutDashboard]
const defaultLocale: Locale = 'en'
const defaultTheme: Theme = 'light'
const primaryNavOrder = ['overview', 'quickstart', 'docs-library', 'reader', 'commands']
const primaryNavIds = new Set(primaryNavOrder)
const defaultDocId = docsLibrary.find((entry) => entry.id === 'install')?.id ?? docsLibrary[0]?.id ?? ''

const appUi = {
  brandContext: {
    en: 'Documentation',
    vi: 'Tài liệu',
    zh: '文档',
  },
  navAria: {
    en: 'Documentation navigation',
    vi: 'Điều hướng tài liệu',
    zh: '文档导航',
  },
  menuOpen: {
    en: 'Open navigation',
    vi: 'Mở điều hướng',
    zh: '打开导航',
  },
  menuClose: {
    en: 'Close navigation',
    vi: 'Đóng điều hướng',
    zh: '关闭导航',
  },
  heroEyebrow: {
    en: 'Documentation center',
    vi: 'Trung tâm tài liệu',
    zh: '文档中心',
  },
  heroTitle: {
    en: 'A tighter technical front door for installing, operating, and understanding RepoBrain.',
    vi: 'Một điểm vào gọn hơn để cài đặt, vận hành và đọc RepoBrain theo đúng ngữ cảnh kỹ thuật.',
    zh: '一个更克制的技术入口，用来安装、运行并系统地理解 RepoBrain。',
  },
  heroBody: {
    en: 'The page is organized as a documentation workflow instead of a product pitch: install first, then the quickstart, then the library and reader in the currently selected language.',
    vi: 'Trang này được tổ chức như một luồng tài liệu thay vì một trang giới thiệu: bắt đầu từ cài đặt, tiếp theo là bắt đầu nhanh, rồi tới thư viện và trình đọc theo đúng ngôn ngữ đang chọn.',
    zh: '这个页面按文档工作流组织，而不是按宣传页来写：先安装，再看快速开始，最后进入与当前语言一致的文档库和阅读区。',
  },
  heroPrimary: {
    en: 'Open install guide',
    vi: 'Mở phần cài đặt',
    zh: '打开安装指南',
  },
  heroSecondary: {
    en: 'Open library',
    vi: 'Mở thư viện tài liệu',
    zh: '打开文档库',
  },
  startHereEyebrow: {
    en: 'Starting path',
    vi: 'Lộ trình làm quen',
    zh: '上手路径',
  },
  startHereTitle: {
    en: 'Install first, then follow the shortest reading path through the repo.',
    vi: 'Cài đặt trước, rồi đi theo luồng đọc ngắn nhất để hiểu repo.',
    zh: '先完成安装，再按最短阅读路径理解这个仓库。',
  },
  startHereBody: {
    en: 'This rail keeps the first session focused: install the stack, open the core documents, and check release status only after the basic flow is clear.',
    vi: 'Khối này giữ cho lần đọc đầu tiên có trọng tâm: cài bộ công cụ, mở các tài liệu cốt lõi và chỉ xem trạng thái phát hành sau khi đã nắm được luồng cơ bản.',
    zh: '这一栏让第一次阅读保持聚焦：先装好环境，再读核心文档，等基本路径清楚后再看发布状态。',
  },
  installCommandLabel: {
    en: 'Install command',
    vi: 'Lệnh cài đặt',
    zh: '安装命令',
  },
  starterDocsTitle: {
    en: 'Read these first',
    vi: 'Nên đọc trước',
    zh: '建议先读',
  },
  readerHint: {
    en: 'Each card opens the reader in the currently selected language.',
    vi: 'Mỗi thẻ sẽ mở trình đọc theo đúng ngôn ngữ đang chọn.',
    zh: '每张卡片都会按当前选择的语言打开阅读内容。',
  },
  openInReader: {
    en: 'Open reader',
    vi: 'Mở trình đọc',
    zh: '打开阅读区',
  },
  exploreMore: {
    en: 'More sections',
    vi: 'Mục khác',
    zh: '更多分区',
  },
  logoTagline: {
    en: 'local-first codebase memory engine for AI coding assistants',
    vi: 'bộ máy ghi nhớ codebase ưu tiên cục bộ cho trợ lý lập trình AI',
    zh: '面向 AI 编程助手的本地优先代码库记忆引擎',
  },
  libraryCount: {
    en: 'documents in library',
    vi: 'tài liệu trong thư viện',
    zh: '篇文档',
  },
  selectedDocLabel: {
    en: 'Selected document',
    vi: 'Tài liệu đang chọn',
    zh: '当前文档',
  },
  releaseSnapshot: {
    en: 'Release snapshot',
    vi: 'Tóm tắt phát hành',
    zh: '发布摘要',
  },
  sourceMarkdown: {
    en: 'Document list',
    vi: 'Danh mục tài liệu',
    zh: '文档列表',
  },
  mobileThemeLabel: {
    en: 'Appearance',
    vi: 'Giao diện',
    zh: '外观',
  },
  mobileLanguageLabel: {
    en: 'Language',
    vi: 'Ngôn ngữ',
    zh: '语言',
  },
  searchResultHint: {
    en: 'The current filter applies to the library, command catalog, and FAQ at the same time.',
    vi: 'Bộ lọc hiện tại đang áp dụng đồng thời cho thư viện tài liệu, danh mục lệnh và phần hỏi đáp.',
    zh: '当前筛选会同时作用于文档库、命令目录和常见问题。',
  },
  localizedDocPending: {
    en: 'A localized reader version is not available for this document yet.',
    vi: 'Tài liệu này chưa có bản đọc đã biên tập cho ngôn ngữ hiện tại.',
    zh: '该文档暂时还没有当前语言的整理版阅读内容。',
  },
  shareView: {
    en: 'Share view',
    vi: 'Chia se giao dien',
    zh: 'Share view',
  },
  copyCommand: {
    en: 'Copy command',
    vi: 'Sao chep lenh',
    zh: 'Copy command',
  },
  copied: {
    en: 'Copied',
    vi: 'Da sao chep',
    zh: 'Copied',
  },
  commandCopied: {
    en: 'Command copied to clipboard.',
    vi: 'Da sao chep lenh vao clipboard.',
    zh: 'Command copied to clipboard.',
  },
  shareCopied: {
    en: 'Shareable reader URL copied to clipboard.',
    vi: 'Da sao chep lien ket trinh doc co the chia se.',
    zh: 'Shareable reader URL copied to clipboard.',
  },
  copyFailed: {
    en: 'Clipboard copy is not available in this browser.',
    vi: 'Trinh duyet hien tai khong ho tro sao chep clipboard.',
    zh: 'Clipboard copy is not available in this browser.',
  },
  keyboardHint: {
    en: 'Shortcuts: / focuses search, Esc closes the menu or clears the filter.',
    vi: 'Phim tat: / dua con tro vao o tim kiem, Esc dong menu hoac xoa bo loc.',
    zh: 'Shortcuts: / focuses search, Esc closes the menu or clears the filter.',
  },
} satisfies Record<string, LocalizedText>

const localizedTagCopy: Record<string, LocalizedText> = {
  product: { en: 'Product', vi: 'Sản phẩm', zh: '产品' },
  direction: { en: 'Direction', vi: 'Định hướng', zh: '方向' },
  why: { en: 'Why', vi: 'Lý do', zh: '原因' },
  install: { en: 'Install', vi: 'Cài đặt', zh: '安装' },
  onboarding: { en: 'Onboarding', vi: 'Làm quen', zh: '上手' },
  setup: { en: 'Setup', vi: 'Thiết lập', zh: '配置' },
  run: { en: 'Run', vi: 'Vận hành', zh: '运行' },
  workflow: { en: 'Workflow', vi: 'Quy trình', zh: '流程' },
  demo: { en: 'Demo', vi: 'Trình diễn', zh: '演示' },
  cli: { en: 'CLI', vi: 'CLI', zh: 'CLI' },
  commands: { en: 'Commands', vi: 'Lệnh', zh: '命令' },
  reference: { en: 'Reference', vi: 'Tham chiếu', zh: '参考' },
  architecture: { en: 'Architecture', vi: 'Kiến trúc', zh: '架构' },
  engine: { en: 'Engine', vi: 'Lõi xử lý', zh: '引擎' },
  design: { en: 'Design', vi: 'Thiết kế', zh: '设计' },
  mcp: { en: 'MCP', vi: 'MCP', zh: 'MCP' },
  agent: { en: 'Agent', vi: 'Tác tử', zh: '智能体' },
  integration: { en: 'Integration', vi: 'Tích hợp', zh: '集成' },
  ux: { en: 'UX', vi: 'Trải nghiệm', zh: '体验' },
  frontend: { en: 'Frontend', vi: 'Giao diện', zh: '前端' },
  evaluation: { en: 'Evaluation', vi: 'Đánh giá', zh: '评估' },
  benchmark: { en: 'Benchmark', vi: 'Đối chuẩn', zh: '基准' },
  quality: { en: 'Quality', vi: 'Chất lượng', zh: '质量' },
  production: { en: 'Production', vi: 'Vận hành thật', zh: '生产环境' },
  readiness: { en: 'Readiness', vi: 'Mức sẵn sàng', zh: '就绪度' },
  ship: { en: 'Ship', vi: 'Đưa vào phát hành', zh: '交付' },
  release: { en: 'Release', vi: 'Phát hành', zh: '发布' },
  checklist: { en: 'Checklist', vi: 'Danh mục kiểm tra', zh: '检查清单' },
  publish: { en: 'Publish', vi: 'Công bố', zh: '发布' },
  presentation: { en: 'Presentation', vi: 'Trình diễn', zh: '展示' },
  script: { en: 'Script', vi: 'Kịch bản', zh: '脚本' },
  roadmap: { en: 'Roadmap', vi: 'Lộ trình', zh: '路线图' },
  versions: { en: 'Versions', vi: 'Phiên bản', zh: '版本' },
  future: { en: 'Future', vi: 'Định hướng sau', zh: '后续方向' },
}

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') {
    return defaultTheme
  }

  const urlTheme = normalizeTheme(
    window.location.search ? new URLSearchParams(window.location.search).get('theme') : null,
  )
  if (urlTheme) {
    return urlTheme
  }

  const savedTheme = window.localStorage.getItem('repobrain-docs-theme')
  if (savedTheme === 'light' || savedTheme === 'dark') {
    return savedTheme
  }

  return defaultTheme
}

function getInitialLocale(): Locale {
  if (typeof window === 'undefined') {
    return defaultLocale
  }

  const urlLocale = normalizeLocale(
    window.location.search ? new URLSearchParams(window.location.search).get('lang') : null,
  )
  if (urlLocale) {
    return urlLocale
  }

  const savedLocale = window.localStorage.getItem('repobrain-docs-locale')
  if (savedLocale === 'en' || savedLocale === 'vi' || savedLocale === 'zh') {
    return savedLocale
  }

  const browserLocales =
    window.navigator.languages.length > 0 ? window.navigator.languages : [window.navigator.language]

  for (const browserLocale of browserLocales) {
    const normalizedLocale = browserLocale.toLowerCase()

    if (normalizedLocale.startsWith('vi')) {
      return 'vi'
    }

    if (normalizedLocale.startsWith('zh')) {
      return 'zh'
    }

    if (normalizedLocale.startsWith('en')) {
      return 'en'
    }
  }

  return defaultLocale
}

function getInitialQuery() {
  if (typeof window === 'undefined') {
    return ''
  }

  return new URLSearchParams(window.location.search).get('q') ?? ''
}

function getInitialSelectedDocId() {
  if (typeof window === 'undefined') {
    return defaultDocId
  }

  const docId = new URLSearchParams(window.location.search).get('doc')
  if (docId && docsLibrary.some((entry) => entry.id === docId)) {
    return docId
  }

  return defaultDocId
}

function normalizeSearchText(value: string) {
  return value.toLowerCase().replaceAll('`', '').trim()
}

function normalizeTheme(value: string | null): Theme | null {
  return value === 'light' || value === 'dark' ? value : null
}

function normalizeLocale(value: string | null): Locale | null {
  return value === 'en' || value === 'vi' || value === 'zh' ? value : null
}

function localizeText(value: LocalizedText, locale: Locale) {
  return value[locale] ?? value.en
}

function flattenLocalizedText(value: LocalizedText) {
  return `${value.en} ${value.vi} ${value.zh}`
}

function buildSearchText(...values: Array<string | LocalizedText>) {
  return normalizeSearchText(
    values
      .map((value) => (typeof value === 'string' ? value : flattenLocalizedText(value)))
      .join(' '),
  )
}

function localizeTag(tag: string, locale: Locale) {
  const value = localizedTagCopy[tag]
  if (!value) {
    return tag
  }

  return localizeText(value, locale)
}

function buildViewUrl({
  docId,
  locale,
  query,
  theme,
  hash,
}: {
  docId: string
  locale: Locale
  query: string
  theme: Theme
  hash?: string
}) {
  if (typeof window === 'undefined') {
    return ''
  }

  const url = new URL(window.location.href)
  const normalizedQuery = query.trim()
  const normalizedHash = hash ? (hash.startsWith('#') ? hash : `#${hash}`) : url.hash

  if (docId && docId !== defaultDocId) {
    url.searchParams.set('doc', docId)
  } else {
    url.searchParams.delete('doc')
  }

  if (locale !== defaultLocale) {
    url.searchParams.set('lang', locale)
  } else {
    url.searchParams.delete('lang')
  }

  if (theme !== defaultTheme) {
    url.searchParams.set('theme', theme)
  } else {
    url.searchParams.delete('theme')
  }

  if (normalizedQuery) {
    url.searchParams.set('q', normalizedQuery)
  } else {
    url.searchParams.delete('q')
  }

  url.hash = normalizedHash
  return url.toString()
}

async function copyTextToClipboard(value: string) {
  if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value)
    return true
  }

  if (typeof document === 'undefined') {
    return false
  }

  const textarea = document.createElement('textarea')
  textarea.value = value
  textarea.setAttribute('readonly', 'true')
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  textarea.style.pointerEvents = 'none'
  document.body.appendChild(textarea)
  textarea.select()

  const copied = document.execCommand('copy')
  document.body.removeChild(textarea)
  return copied
}

function isTypingTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) {
    return false
  }

  return (
    target.isContentEditable ||
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.tagName === 'SELECT'
  )
}

function App() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme)
  const [locale, setLocale] = useState<Locale>(getInitialLocale)
  const [query, setQuery] = useState(getInitialQuery)
  const [selectedDocId, setSelectedDocId] = useState(getInitialSelectedDocId)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [shouldFocusMobileSearch, setShouldFocusMobileSearch] = useState(false)
  const [copiedActionId, setCopiedActionId] = useState('')
  const [toastMessage, setToastMessage] = useState('')
  const desktopSearchRef = useRef<HTMLInputElement>(null)
  const mobileSearchRef = useRef<HTMLInputElement>(null)
  const copyResetTimeoutRef = useRef<number | null>(null)
  const deferredQuery = useDeferredValue(normalizeSearchText(query))
  const text = (value: LocalizedText) => localizeText(value, locale)
  const spotlightItems = uiCopy.spotlightItems[locale]
  const readingOrderItems = uiCopy.readingOrderItems[locale]
  const currentLocaleOption =
    localeOptions.find((option) => option.code === locale) ?? localeOptions[0]
  const primaryNavigation = primaryNavOrder
    .map((id) => navigationSections.find((section) => section.id === id))
    .filter((section): section is (typeof navigationSections)[number] => Boolean(section))
  const secondaryNavigation = navigationSections.filter((section) => !primaryNavIds.has(section.id))
  const readerNavigation = navigationSections.find((section) => section.id === 'reader')
  const docsNavigation = navigationSections.find((section) => section.id === 'docs-library')
  const commandsNavigation = navigationSections.find((section) => section.id === 'commands')
  const getDocReaderContent = (doc: (typeof docsLibrary)[number]) => {
    if (locale === 'en') {
      return doc.content
    }

    return localizedDocContent[doc.id]?.[locale] ?? text(appUi.localizedDocPending)
  }
  const getDocSearchContent = (doc: (typeof docsLibrary)[number]) => {
    const localizedEntry = localizedDocContent[doc.id]

    return [doc.content, localizedEntry?.vi, localizedEntry?.zh].filter(Boolean).join(' ')
  }

  const visibleDocs = docsLibrary.filter((doc) => {
    if (!deferredQuery) {
      return true
    }

    const haystack = buildSearchText(
      doc.title,
      doc.eyebrow,
      doc.summary,
      doc.audience,
      doc.path,
      doc.tags.join(' '),
      getDocSearchContent(doc).slice(0, 1400),
    )

    return haystack.includes(deferredQuery)
  })

  const visibleCommands = commandCatalog.filter((entry) => {
    if (!deferredQuery) {
      return true
    }

    return buildSearchText(entry.category, entry.command, entry.summary, entry.result).includes(
      deferredQuery,
    )
  })

  const visibleFaqs = faqs.filter((entry) => {
    if (!deferredQuery) {
      return true
    }

    return buildSearchText(entry.question, entry.answer).includes(deferredQuery)
  })

  const effectiveSelectedDocId =
    visibleDocs.find((entry) => entry.id === selectedDocId)?.id ?? visibleDocs[0]?.id ?? ''
  const selectedDoc = effectiveSelectedDocId
    ? docsLibrary.find((entry) => entry.id === effectiveSelectedDocId)
    : undefined
  const selectedDocReaderContent = selectedDoc ? getDocReaderContent(selectedDoc) : ''
  const installStep = quickstartSteps[0]
  const installGuideDoc = docsLibrary.find((entry) => entry.id === 'install')
  const starterDocs = ['install', 'run', 'cli']
    .map((id) => docsLibrary.find((entry) => entry.id === id))
    .filter((entry): entry is NonNullable<typeof entry> => Boolean(entry))
  const passCount = releaseStatus.filter((entry) => entry.state === 'pass').length
  const pendingCount = releaseStatus.filter((entry) => entry.state === 'pending').length
  const statusLabels: Record<StatusState, string> = {
    pass: text(uiCopy.statusPass),
    pending: text(uiCopy.statusPending),
    info: text(uiCopy.statusInfo),
  }
  const currentThemeLabel = theme === 'light' ? text(uiCopy.lightMode) : text(uiCopy.darkMode)
  const releaseSummary =
    locale === 'vi'
      ? `${passCount} đạt / ${pendingCount} chờ xác minh`
      : locale === 'zh'
        ? `${passCount} 项通过 / ${pendingCount} 项待验证`
        : `${passCount} passed / ${pendingCount} pending`
  const onboardingFlow = [
    {
      id: 'overview',
      index: '01',
      title: installGuideDoc ? text(installGuideDoc.title) : text(uiCopy.quickstartTitle),
      description: installGuideDoc ? text(installGuideDoc.summary) : text(uiCopy.quickstartBody),
    },
    {
      id: 'quickstart',
      index: '02',
      title: text(uiCopy.quickstartTitle),
      description: text(uiCopy.quickstartBody),
    },
    {
      id: 'docs-library',
      index: '03',
      title: docsNavigation ? text(docsNavigation.label) : text(uiCopy.docsEyebrow),
      description: text(uiCopy.docsBody),
    },
    {
      id: 'reader',
      index: '04',
      title: readerNavigation ? text(readerNavigation.label) : text(uiCopy.readerEyebrow),
      description: text(uiCopy.readerBody),
    },
    {
      id: 'commands',
      index: '05',
      title: commandsNavigation ? text(commandsNavigation.label) : text(uiCopy.commandsEyebrow),
      description: text(uiCopy.commandsBody),
    },
  ]
  const announceFeedback = useEffectEvent((actionId: string, message: string) => {
    if (copyResetTimeoutRef.current !== null) {
      window.clearTimeout(copyResetTimeoutRef.current)
    }

    setCopiedActionId(actionId)
    setToastMessage(message)
    copyResetTimeoutRef.current = window.setTimeout(() => {
      setCopiedActionId('')
      setToastMessage('')
      copyResetTimeoutRef.current = null
    }, 2200)
  })
  const focusSearchInput = useEffectEvent(() => {
    if (typeof window === 'undefined') {
      return
    }

    if (window.matchMedia('(min-width: 1025px)').matches) {
      desktopSearchRef.current?.focus()
      desktopSearchRef.current?.select()
      return
    }

    if (!isMobileMenuOpen) {
      setShouldFocusMobileSearch(true)
      setIsMobileMenuOpen(true)
      return
    }

    mobileSearchRef.current?.focus()
    mobileSearchRef.current?.select()
  })
  const handleCopyAction = useEffectEvent(
    async (actionId: string, value: string, successMessage: string) => {
      try {
        const copied = await copyTextToClipboard(value)
        if (copied) {
          announceFeedback(actionId, successMessage)
          return
        }
      } catch {
        // Fall through to the generic failure message below.
      }

      setCopiedActionId('')
      setToastMessage(text(appUi.copyFailed))
    },
  )
  const handleGlobalKeyDown = useEffectEvent((event: KeyboardEvent) => {
    if (event.defaultPrevented) {
      return
    }

    if (event.key === '/' && !isTypingTarget(event.target)) {
      event.preventDefault()
      focusSearchInput()
      return
    }

    if (event.key === 'Escape') {
      if (isMobileMenuOpen) {
        event.preventDefault()
        closeMobileMenu()
        return
      }

      if (query) {
        event.preventDefault()
        setQuery('')
      }
    }
  })

  function handleSearchChange(event: ChangeEvent<HTMLInputElement>) {
    const nextValue = event.target.value
    startTransition(() => {
      setQuery(nextValue)
    })
  }

  function closeMobileMenu() {
    setIsMobileMenuOpen(false)
  }

  function toggleTheme() {
    setTheme((current) => (current === 'light' ? 'dark' : 'light'))
  }

  function cycleLocale() {
    const currentIndex = localeOptions.findIndex((option) => option.code === locale)
    const nextLocale = localeOptions[(currentIndex + 1) % localeOptions.length]
    setLocale(nextLocale.code)
  }

  function handleSelectDoc(docId: string, options?: { clearSearch?: boolean }) {
    if (options?.clearSearch) {
      setQuery('')
    }

    setSelectedDocId(docId)
    setIsMobileMenuOpen(false)
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

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    window.localStorage.setItem('repobrain-docs-theme', theme)
  }, [theme])

  useEffect(() => {
    document.documentElement.lang = locale
    document.documentElement.dataset.locale = locale
    window.localStorage.setItem('repobrain-docs-locale', locale)
  }, [locale])

  useEffect(() => {
    document.body.style.overflow = isMobileMenuOpen ? 'hidden' : ''

    return () => {
      document.body.style.overflow = ''
    }
  }, [isMobileMenuOpen])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined
    }

    const mediaQuery = window.matchMedia('(min-width: 1025px)')
    const handleChange = (event: MediaQueryListEvent) => {
      if (event.matches) {
        setIsMobileMenuOpen(false)
        setShouldFocusMobileSearch(false)
      }
    }

    mediaQuery.addEventListener('change', handleChange)

    return () => {
      mediaQuery.removeEventListener('change', handleChange)
    }
  }, [])

  useEffect(() => {
    if (!isMobileMenuOpen || !shouldFocusMobileSearch) {
      return
    }

    mobileSearchRef.current?.focus()
    mobileSearchRef.current?.select()
    setShouldFocusMobileSearch(false)
  }, [isMobileMenuOpen, shouldFocusMobileSearch])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const nextUrl = buildViewUrl({
      docId: effectiveSelectedDocId || selectedDocId || defaultDocId,
      locale,
      query,
      theme,
    })

    if (nextUrl && nextUrl !== window.location.href) {
      window.history.replaceState(null, '', nextUrl)
    }
  }, [effectiveSelectedDocId, locale, query, selectedDocId, theme])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined
    }

    window.addEventListener('keydown', handleGlobalKeyDown)

    return () => {
      window.removeEventListener('keydown', handleGlobalKeyDown)
    }
  }, [handleGlobalKeyDown])

  useEffect(() => {
    return () => {
      if (copyResetTimeoutRef.current !== null) {
        window.clearTimeout(copyResetTimeoutRef.current)
      }
    }
  }, [])

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <div className="header-bar">
            <a className="brand-link" href="#overview" aria-label="RepoBrain documentation home">
              <RepoBrainLogo compact showTagline={false} />
              <span className="brand-context desktop-only">{text(appUi.brandContext)}</span>
            </a>

            <nav className="topbar-nav desktop-only" aria-label={text(appUi.navAria)}>
              {primaryNavigation.map((section) => (
                <a key={section.id} href={`#${section.id}`} onClick={closeMobileMenu}>
                  {text(section.label)}
                </a>
              ))}
            </nav>

            <div className="topbar-actions desktop-only">
              <label className="topbar-search" htmlFor="repo-search">
                <Search size={16} />
                <input
                  id="repo-search"
                  ref={desktopSearchRef}
                  type="search"
                  value={query}
                  onChange={handleSearchChange}
                  placeholder={text(uiCopy.searchPlaceholder)}
                  aria-label={text(uiCopy.searchPlaceholder)}
                />
                <span className="search-shortcut" aria-hidden="true">
                  /
                </span>
              </label>

              <button
                className="theme-toggle-button"
                type="button"
                aria-label={`${text(uiCopy.themeLabel)}: ${currentThemeLabel}`}
                aria-pressed={theme === 'dark'}
                onClick={toggleTheme}
              >
                {theme === 'light' ? <SunMedium size={16} /> : <MoonStar size={16} />}
                <span>{currentThemeLabel}</span>
              </button>

              <div className="locale-switch" role="group" aria-label={text(uiCopy.languageLabel)}>
                {localeOptions.map((option) => (
                  <button
                    className={`locale-button${locale === option.code ? ' active' : ''}`}
                    key={option.code}
                    type="button"
                    aria-pressed={locale === option.code}
                    onClick={() => setLocale(option.code)}
                  >
                    {option.short}
                  </button>
                ))}
              </div>
            </div>

            <div className="mobile-header-actions mobile-only">
              <button
                className="icon-toggle"
                type="button"
                aria-label={`${text(uiCopy.themeLabel)}: ${currentThemeLabel}`}
                aria-pressed={theme === 'dark'}
                onClick={toggleTheme}
              >
                {theme === 'light' ? <SunMedium size={16} /> : <MoonStar size={16} />}
              </button>

              <button
                className="locale-chip"
                type="button"
                aria-label={`${text(uiCopy.languageLabel)}: ${currentLocaleOption.nativeLabel}`}
                onClick={cycleLocale}
              >
                {currentLocaleOption.short}
              </button>

              <button
                className="menu-toggle"
                type="button"
                aria-expanded={isMobileMenuOpen}
                aria-label={isMobileMenuOpen ? text(appUi.menuClose) : text(appUi.menuOpen)}
                onClick={() => setIsMobileMenuOpen((current) => !current)}
              >
                {isMobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
              </button>
            </div>
          </div>

          {isMobileMenuOpen ? (
            <div className="mobile-drawer mobile-only">
              <label className="search-field drawer-search" htmlFor="repo-search-mobile">
                <Search size={18} />
                <input
                  id="repo-search-mobile"
                  ref={mobileSearchRef}
                  type="search"
                  value={query}
                  onChange={handleSearchChange}
                  placeholder={text(uiCopy.searchPlaceholder)}
                  aria-label={text(uiCopy.searchPlaceholder)}
                />
                <span className="search-shortcut" aria-hidden="true">
                  /
                </span>
              </label>

              <div className="mobile-drawer-grid">
                <div className="mobile-nav-group">
                  <span className="control-label">{text(appUi.startHereEyebrow)}</span>
                  <nav className="mobile-nav" aria-label={text(appUi.navAria)}>
                    {primaryNavigation.map((section) => (
                      <a key={section.id} href={`#${section.id}`} onClick={closeMobileMenu}>
                        <span>{text(section.label)}</span>
                        <ArrowRight size={15} />
                      </a>
                    ))}
                  </nav>
                </div>

                <div className="mobile-nav-group">
                  <span className="control-label">{text(appUi.exploreMore)}</span>
                  <nav className="mobile-nav" aria-label={text(appUi.navAria)}>
                    {secondaryNavigation.map((section) => (
                      <a key={section.id} href={`#${section.id}`} onClick={closeMobileMenu}>
                        <span>{text(section.label)}</span>
                        <ArrowRight size={15} />
                      </a>
                    ))}
                  </nav>
                </div>
              </div>

              <div className="drawer-controls">
                <div className="drawer-panel">
                  <span className="control-label">{text(appUi.mobileThemeLabel)}</span>
                  <button
                    className="drawer-theme-button"
                    type="button"
                    aria-label={`${text(uiCopy.themeLabel)}: ${currentThemeLabel}`}
                    aria-pressed={theme === 'dark'}
                    onClick={toggleTheme}
                  >
                    {theme === 'light' ? <SunMedium size={16} /> : <MoonStar size={16} />}
                    <span>{currentThemeLabel}</span>
                  </button>
                </div>

                <div className="drawer-panel">
                  <span className="control-label">{text(appUi.mobileLanguageLabel)}</span>
                  <div className="drawer-locale-switch" role="group" aria-label={text(uiCopy.languageLabel)}>
                    {localeOptions.map((option) => (
                      <button
                        className={`drawer-locale-button${locale === option.code ? ' active' : ''}`}
                        key={option.code}
                        type="button"
                        aria-pressed={locale === option.code}
                        onClick={() => setLocale(option.code)}
                      >
                        <span>{option.short}</span>
                        <small>{option.nativeLabel}</small>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </header>

      <main className="app-main">
        <section className="hero-section" id="overview">
          <div className="hero-grid">
            <div className="hero-copy card">
              <div className="hero-intro">
                <span className="eyebrow">{text(appUi.heroEyebrow)}</span>
                <div className="hero-utility-row">
                  <span>
                    {text(uiCopy.languageLabel)}: <strong>{currentLocaleOption.nativeLabel}</strong>
                  </span>
                  <span>
                    {text(uiCopy.themeLabel)}: <strong>{currentThemeLabel}</strong>
                  </span>
                </div>
              </div>

              <div className="hero-brand">
                <RepoBrainLogo showTagline={false} />
              </div>

              <h1>{text(appUi.heroTitle)}</h1>
              <p className="hero-body">{text(appUi.heroBody)}</p>

              <div className="hero-actions">
                <a className="primary-action" href="#quickstart">
                  <span>{text(appUi.heroPrimary)}</span>
                  <ArrowRight size={16} />
                </a>
                <a className="secondary-action" href="#docs-library">
                  {text(appUi.heroSecondary)}
                </a>
              </div>

              <div className="hero-stats">
                <article className="hero-stat">
                  <span>{text(uiCopy.docsEyebrow)}</span>
                  <strong>{docsLibrary.length}</strong>
                  <small>{text(appUi.libraryCount)}</small>
                </article>
                <article className="hero-stat">
                  <span>{text(uiCopy.commandsEyebrow)}</span>
                  <strong>{commandCatalog.length}</strong>
                  <small>{text(uiCopy.commandsBody)}</small>
                </article>
                <article className="hero-stat wide">
                  <span>{text(appUi.releaseSnapshot)}</span>
                  <strong>{releaseSummary}</strong>
                  <small>{text(uiCopy.releaseBody)}</small>
                </article>
              </div>
            </div>

            <aside className="hero-rail">
              <div className="hero-panel card">
                <div className="panel-head">
                  <span className="eyebrow">{text(appUi.startHereEyebrow)}</span>
                  <div className="interface-state">
                    <span>{currentLocaleOption.short}</span>
                    <span>{currentThemeLabel}</span>
                  </div>
                </div>

                <h2>{text(appUi.startHereTitle)}</h2>
                <p>{text(appUi.startHereBody)}</p>

                <div className="install-card">
                  <div className="install-card-top">
                    <span className="control-label">{text(appUi.installCommandLabel)}</span>
                    <div className="install-card-actions">
                      {installStep ? (
                        <button
                          className={`utility-button copy-button${
                            copiedActionId === 'install-command' ? ' copied' : ''
                          }`}
                          type="button"
                          onClick={() =>
                            void handleCopyAction(
                              'install-command',
                              installStep.command,
                              text(appUi.commandCopied),
                            )
                          }
                        >
                          {copiedActionId === 'install-command' ? <Check size={16} /> : <Copy size={16} />}
                          <span>
                            {copiedActionId === 'install-command'
                              ? text(appUi.copied)
                              : text(appUi.copyCommand)}
                          </span>
                        </button>
                      ) : null}
                      {installStep ? <span className="install-step-tag">01</span> : null}
                    </div>
                  </div>
                  {installStep ? (
                    <>
                      <pre>
                        <code>{installStep.command}</code>
                      </pre>
                      <p className="install-note">{text(installStep.body)}</p>
                    </>
                  ) : null}
                </div>

                <div className="starter-docs">
                  <div className="starter-docs-heading">
                    <strong>{text(appUi.starterDocsTitle)}</strong>
                    <small>{text(appUi.readerHint)}</small>
                  </div>

                  <div className="starter-doc-list">
                    {starterDocs.map((doc) => (
                      <a
                        className="starter-doc-card"
                        key={doc.id}
                        href="#reader"
                        onClick={() => handleSelectDoc(doc.id, { clearSearch: true })}
                      >
                        <span className="doc-list-eyebrow">{text(doc.eyebrow)}</span>
                        <strong>{text(doc.title)}</strong>
                        <small>{text(doc.summary)}</small>
                        <span className="starter-doc-action">{text(appUi.openInReader)}</span>
                      </a>
                    ))}
                  </div>
                </div>

                <div className="hero-meta-row">
                  <article className="meta-card">
                    <span className="control-label">{text(appUi.selectedDocLabel)}</span>
                    <strong>{selectedDoc ? text(selectedDoc.title) : text(uiCopy.noDocumentSelected)}</strong>
                    <small>{selectedDoc?.path ?? text(uiCopy.pickDocumentHint)}</small>
                  </article>

                  <article className="meta-card">
                    <span className="control-label">{text(appUi.releaseSnapshot)}</span>
                    <strong>{releaseSummary}</strong>
                    <small>{text(uiCopy.releaseBody)}</small>
                  </article>
                </div>
              </div>
            </aside>
          </div>

          <div className="journey-grid">
            {onboardingFlow.map((item) => (
              <a className="journey-card" key={item.id} href={`#${item.id}`}>
                <span className="journey-index">{item.index}</span>
                <div className="journey-copy">
                  <strong>{item.title}</strong>
                  <small>{item.description}</small>
                </div>
                <ArrowRight size={16} />
              </a>
            ))}
          </div>
        </section>

        <section className="section-block quickstart-block" id="quickstart">
          <div className="section-heading">
            <span className="eyebrow">{text(uiCopy.quickstartEyebrow)}</span>
            <h2>{text(uiCopy.quickstartTitle)}</h2>
            <p>{text(uiCopy.quickstartBody)}</p>
          </div>

          <div className="quickstart-layout">
            <aside className="quickstart-panel card">
              <div className="quickstart-panel-copy">
                <span className="eyebrow">{text(uiCopy.spotlightEyebrow)}</span>
                <ul className="bullet-grid">
                  {spotlightItems.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="reading-order">
                <h3>{text(uiCopy.readingOrderTitle)}</h3>
                <ol>
                  {readingOrderItems.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
              </div>

              <div className="repo-callouts">
                <div>
                  <BookOpenText size={18} />
                  <p>{text(uiCopy.calloutDocs)}</p>
                </div>
                <div>
                  <ShieldCheck size={18} />
                  <p>{text(uiCopy.calloutDoctor)}</p>
                </div>
                <div>
                  <LayoutDashboard size={18} />
                  <p>{text(uiCopy.calloutCleanup)}</p>
                </div>
              </div>
            </aside>

            <div className="quickstart-steps">
              {quickstartSteps.map((step, index) => (
                <article className="card quickstart-card" key={index}>
                  <span className="step-index">0{index + 1}</span>
                  <div className="quickstart-copy">
                    <h3>{text(step.title)}</h3>
                    <p>{text(step.body)}</p>
                    <pre>
                      <code>{step.command}</code>
                    </pre>
                    <div className="card-action-row">
                      <button
                        className={`utility-button copy-button${
                          copiedActionId === `quickstart-${index}` ? ' copied' : ''
                        }`}
                        type="button"
                        onClick={() =>
                          void handleCopyAction(
                            `quickstart-${index}`,
                            step.command,
                            text(appUi.commandCopied),
                          )
                        }
                      >
                        {copiedActionId === `quickstart-${index}` ? <Check size={16} /> : <Copy size={16} />}
                        <span>
                          {copiedActionId === `quickstart-${index}`
                            ? text(appUi.copied)
                            : text(appUi.copyCommand)}
                        </span>
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section-block docs-section" id="docs-library">
          <div className="section-heading">
            <span className="eyebrow">{text(uiCopy.docsEyebrow)}</span>
            <h2>{text(uiCopy.docsTitle)}</h2>
            <p>{text(uiCopy.docsBody)}</p>
          </div>

          <div className="docs-overview card">
            <div className="docs-overview-copy">
              <span className="eyebrow">{readerNavigation ? text(readerNavigation.label) : text(uiCopy.readerEyebrow)}</span>
              <h3>{selectedDoc ? text(selectedDoc.title) : text(uiCopy.noDocumentSelected)}</h3>
              <p>{query ? text(appUi.searchResultHint) : text(uiCopy.readerBody)}</p>
            </div>

            <div className="docs-overview-stats">
              <article className="overview-pill">
                <strong>{visibleDocs.length}</strong>
                <span>{text(uiCopy.docsUnit)}</span>
              </article>
              <article className="overview-pill">
                <strong>{visibleCommands.length}</strong>
                <span>{text(uiCopy.commandsMatch)}</span>
              </article>
              <article className="overview-pill">
                <strong>{visibleFaqs.length}</strong>
                <span>{text(uiCopy.faqMatch)}</span>
              </article>
            </div>
          </div>

          <div className="docs-workspace">
            <aside className="card docs-sidebar">
              <div className="docs-sidebar-head">
                <span className="eyebrow">{text(appUi.sourceMarkdown)}</span>
                <h3>
                  {visibleDocs.length} {text(appUi.libraryCount)}
                </h3>
                <p>{text(uiCopy.originalMarkdownNote)}</p>
              </div>

              <div className="doc-list">
                {visibleDocs.map((doc) => (
                  <button
                    className={`doc-list-item${selectedDoc?.id === doc.id ? ' active' : ''}`}
                    key={doc.id}
                    type="button"
                    onClick={() => handleSelectDoc(doc.id)}
                  >
                    <span className="doc-list-eyebrow">{text(doc.eyebrow)}</span>
                    <strong>{text(doc.title)}</strong>
                    <small>{text(doc.summary)}</small>
                    <code>{doc.path}</code>
                  </button>
                ))}
              </div>
            </aside>

            <div className="reader-column">
              <div id="reader" className="reader-anchor" />

              {selectedDoc ? (
                <>
                  <div className="card reader-intro">
                    <div className="reader-intro-head">
                      <div className="reader-intro-copy">
                        <span className="eyebrow">
                          {readerNavigation ? text(readerNavigation.label) : text(uiCopy.readerEyebrow)}
                        </span>
                        <h3>{text(selectedDoc.title)}</h3>
                        <p>{text(selectedDoc.summary)}</p>
                      </div>

                      <div className="reader-intro-tools">
                        <button
                          className={`utility-button share-button${
                            copiedActionId === 'share-view' ? ' copied' : ''
                          }`}
                          type="button"
                          onClick={() =>
                            void handleCopyAction(
                              'share-view',
                              buildViewUrl({
                                docId: selectedDoc.id,
                                locale,
                                query,
                                theme,
                                hash: 'reader',
                              }),
                              text(appUi.shareCopied),
                            )
                          }
                        >
                          {copiedActionId === 'share-view' ? <Check size={16} /> : <Link2 size={16} />}
                          <span>
                            {copiedActionId === 'share-view'
                              ? text(appUi.copied)
                              : text(appUi.shareView)}
                          </span>
                        </button>

                        <div className="shortcut-hint">
                          <Keyboard size={16} />
                          <span>{text(appUi.keyboardHint)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="reader-intro-meta">
                      <div className="reader-stat">
                        <strong>{text(uiCopy.sourceFile)}</strong>
                        <code>{selectedDoc.path}</code>
                      </div>
                      <div className="reader-stat">
                        <strong>{text(uiCopy.bestFor)}</strong>
                        <span>{text(selectedDoc.audience)}</span>
                      </div>
                      <div className="reader-tags">
                        {selectedDoc.tags.map((tag) => (
                          <span key={tag}>{locale === 'en' ? tag : localizeTag(tag, locale)}</span>
                        ))}
                      </div>
                    </div>
                  </div>

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
                                  handleSelectDoc(localDocId, { clearSearch: true })
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
                        table: ({ children, ...props }) => (
                          <div className="table-scroll">
                            <table {...props}>{children}</table>
                          </div>
                        ),
                      }}
                    >
                      {selectedDocReaderContent}
                    </ReactMarkdown>
                  </article>
                </>
              ) : (
                <div className="card empty-state">
                  <p>{text(uiCopy.noDocMatches)}</p>
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="section-block" id="commands">
          <div className="section-heading">
            <span className="eyebrow">{text(uiCopy.commandsEyebrow)}</span>
            <h2>{text(uiCopy.commandsTitle)}</h2>
            <p>{text(uiCopy.commandsBody)}</p>
          </div>

          <div className="command-list">
            {visibleCommands.map((entry) => (
              <article className="card command-card" key={entry.command}>
                <div className="command-card-top">
                  <span className="command-category">{text(entry.category)}</span>
                  <div className="command-card-actions">
                    <Command size={16} />
                    <button
                      className={`utility-button copy-button${
                        copiedActionId === `command-${entry.command}` ? ' copied' : ''
                      }`}
                      type="button"
                      onClick={() =>
                        void handleCopyAction(
                          `command-${entry.command}`,
                          entry.command,
                          text(appUi.commandCopied),
                        )
                      }
                    >
                      {copiedActionId === `command-${entry.command}` ? <Check size={16} /> : <Copy size={16} />}
                      <span>
                        {copiedActionId === `command-${entry.command}`
                          ? text(appUi.copied)
                          : text(appUi.copyCommand)}
                      </span>
                    </button>
                  </div>
                </div>

                <div className="command-card-body">
                  <pre>
                    <code>{entry.command}</code>
                  </pre>
                  <div className="command-card-copy">
                    <p>{text(entry.summary)}</p>
                    <small>{text(entry.result)}</small>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="section-grid" id="surfaces">
          <div className="section-block">
            <div className="section-heading">
              <span className="eyebrow">{text(uiCopy.surfacesEyebrow)}</span>
              <h2>{text(uiCopy.surfacesTitle)}</h2>
              <p>{text(uiCopy.surfacesBody)}</p>
            </div>

            <div className="surface-grid">
              {surfaces.map((surface, index) => {
                const Icon = sectionIcons[index % sectionIcons.length]

                return (
                  <article className="card surface-card" key={index}>
                    <div className="surface-icon">
                      <Icon size={20} />
                    </div>
                    <h3>{text(surface.title)}</h3>
                    <p>{text(surface.description)}</p>
                    <small>{text(surface.detail)}</small>
                  </article>
                )
              })}
            </div>
          </div>

          <div className="section-block" id="repo-map">
            <div className="section-heading">
              <span className="eyebrow">{text(uiCopy.repoMapEyebrow)}</span>
              <h2>{text(uiCopy.repoMapTitle)}</h2>
              <p>{text(uiCopy.repoMapBody)}</p>
            </div>

            <div className="repo-map-grid">
              {repoMap.map((entry) => (
                <article className="card repo-map-card" key={entry.path}>
                  <code>{entry.path}</code>
                  <p>{text(entry.summary)}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section-block release-block" id="release-state">
          <div className="section-heading">
            <span className="eyebrow">{text(uiCopy.releaseEyebrow)}</span>
            <h2>{text(uiCopy.releaseTitle)}</h2>
            <p>{text(uiCopy.releaseBody)}</p>
          </div>

          <div className="status-grid">
            {releaseStatus.map((entry, index) => (
              <article className={`card status-card status-${entry.state}`} key={index}>
                <div className="status-pill">{statusLabels[entry.state]}</div>
                <h3>{text(entry.label)}</h3>
                <p>{text(entry.detail)}</p>
              </article>
            ))}
          </div>

          <div className="card release-callout">
            <div>
              <Binary size={18} />
              <p>{text(uiCopy.releaseRemote)}</p>
            </div>
            <div>
              <Bot size={18} />
              <p>{text(uiCopy.releaseHuman)}</p>
            </div>
            <div>
              <GitBranch size={18} />
              <p>{text(uiCopy.releaseNext)}</p>
            </div>
          </div>
        </section>

        <section className="section-block faq-block" id="faq">
          <div className="section-heading">
            <span className="eyebrow">{text(uiCopy.faqEyebrow)}</span>
            <h2>{text(uiCopy.faqTitle)}</h2>
            <p>{text(uiCopy.faqBody)}</p>
          </div>

          <div className="faq-list">
            {visibleFaqs.map((entry, index) => (
              <details className="card faq-item" key={index}>
                <summary>{text(entry.question)}</summary>
                <p>{text(entry.answer)}</p>
              </details>
            ))}
          </div>
        </section>

        <footer className="footer card">
          <div>
            <RepoBrainLogo compact />
            <p>{text(uiCopy.footerBody)}</p>
          </div>

          <div className="footer-links">
            <a href="#overview">{text(uiCopy.footerTop)}</a>
            <a href="#reader">{text(uiCopy.footerReader)}</a>
            <a href="#release-state">{text(uiCopy.footerRelease)}</a>
          </div>
        </footer>
      </main>

      <div className={`floating-toast${toastMessage ? ' visible' : ''}`} aria-live="polite" role="status">
        {toastMessage}
      </div>
    </div>
  )
}

export default App
