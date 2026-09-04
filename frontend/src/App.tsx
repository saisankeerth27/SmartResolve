import { useEffect, useState } from 'react'

type NavItem = {
  id: string
  label: string
  icon: string
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2' },
  { id: 'cases', label: 'Cases', icon: 'M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
  { id: 'customers', label: 'Customers', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
  { id: 'operations', label: 'Operations', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
  { id: 'knowledge', label: 'Knowledge', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
  { id: 'evidence', label: 'Evidence', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
]

type DashboardStats = {
  total_customers: number
  open_tickets: number
  active_incidents: number
  total_network_sites: number
  active_network_events: number
  ticket_status_counts: Record<string, number>
  incident_status_counts: Record<string, number>
  site_status_counts: Record<string, number>
}

type Customer = {
  id: number
  customer_number: string
  name: string
  email: string
  phone: string
  segment: string
  status: string
  created_at: string
}

type Ticket = {
  id: number
  ticket_number: string
  subject: string
  category: string
  priority: string
  status: string
  customer_name: string
  created_at: string
}

type Incident = {
  id: number
  incident_number: string
  title: string
  severity: string
  status: string
  region: string
  affected_customers_estimate: number
  started_at: string
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

function useApi<T>(url: string) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((json) => {
        if (!cancelled) {
          setData(json)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setLoading(false)
        }
      })
    return () => { cancelled = true }
  }, [url])

  return { data, loading, error }
}

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
            <div className="text-[11px] text-surface-400 mt-0.5">Operations Console</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveNav(item.id)
                setSidebarOpen(false)
              }}
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
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            System Operational
          </div>
        </div>
      </aside>

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
              <h1 className="text-sm font-semibold text-surface-900 leading-none">Telecom Operations</h1>
              <p className="text-xs text-surface-500 mt-0.5">Resolution Workspace</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs text-surface-500 bg-surface-50 rounded-lg px-3 py-1.5 border border-surface-200">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Data Layer v0.2
            </div>
            <div className="w-8 h-8 rounded-full bg-surface-200 flex items-center justify-center text-surface-600 text-xs font-medium">
              OP
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <ContentArea activeNav={activeNav} />
        </main>
      </div>
    </div>
  )
}

function ContentArea({ activeNav }: { activeNav: string }) {
  const titles: Record<string, string> = {
    overview: 'Operations Overview',
    cases: 'Active Cases',
    customers: 'Customer Directory',
    operations: 'Network Operations',
    knowledge: 'Knowledge Base',
    evidence: 'Evidence & Citations',
  }

  const descriptions: Record<string, string> = {
    overview: 'Real-time view of telecom operations status, active cases, and system health.',
    cases: 'Track and manage open support and operational cases.',
    customers: 'Access customer account information and history.',
    operations: 'Monitor network operational records and status.',
    knowledge: 'Browse telecom policies, procedures, and operational documents.',
    evidence: 'Review AI-generated evidence and citations for resolutions.',
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-surface-900">{titles[activeNav]}</h2>
        <p className="text-sm text-surface-500 mt-1">{descriptions[activeNav]}</p>
      </div>

      {activeNav === 'overview' && <OverviewPage />}
      {activeNav === 'cases' && <CasesPage />}
      {activeNav === 'customers' && <CustomersPage />}
      {activeNav === 'operations' && <OperationsPage />}
      {activeNav === 'knowledge' && <KnowledgePage />}
      {activeNav === 'evidence' && <EvidencePage />}
    </div>
  )
}

function OverviewPage() {
  const { data: stats, loading, error } = useApi<DashboardStats>('/api/dashboard')

  if (loading) return <LoadingState />
  if (error || !stats) return <ErrorState message={error || 'Failed to load dashboard'} />

  const openTicketCount = Object.entries(stats.ticket_status_counts)
    .filter(([k]) => k !== 'resolved')
    .reduce((sum, [, v]) => sum + v, 0)

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Customers" value={String(stats.total_customers)} trend="neutral" />
        <StatCard label="Open Tickets" value={String(openTicketCount)} trend="neutral" />
        <StatCard label="Active Incidents" value={String(stats.active_incidents)} trend={stats.active_incidents > 0 ? 'down' : 'neutral'} />
        <StatCard label="Network Sites" value={String(stats.total_network_sites)} trend="neutral" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <InfoCard
          title="Ticket Status"
          items={Object.entries(stats.ticket_status_counts).map(([k, v]) => ({
            label: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
            value: String(v),
            status: k === 'resolved' ? 'ok' : k === 'escalated' ? 'error' : k === 'open' ? 'warn' : 'neutral' as const,
          }))}
        />
        <InfoCard
          title="Incident Status"
          items={Object.entries(stats.incident_status_counts).map(([k, v]) => ({
            label: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
            value: String(v),
            status: k === 'resolved' ? 'ok' : k === 'investigating' ? 'error' : 'neutral' as const,
          }))}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <InfoCard
          title="Network Site Health"
          items={Object.entries(stats.site_status_counts).map(([k, v]) => ({
            label: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
            value: String(v),
            status: k === 'operational' ? 'ok' : k === 'degraded' ? 'warn' : k === 'offline' ? 'error' : 'neutral' as const,
          }))}
        />
        <InfoCard
          title="System Status"
          items={[
            { label: 'API', value: 'Healthy', status: 'ok' as const },
            { label: 'Database', value: 'Connected', status: 'ok' as const },
            { label: 'Active Network Events', value: String(stats.active_network_events), status: stats.active_network_events > 10 ? 'warn' : 'ok' as const },
            { label: 'Gemini API', value: 'Not Configured', status: 'warn' as const },
          ]}
        />
      </div>
    </div>
  )
}

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
        <StatCard label="Open Cases" value={String(data?.pagination.total || 0)} trend="neutral" />
        <StatCard label="Escalated" value={String(escalated?.pagination.total || 0)} trend="down" />
        <StatCard label="Pending Resolution" value="--" trend="neutral" />
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

function OperationsPage() {
  const { data: sites, loading: sitesLoading } = useApi<{ data: NetworkSite[]; pagination: { total: number } }>(
    '/api/network/sites?page_size=20'
  )
  const { data: incidents } = useApi<{ data: Incident[]; pagination: { total: number } }>(
    '/api/incidents/active?page_size=5'
  )

  if (sitesLoading) return <LoadingState />

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Total Sites" value={String(sites?.pagination.total || 0)} trend="neutral" />
        <StatCard label="Active Incidents" value={String(incidents?.pagination.total || 0)} trend={incidents && incidents.pagination.total > 0 ? 'down' : 'neutral'} />
        <StatCard label="Degraded Sites" value={String(sites?.data.filter(s => s.status === 'degraded').length || 0)} trend="neutral" />
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

// ── Shared Components ────────────────────────────────────

function StatCard({ label, value, trend }: { label: string; value: string; trend: 'up' | 'down' | 'neutral' }) {
  return (
    <div className="bg-white rounded-xl border border-surface-200 p-4">
      <div className="text-xs font-medium text-surface-500 mb-1">{label}</div>
      <div className="text-2xl font-bold text-surface-900">{value}</div>
      <div className="flex items-center gap-1 mt-2 text-xs">
        {trend === 'up' && <span className="text-emerald-600">+0%</span>}
        {trend === 'down' && <span className="text-red-500">Attention</span>}
        {trend === 'neutral' && <span className="text-surface-400">Baseline</span>}
      </div>
    </div>
  )
}

function InfoCard({ title, items }: { title: string; items: { label: string; value: string; status: 'ok' | 'warn' | 'error' | 'neutral' }[] }) {
  const statusColors: Record<string, string> = {
    ok: 'bg-emerald-400',
    warn: 'bg-amber-400',
    error: 'bg-red-400',
    neutral: 'bg-surface-300',
  }

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <h3 className="text-sm font-semibold text-surface-900 mb-3">{title}</h3>
      <div className="space-y-2.5">
        {items.map((item) => (
          <div key={item.label} className="flex items-center justify-between text-sm">
            <span className="text-surface-500">{item.label}</span>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${statusColors[item.status]}`} />
              <span className="text-surface-700 font-medium">{item.value}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    open: 'bg-amber-50 text-amber-700 border-amber-200',
    in_progress: 'bg-blue-50 text-blue-700 border-blue-200',
    resolved: 'bg-surface-50 text-surface-600 border-surface-200',
    escalated: 'bg-red-50 text-red-700 border-red-200',
    suspended: 'bg-amber-50 text-amber-700 border-amber-200',
    closed: 'bg-surface-50 text-surface-500 border-surface-200',
    operational: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    degraded: 'bg-amber-50 text-amber-700 border-amber-200',
    maintenance: 'bg-blue-50 text-blue-700 border-blue-200',
    offline: 'bg-red-50 text-red-700 border-red-200',
    investigating: 'bg-red-50 text-red-700 border-red-200',
    identified: 'bg-amber-50 text-amber-700 border-amber-200',
    monitoring: 'bg-blue-50 text-blue-700 border-blue-200',
    pending_customer: 'bg-amber-50 text-amber-700 border-amber-200',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded border ${colors[status] || 'bg-surface-50 text-surface-600 border-surface-200'}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    critical: 'bg-red-50 text-red-700 border-red-200',
    high: 'bg-orange-50 text-orange-700 border-orange-200',
    medium: 'bg-amber-50 text-amber-700 border-amber-200',
    low: 'bg-surface-50 text-surface-600 border-surface-200',
  }
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded border ${colors[priority] || 'bg-surface-50 text-surface-600 border-surface-200'}`}>
      {priority}
    </span>
  )
}

function SegmentBadge({ segment }: { segment: string }) {
  const labels: Record<string, string> = {
    consumer: 'Consumer',
    small_business: 'Small Business',
    enterprise: 'Enterprise',
  }
  const colors: Record<string, string> = {
    consumer: 'bg-surface-100 text-surface-600',
    small_business: 'bg-blue-50 text-blue-700',
    enterprise: 'bg-purple-50 text-purple-700',
  }
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded ${colors[segment] || 'bg-surface-100 text-surface-600'}`}>
      {labels[segment] || segment}
    </span>
  )
}

function TechBadge({ technology }: { technology: string }) {
  const colors: Record<string, string> = {
    '5G': 'bg-violet-50 text-violet-700 border-violet-200',
    '4G': 'bg-blue-50 text-blue-700 border-blue-200',
    'LTE': 'bg-cyan-50 text-cyan-700 border-cyan-200',
    'Fiber': 'bg-emerald-50 text-emerald-700 border-emerald-200',
  }
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded border ${colors[technology] || 'bg-surface-50 text-surface-600 border-surface-200'}`}>
      {technology}
    </span>
  )
}

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

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="flex items-center gap-3 text-surface-500">
        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span className="text-sm">Loading...</span>
      </div>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
      <p className="text-sm text-red-700">Failed to load data: {message}</p>
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="py-8 text-center text-sm text-surface-400">{message}</div>
  )
}

export default App
