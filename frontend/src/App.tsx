import { useState } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { OverviewPage } from './pages/Overview'
import { CasesPage } from './pages/Cases'
import { CaseDetailPage } from './pages/CaseDetail'

type NavItem = {
  id: string
  label: string
  icon: string
  path: string
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', path: '/', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2' },
  { id: 'cases', label: 'Cases', path: '/cases', icon: 'M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
  { id: 'customers', label: 'Customers', path: '/customers', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
  { id: 'operations', label: 'Operations', path: '/operations', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
  { id: 'knowledge', label: 'Knowledge', path: '/knowledge', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
  { id: 'evidence', label: 'Evidence', path: '/evidence', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
]

function Sidebar({ sidebarOpen, setSidebarOpen }: { sidebarOpen: boolean; setSidebarOpen: (v: boolean) => void }) {
  const navigate = useNavigate()
  const location = useLocation()

  const isActive = (item: NavItem) => {
    if (item.path === '/') return location.pathname === '/'
    return location.pathname.startsWith(item.path)
  }

  return (
    <>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-surface-900 text-white flex flex-col transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-3 px-5 py-5 border-b border-surface-700">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <div className="text-sm font-semibold tracking-tight leading-none">SmartResolve</div>
            <div className="text-[11px] text-surface-400 mt-0.5">Telecom Operations</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" role="navigation" aria-label="Main navigation">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                navigate(item.path)
                setSidebarOpen(false)
              }}
              aria-current={isActive(item) ? 'page' : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive(item)
                  ? 'bg-brand-600/20 text-brand-300'
                  : 'text-surface-300 hover:bg-surface-800 hover:text-white'
              }`}
            >
              <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
              </svg>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-surface-700">
          <div className="flex items-center gap-2 text-xs text-surface-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" aria-hidden="true" />
            System Operational
          </div>
        </div>
      </aside>
    </>
  )
}

function Header({ setSidebarOpen }: { sidebarOpen: boolean; setSidebarOpen: (v: boolean) => void }) {
  const location = useLocation()

  const getPageInfo = () => {
    const path = location.pathname
    if (path === '/') return { title: 'Operations Overview', desc: 'Monitor network health, support workload, and incidents' }
    if (path.startsWith('/cases/')) return { title: 'Case Investigation', desc: 'Investigate customer issue using operational and service data' }
    if (path === '/cases') return { title: 'Cases', desc: 'Investigate customer issues using operational and service data' }
    if (path.startsWith('/customers')) return { title: 'Customer Directory', desc: 'Access customer account information' }
    if (path.startsWith('/operations')) return { title: 'Network Operations', desc: 'Monitor network operational records' }
    if (path.startsWith('/knowledge')) return { title: 'Knowledge Base', desc: 'Telecom policies and procedures' }
    if (path.startsWith('/evidence')) return { title: 'Evidence & Citations', desc: 'AI-generated evidence and citations' }
    return { title: 'SmartResolve', desc: '' }
  }

  const { title, desc } = getPageInfo()

  return (
    <header className="h-14 border-b border-surface-200 bg-white flex items-center justify-between px-4 lg:px-6 shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setSidebarOpen(true)}
          className="lg:hidden p-1.5 rounded-lg hover:bg-surface-100 text-surface-600"
          aria-label="Open menu"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div>
          <h1 className="text-sm font-semibold text-surface-900 leading-none">{title}</h1>
          <p className="text-xs text-surface-500 mt-0.5">{desc}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-2 text-xs text-surface-500 bg-surface-50 rounded-lg px-3 py-1.5 border border-surface-200">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Data Layer v0.4
        </div>
        <div className="w-8 h-8 rounded-full bg-surface-200 flex items-center justify-center text-surface-600 text-xs font-medium" aria-label="Operator avatar">
          OP
        </div>
      </div>
    </header>
  )
}

// ── Placeholder Pages ─────────────────────────────────

function CustomersPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [segment, setSegment] = useState('')
  const [data, setData] = useState<{ data: { id: number; customer_number: string; name: string; email: string; segment: string; status: string }[]; pagination: { total: number; page: number; total_pages: number } } | null>(null)
  const [loading, setLoading] = useState(true)

  useState(() => {
    const params = new URLSearchParams()
    params.set('page', String(page))
    params.set('page_size', '15')
    if (search) params.set('search', search)
    if (segment) params.set('segment', segment)
    fetch(`/api/customers?${params.toString()}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  })

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-surface-900">Customers</h2>
        <p className="text-sm text-surface-500 mt-0.5">Access customer account information.</p>
      </div>
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          placeholder="Search customers..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          className="flex-1 px-3 py-2 text-sm border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
        <select
          value={segment}
          onChange={(e) => { setSegment(e.target.value); setPage(1) }}
          className="px-3 py-2 text-sm border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All Segments</option>
          <option value="consumer">Consumer</option>
          <option value="small_business">Small Business</option>
          <option value="enterprise">Enterprise</option>
        </select>
      </div>
      <div className="bg-white rounded-xl border border-surface-200">
        <div className="divide-y divide-surface-100">
          {loading && <div className="p-8 text-center text-sm text-surface-400">Loading...</div>}
          {data?.data.map((c) => (
            <div key={c.id} className="px-5 py-3 hover:bg-surface-50">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-mono text-surface-400">{c.customer_number}</span>
                  <p className="text-sm font-medium text-surface-900 mt-0.5">{c.name}</p>
                  <p className="text-xs text-surface-500">{c.email}</p>
                </div>
                <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded border ${
                  c.status === 'active' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                  c.status === 'suspended' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                  'bg-surface-50 text-surface-600 border-surface-200'
                }`}>
                  {c.status}
                </span>
              </div>
            </div>
          ))}
          {data && data.data.length === 0 && <div className="p-8 text-center text-sm text-surface-400">No customers found</div>}
        </div>
      </div>
      {data && data.pagination.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(p => p - 1)}
            disabled={page <= 1}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-xs text-surface-500">Page {data.pagination.page} of {data.pagination.total_pages}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page >= data.pagination.total_pages}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

function OperationsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-surface-900">Network Operations</h2>
        <p className="text-sm text-surface-500 mt-0.5">Monitor network operational records.</p>
      </div>
      <div className="bg-white rounded-xl border border-surface-200 p-8 text-center">
        <p className="text-sm text-surface-500">Use the Overview dashboard for network operations monitoring.</p>
      </div>
    </div>
  )
}

function KnowledgePage() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-surface-900">Knowledge Base</h2>
        <p className="text-sm text-surface-500 mt-0.5">Telecom policies, runbooks, and operational documents.</p>
      </div>
      <div className="bg-white rounded-xl border border-surface-200 p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-surface-100 flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
        <h4 className="text-sm font-medium text-surface-700 mb-1">Knowledge Base</h4>
        <p className="text-xs text-surface-500 max-w-sm mx-auto">
          Telecom policies, runbooks, and operational documents will be indexed here using local RAG retrieval in a future stage.
        </p>
      </div>
    </div>
  )
}

function EvidencePage() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-surface-900">Evidence & Citations</h2>
        <p className="text-sm text-surface-500 mt-0.5">AI-generated evidence, citations, and resolution recommendations.</p>
      </div>
      <div className="bg-white rounded-xl border border-surface-200 p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-surface-100 flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <h4 className="text-sm font-medium text-surface-700 mb-1">Evidence & Citations</h4>
        <p className="text-xs text-surface-500 max-w-sm mx-auto">
          AI-generated evidence, citations, and resolution recommendations will appear here after the Gemini reasoning engine is implemented.
        </p>
      </div>
    </div>
  )
}

// ── Layout ────────────────────────────────────────────

function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-surface-50">
      <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="flex-1 flex flex-col min-w-0">
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<OverviewPage />} />
              <Route path="/cases" element={<CasesPage />} />
              <Route path="/cases/:ticketId" element={<CaseDetailPage />} />
              <Route path="/customers" element={<CustomersPage />} />
              <Route path="/operations" element={<OperationsPage />} />
              <Route path="/knowledge" element={<KnowledgePage />} />
              <Route path="/evidence" element={<EvidencePage />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  )
}

// ── App ───────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  )
}
