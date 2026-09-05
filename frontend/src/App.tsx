import { useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { OverviewPage } from './pages/Overview'
import { CasesPage } from './pages/Cases'
import { CaseDetailPage } from './pages/CaseDetail'
import { KnowledgePage } from './pages/Knowledge'
import { KnowledgeDetailPage } from './pages/KnowledgeDetail'
import AgentConsolePage from './pages/AgentConsole'

type NavItem = {
  id: string
  label: string
  icon: string
  path: string
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', path: '/', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2' },
  { id: 'console', label: 'Agent Console', path: '/console', icon: 'M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' },
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
    if (path === '/console') return { title: 'Agent Console', desc: 'Analyze cases with Mode A/B/C deterministic classification' }
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
          Data Layer v0.5
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
  const [data, setData] = useState<{ data: { id: number; customer_number: string; name: string; email: string; phone: string; segment: string; status: string }[]; pagination: { total: number; page: number; total_pages: number } } | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.set('page', String(page))
      params.set('page_size', '15')
      if (search) params.set('search', search)
      if (segment) params.set('segment', segment)
      const res = await fetch(`/api/customers?${params.toString()}`)
      const d = await res.json()
      setData(d)
    } catch {
      // failed
    }
    setLoading(false)
  }, [page, search, segment])

  useEffect(() => { fetchData() }, [fetchData])

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
  const navigate = useNavigate()
  const [networkData, setNetworkData] = useState<{ data: { id: number; site_code: string; site_name: string; technology: string; region: string; city: string; state: string; status: string; capacity_percent: number }[]; pagination: { total: number } } | null>(null)
  const [incidents, setIncidents] = useState<{ data: { id: number; incident_number: string; title: string; severity: string; region: string; status: string; affected_service: string; started_at: string; affected_customers_estimate: number }[]; pagination: { total: number } } | null>(null)
  const [tickets, setTickets] = useState<{ data: { id: number; ticket_number: string; status: string; priority: string; category: string }[]; pagination: { total: number } } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true)
      try {
        const [sitesRes, incRes, tkRes] = await Promise.all([
          fetch('/api/network/sites?page_size=100'),
          fetch('/api/incidents?page_size=50'),
          fetch('/api/tickets?page_size=100'),
        ])
        setNetworkData(await sitesRes.json())
        setIncidents(await incRes.json())
        setTickets(await tkRes.json())
      } catch { /* ignore */ }
      setLoading(false)
    }
    fetchAll()
  }, [])

  const siteStatusCounts = { operational: 0, degraded: 0, offline: 0, maintenance: 0 }
  const ticketStatusCounts: Record<string, number> = {}
  const ticketPriorityCounts: Record<string, number> = {}
  const ticketCategoryCounts: Record<string, number> = {}
  const activeIncidents = incidents?.data.filter(i => i.status !== 'resolved') || []

  networkData?.data.forEach(s => { siteStatusCounts[s.status as keyof typeof siteStatusCounts] = (siteStatusCounts[s.status as keyof typeof siteStatusCounts] || 0) + 1 })
  tickets?.data.forEach(t => {
    ticketStatusCounts[t.status] = (ticketStatusCounts[t.status] || 0) + 1
    ticketPriorityCounts[t.priority] = (ticketPriorityCounts[t.priority] || 0) + 1
    ticketCategoryCounts[t.category] = (ticketCategoryCounts[t.category] || 0) + 1
  })

  if (loading) return <div className="p-8 text-center text-sm text-surface-400">Loading operations data...</div>

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-surface-900">Network Operations</h2>
        <p className="text-sm text-surface-500 mt-0.5">Real-time network health, incidents, and support operations.</p>
      </div>

      {/* Network Health */}
      <div className="bg-white rounded-xl border border-surface-200 p-4">
        <h3 className="text-sm font-semibold text-surface-900 mb-3">Network Health ({networkData?.pagination.total || 0} Sites)</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Object.entries(siteStatusCounts).map(([status, count]) => (
            <button key={status} onClick={() => navigate(`/cases`)} className={`p-3 rounded-lg border text-center transition-colors hover:shadow-sm ${
              status === 'operational' ? 'bg-emerald-50 border-emerald-200 hover:bg-emerald-100' :
              status === 'degraded' ? 'bg-amber-50 border-amber-200 hover:bg-amber-100' :
              status === 'offline' ? 'bg-red-50 border-red-200 hover:bg-red-100' :
              'bg-surface-50 border-surface-200 hover:bg-surface-100'
            }`}>
              <div className={`text-2xl font-bold ${
                status === 'operational' ? 'text-emerald-600' :
                status === 'degraded' ? 'text-amber-600' :
                status === 'offline' ? 'text-red-600' : 'text-surface-600'
              }`}>{count}</div>
              <div className="text-[10px] font-medium uppercase tracking-wider mt-1 capitalize">{status}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Active Incidents */}
      <div className="bg-white rounded-xl border border-surface-200 p-4">
        <h3 className="text-sm font-semibold text-surface-900 mb-3">Active Incidents ({activeIncidents.length})</h3>
        {activeIncidents.length === 0 ? (
          <p className="text-xs text-surface-400">No active incidents.</p>
        ) : (
          <div className="space-y-2">
            {activeIncidents.map(inc => (
              <button key={inc.id} onClick={() => navigate(`/cases`)} className="w-full text-left p-3 rounded-lg border border-surface-100 hover:bg-surface-50 transition-colors">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-surface-400">{inc.incident_number}</span>
                  <span className={`text-[9px] font-medium px-1.5 py-0.5 rounded ${
                    inc.severity === 'critical' ? 'bg-red-100 text-red-700' :
                    inc.severity === 'high' ? 'bg-amber-100 text-amber-700' :
                    'bg-surface-100 text-surface-600'
                  }`}>{inc.severity.toUpperCase()}</span>
                  <span className="text-[9px] text-surface-400">{inc.region}</span>
                  <span className="text-[9px] text-surface-400 ml-auto">{inc.affected_service}</span>
                </div>
                <p className="text-xs font-medium text-surface-800 mt-1">{inc.title}</p>
                <div className="flex items-center gap-3 mt-1 text-[10px] text-surface-400">
                  <span>{inc.affected_customers_estimate.toLocaleString()} affected</span>
                  <span>{inc.status}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Ticket Operations */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-surface-200 p-4">
          <h3 className="text-sm font-semibold text-surface-900 mb-3">By Status</h3>
          <div className="space-y-1.5">
            {Object.entries(ticketStatusCounts).sort((a, b) => b[1] - a[1]).map(([status, count]) => (
              <button key={status} onClick={() => navigate('/cases')} className="w-full flex items-center justify-between text-xs px-2 py-1.5 rounded hover:bg-surface-50">
                <span className="capitalize text-surface-700">{status.replace(/_/g, ' ')}</span>
                <span className="font-medium text-surface-900">{count}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="bg-white rounded-xl border border-surface-200 p-4">
          <h3 className="text-sm font-semibold text-surface-900 mb-3">By Priority</h3>
          <div className="space-y-1.5">
            {Object.entries(ticketPriorityCounts).sort((a, b) => b[1] - a[1]).map(([priority, count]) => (
              <button key={priority} onClick={() => navigate('/cases')} className="w-full flex items-center justify-between text-xs px-2 py-1.5 rounded hover:bg-surface-50">
                <span className={`capitalize font-medium ${
                  priority === 'critical' ? 'text-red-600' :
                  priority === 'high' ? 'text-amber-600' : 'text-surface-700'
                }`}>{priority}</span>
                <span className="font-medium text-surface-900">{count}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="bg-white rounded-xl border border-surface-200 p-4">
          <h3 className="text-sm font-semibold text-surface-900 mb-3">By Category</h3>
          <div className="space-y-1.5">
            {Object.entries(ticketCategoryCounts).sort((a, b) => b[1] - a[1]).map(([category, count]) => (
              <button key={category} onClick={() => navigate('/cases')} className="w-full flex items-center justify-between text-xs px-2 py-1.5 rounded hover:bg-surface-50">
                <span className="capitalize text-surface-700">{category.replace(/_/g, ' ')}</span>
                <span className="font-medium text-surface-900">{count}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function EvidencePage() {
  const navigate = useNavigate()
  const [caseId, setCaseId] = useState('')
  const [investigation, setInvestigation] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [searchParams] = useState(() => new URLSearchParams(window.location.search))
  const initialCaseId = searchParams.get('case_id') || ''

  useEffect(() => {
    if (initialCaseId && !caseId) {
      setCaseId(initialCaseId)
    }
  }, [initialCaseId])

  useEffect(() => {
    if (!caseId) { setInvestigation(null); return }
    setLoading(true)
    fetch(`/api/cases/${caseId}/investigation`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setInvestigation(d); setLoading(false) })
      .catch(() => { setInvestigation(null); setLoading(false) })
  }, [caseId])

  const inv = investigation as Record<string, unknown> | null
  const ticket = inv?.ticket as Record<string, unknown> | undefined
  const customer = inv?.customer as Record<string, unknown> | undefined
  const subscription = inv?.subscription as Record<string, unknown> | undefined
  const network = inv?.network as Record<string, unknown> | undefined
  const networkSite = network?.site as Record<string, unknown> | undefined
  const networkEvents = (network?.events || []) as Record<string, unknown>[]
  const incidents = (inv?.incidents || []) as Record<string, unknown>[]
  const investigationData = inv?.investigation as Record<string, unknown> | undefined
  const knownFacts = (investigationData?.known_facts || []) as string[]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-surface-900">Evidence & Citations</h2>
        <p className="text-sm text-surface-500 mt-0.5">View evidence traceability for any case. Every recommendation links back to account, operational, and knowledge evidence.</p>
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Enter case ID (e.g. 60)..."
          value={caseId}
          onChange={(e) => setCaseId(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && caseId && navigate(`/evidence?case_id=${caseId}`)}
          className="flex-1 px-3 py-2 text-sm border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <button
          onClick={() => caseId && navigate(`/evidence?case_id=${caseId}`)}
          className="px-4 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700 transition-colors"
        >
          Load Evidence
        </button>
      </div>

      {loading && <div className="p-8 text-center text-sm text-surface-400">Loading evidence...</div>}

      {!loading && !investigation && caseId && (
        <div className="bg-white rounded-xl border border-surface-200 p-8 text-center">
          <p className="text-sm text-surface-500">No case found with ID {caseId}.</p>
        </div>
      )}

      {!loading && !caseId && (
        <div className="bg-white rounded-xl border border-surface-200 p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-surface-100 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h4 className="text-sm font-medium text-surface-700 mb-1">Select a Case</h4>
          <p className="text-xs text-surface-500 max-w-sm mx-auto">Enter a case ID above to view the complete evidence chain: account data, operational context, network status, and knowledge citations.</p>
        </div>
      )}

      {investigation && (
        <div className="space-y-4">
          {/* Case Header */}
          {ticket && (
            <div className="bg-white rounded-xl border border-surface-200 p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-mono text-surface-400">{ticket.ticket_number as string}</span>
                <span className={`text-[9px] font-medium px-1.5 py-0.5 rounded ${
                  ticket.priority === 'critical' ? 'bg-red-100 text-red-700' :
                  ticket.priority === 'high' ? 'bg-amber-100 text-amber-700' :
                  'bg-surface-100 text-surface-600'
                }`}>{(ticket.priority as string)?.toUpperCase()}</span>
                <span className="text-[9px] font-medium px-1.5 py-0.5 rounded bg-surface-100 text-surface-600">{ticket.status as string}</span>
              </div>
              <h3 className="text-sm font-semibold text-surface-900">{ticket.subject as string}</h3>
              <p className="text-xs text-surface-500 mt-1">{ticket.description as string}</p>
              <button onClick={() => navigate(`/cases/${ticket.id}`)} className="text-xs text-brand-600 hover:text-brand-700 font-medium mt-2">Open Case →</button>
            </div>
          )}

          {/* Account Evidence */}
          {customer && (
            <div className="bg-white rounded-xl border border-surface-200 p-4">
              <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-3">Account Evidence</h3>
              <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
                <div className="text-surface-500">Customer</div><div className="font-medium text-surface-800">{customer.name as string}</div>
                <div className="text-surface-500">Customer #</div><div className="font-mono text-surface-600">{customer.customer_number as string}</div>
                <div className="text-surface-500">Phone</div><div className="text-surface-700">{customer.phone as string}</div>
                <div className="text-surface-500">Segment</div><div className="text-surface-700 capitalize">{customer.segment as string}</div>
                <div className="text-surface-500">Status</div><div className={`font-medium ${customer.status === 'active' ? 'text-emerald-600' : 'text-amber-600'}`}>{customer.status as string}</div>
              </div>
            </div>
          )}

          {/* Subscription Evidence */}
          {subscription && (
            <div className="bg-white rounded-xl border border-surface-200 p-4">
              <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-3">Subscription Evidence</h3>
              <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
                <div className="text-surface-500">Plan</div><div className="font-medium text-surface-800">{subscription.plan_name as string}</div>
                <div className="text-surface-500">Service</div><div className="text-surface-700">{subscription.service_type as string}</div>
                <div className="text-surface-500">Price</div><div className="text-surface-700">₹{subscription.monthly_price as number}/mo</div>
                <div className="text-surface-500">Data Limit</div><div className="text-surface-700">{subscription.data_limit_gb as number}GB</div>
                <div className="text-surface-500">Status</div><div className={`font-medium ${(subscription.status as string) === 'active' ? 'text-emerald-600' : 'text-amber-600'}`}>{subscription.status as string}</div>
              </div>
            </div>
          )}

          {/* Network Evidence */}
          <div className="bg-white rounded-xl border border-surface-200 p-4">
            <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-3">Network Evidence</h3>
            {networkSite ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
                  <div className="text-surface-500">Site</div><div className="font-medium text-surface-800">{networkSite.site_code as string}</div>
                  <div className="text-surface-500">Technology</div><div className="text-surface-700">{networkSite.technology as string}</div>
                  <div className="text-surface-500">Region</div><div className="text-surface-700">{networkSite.region as string}</div>
                  <div className="text-surface-500">City</div><div className="text-surface-700">{networkSite.city as string}</div>
                  <div className="text-surface-500">Status</div><div className={`font-medium ${(networkSite.status as string) === 'operational' ? 'text-emerald-600' : (networkSite.status as string) === 'degraded' ? 'text-amber-600' : 'text-red-600'}`}>{networkSite.status as string}</div>
                  <div className="text-surface-500">Capacity</div><div className="text-surface-700">{networkSite.capacity_percent as number}%</div>
                </div>
                {networkEvents.length > 0 && (
                  <div className="pt-2 border-t border-surface-100">
                    <p className="text-[10px] font-medium text-surface-500 uppercase mb-1">Recent Events</p>
                    {networkEvents.slice(0, 5).map((ev, i) => (
                      <div key={i} className="text-[10px] py-1">
                        <span className={`font-medium ${(ev.severity as string) === 'critical' ? 'text-red-600' : (ev.severity as string) === 'high' ? 'text-amber-600' : 'text-surface-500'}`}>{(ev.severity as string)?.toUpperCase()}</span>
                        <span className="text-surface-700 ml-1">{ev.title as string}</span>
                        <span className="text-surface-400 ml-1">({ev.status as string})</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-surface-400">No network site data available.</p>
            )}
          </div>

          {/* Incident Evidence */}
          {incidents.length > 0 && (
            <div className="bg-white rounded-xl border border-surface-200 p-4">
              <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-3">Incident Evidence</h3>
              <div className="space-y-2">
                {incidents.map((inc, i) => (
                  <div key={i} className="p-2 rounded-lg bg-surface-50 border border-surface-100">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-surface-400">{inc.incident_number as string}</span>
                      <span className={`text-[9px] font-medium px-1.5 py-0.5 rounded ${
                        inc.severity === 'critical' ? 'bg-red-100 text-red-700' : inc.severity === 'high' ? 'bg-amber-100 text-amber-700' : 'bg-surface-100 text-surface-600'
                      }`}>{(inc.severity as string)?.toUpperCase()}</span>
                    </div>
                    <p className="text-xs text-surface-700 mt-0.5">{inc.title as string}</p>
                    <p className="text-[10px] text-surface-400">{inc.region as string} · {inc.affected_service as string} · {inc.status as string}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Known Facts */}
          {knownFacts.length > 0 && (
            <div className="bg-white rounded-xl border border-surface-200 p-4">
              <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-3">Confirmed Facts</h3>
              <ul className="space-y-1">
                {knownFacts.map((fact, i) => (
                  <li key={i} className="text-xs text-surface-700 flex items-start gap-2">
                    <span className="text-emerald-500 mt-0.5">✓</span> {fact}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Traceability */}
          <div className="bg-surface-50 rounded-xl border border-surface-200 p-4">
            <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2">Evidence Traceability</h3>
            <p className="text-xs text-surface-600">
              Every AI recommendation traces back to: <span className="font-medium">Account Evidence</span> (customer/plan/subscription) → <span className="font-medium">Operational Evidence</span> (network/site/incidents) → <span className="font-medium">Knowledge Evidence</span> (retrieved articles with citations). Click evidence items to view source details.
            </p>
          </div>
        </div>
      )}
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
              <Route path="/console" element={<AgentConsolePage />} />
              <Route path="/cases" element={<CasesPage />} />
              <Route path="/cases/:ticketId" element={<CaseDetailPage />} />
              <Route path="/customers" element={<CustomersPage />} />
              <Route path="/operations" element={<OperationsPage />} />
              <Route path="/knowledge" element={<KnowledgePage />} />
              <Route path="/knowledge/:documentId" element={<KnowledgeDetailPage />} />
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
