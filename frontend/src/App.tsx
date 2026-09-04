import { useState } from 'react'
import { OverviewPage } from './pages/Overview'
import { StatusBadge, PriorityBadge, SegmentBadge, TechBadge } from './components/common/Badges'
import { LoadingState, ErrorState, EmptyState } from './components/common/States'

// ── Types ─────────────────────────────────────────────

type NavItem = {
  id: string
  label: string
  icon: string
}

type Customer = {
  id: number
  customer_number: string
  name: string
  email: string
  phone: string
  segment: string
  status: string
}

type Ticket = {
  id: number
  ticket_number: string
  subject: string
  category: string
  priority: string
  status: string
  customer_name: string
}

type NetworkSite = {
  id: number
  site_code: string
  site_name: string
  technology: string
  region: string
  city: string
  capacity_percent: number
  status: string
}

// ── API Hook ──────────────────────────────────────────

function useApi<T>(url: string) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useState(() => {
    setLoading(true)
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((json) => { setData(json); setLoading(false) })
      .catch((err) => { setError(err.message); setLoading(false) })
  })

  return { data, loading, error }
}

// ── Navigation ────────────────────────────────────────

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2' },
  { id: 'cases', label: 'Cases', icon: 'M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
  { id: 'customers', label: 'Customers', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
  { id: 'operations', label: 'Operations', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
  { id: 'knowledge', label: 'Knowledge', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
  { id: 'evidence', label: 'Evidence', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
]

// ── App ───────────────────────────────────────────────

function App() {
  const [activeNav, setActiveNav] = useState('overview')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-surface-50">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
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
                setActiveNav(item.id)
                setSidebarOpen(false)
              }}
              aria-current={activeNav === item.id ? 'page' : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeNav === item.id
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

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
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
              <h1 className="text-sm font-semibold text-surface-900 leading-none">
                {activeNav === 'overview' ? 'Operations Overview' :
                 activeNav === 'cases' ? 'Active Cases' :
                 activeNav === 'customers' ? 'Customer Directory' :
                 activeNav === 'operations' ? 'Network Operations' :
                 activeNav === 'knowledge' ? 'Knowledge Base' :
                 'Evidence & Citations'}
              </h1>
              <p className="text-xs text-surface-500 mt-0.5">
                {activeNav === 'overview' ? 'Monitor network health, support workload, and incidents' :
                 activeNav === 'cases' ? 'Track and manage open support cases' :
                 activeNav === 'customers' ? 'Access customer account information' :
                 activeNav === 'operations' ? 'Monitor network operational records' :
                 activeNav === 'knowledge' ? 'Telecom policies and procedures' :
                 'AI-generated evidence and citations'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs text-surface-500 bg-surface-50 rounded-lg px-3 py-1.5 border border-surface-200">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Data Layer v0.3
            </div>
            <div className="w-8 h-8 rounded-full bg-surface-200 flex items-center justify-center text-surface-600 text-xs font-medium" aria-label="Operator avatar">
              OP
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto">
            {activeNav === 'overview' && <OverviewPage />}
            {activeNav === 'cases' && <CasesPage />}
            {activeNav === 'customers' && <CustomersPage />}
            {activeNav === 'operations' && <OperationsPage />}
            {activeNav === 'knowledge' && <KnowledgePage />}
            {activeNav === 'evidence' && <EvidencePage />}
          </div>
        </main>
      </div>
    </div>
  )
}

// ── Cases Page ────────────────────────────────────────

function CasesPage() {
  const { data, loading, error } = useApi<{ data: Ticket[]; pagination: { total: number } }>(
    '/api/tickets?status=open&page_size=10'
  )
  const { data: escalated } = useApi<{ data: Ticket[]; pagination: { total: number } }>(
    '/api/tickets?status=escalated&page_size=5'
  )

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-surface-200 p-4">
          <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">Open Cases</p>
          <p className="text-2xl font-bold text-surface-900 mt-1">{data?.pagination.total || 0}</p>
        </div>
        <div className="bg-white rounded-xl border border-surface-200 p-4">
          <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">Escalated</p>
          <p className="text-2xl font-bold text-red-600 mt-1">{escalated?.pagination.total || 0}</p>
        </div>
        <div className="bg-white rounded-xl border border-surface-200 p-4">
          <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">Pending</p>
          <p className="text-2xl font-bold text-surface-900 mt-1">--</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-surface-200">
        <div className="px-5 py-4 border-b border-surface-200">
          <h3 className="text-sm font-semibold text-surface-900">Open Cases</h3>
        </div>
        <div className="divide-y divide-surface-100">
          {(data?.data || []).map((ticket) => (
            <div key={ticket.id} className="px-5 py-3 flex items-center justify-between hover:bg-surface-50">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-surface-400">{ticket.ticket_number}</span>
                  <PriorityBadge priority={ticket.priority} />
                </div>
                <p className="text-sm text-surface-800 mt-0.5 truncate">{ticket.subject}</p>
                <p className="text-xs text-surface-500 mt-0.5">{ticket.customer_name}</p>
              </div>
              <StatusBadge status={ticket.status} />
            </div>
          ))}
          {(!data?.data || data.data.length === 0) && (
            <EmptyState message="No open cases" />
          )}
        </div>
      </div>
    </div>
  )
}

// ── Customers Page ────────────────────────────────────

function Pagination({ page, totalPages, onPageChange }: { page: number; totalPages: number; onPageChange: (p: number) => void }) {
  return (
    <div className="flex items-center justify-center gap-2">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="px-3 py-1.5 text-xs font-medium rounded-lg border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Previous
      </button>
      <span className="text-xs text-surface-500">Page {page} of {totalPages}</span>
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="px-3 py-1.5 text-xs font-medium rounded-lg border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </div>
  )
}

function CustomersPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [segment, setSegment] = useState('')
  const { data, loading, error } = useApi<{ data: Customer[]; pagination: { total: number; page: number; total_pages: number } }>(
    `/api/customers?page=${page}&page_size=15${search ? `&search=${encodeURIComponent(search)}` : ''}${segment ? `&segment=${segment}` : ''}`
  )

  if (loading && !data) return <LoadingState />
  if (error) return <ErrorState message={error} />

  return (
    <div className="space-y-4">
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
          {(data?.data || []).map((c) => (
            <div key={c.id} className="px-5 py-3 hover:bg-surface-50">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-surface-400">{c.customer_number}</span>
                    <SegmentBadge segment={c.segment} />
                  </div>
                  <p className="text-sm font-medium text-surface-900 mt-0.5">{c.name}</p>
                  <p className="text-xs text-surface-500">{c.email}</p>
                </div>
                <StatusBadge status={c.status} />
              </div>
            </div>
          ))}
          {(!data?.data || data.data.length === 0) && <EmptyState message="No customers found" />}
        </div>
      </div>

      {data && data.pagination.total_pages > 1 && (
        <Pagination
          page={data.pagination.page}
          totalPages={data.pagination.total_pages}
          onPageChange={setPage}
        />
      )}
    </div>
  )
}

// ── Operations Page ───────────────────────────────────

function OperationsPage() {
  const { data: sites, loading: sitesLoading } = useApi<{ data: NetworkSite[]; pagination: { total: number } }>(
    '/api/network/sites?page_size=20'
  )
  const { data: incidents } = useApi<{ data: { id: number }[]; pagination: { total: number } }>(
    '/api/incidents/active?page_size=5'
  )

  if (sitesLoading) return <LoadingState />

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-surface-200 p-4">
          <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">Total Sites</p>
          <p className="text-2xl font-bold text-surface-900 mt-1">{sites?.pagination.total || 0}</p>
        </div>
        <div className="bg-white rounded-xl border border-surface-200 p-4">
          <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">Active Incidents</p>
          <p className="text-2xl font-bold text-surface-900 mt-1">{incidents?.pagination.total || 0}</p>
        </div>
        <div className="bg-white rounded-xl border border-surface-200 p-4">
          <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">Degraded Sites</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">
            {sites?.data.filter(s => s.status === 'degraded').length || 0}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-surface-200">
        <div className="px-5 py-4 border-b border-surface-200">
          <h3 className="text-sm font-semibold text-surface-900">Network Sites</h3>
        </div>
        <div className="divide-y divide-surface-100">
          {(sites?.data || []).map((site) => (
            <div key={site.id} className="px-5 py-3 flex items-center justify-between hover:bg-surface-50">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-surface-400">{site.site_code}</span>
                  <TechBadge technology={site.technology} />
                </div>
                <p className="text-sm text-surface-800 mt-0.5">{site.site_name}</p>
                <p className="text-xs text-surface-500">{site.region} - {site.city}</p>
              </div>
              <div className="text-right">
                <StatusBadge status={site.status} />
                <div className="mt-1">
                  <div className="w-20 h-1.5 bg-surface-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        site.capacity_percent > 85 ? 'bg-red-400' :
                        site.capacity_percent > 65 ? 'bg-amber-400' : 'bg-emerald-400'
                      }`}
                      style={{ width: `${site.capacity_percent}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-surface-400 mt-0.5">{site.capacity_percent}% capacity</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Placeholder Pages ─────────────────────────────────

function KnowledgePage() {
  return (
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
  )
}

function EvidencePage() {
  return (
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
  )
}

export default App
