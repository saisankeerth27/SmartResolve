import { useState } from 'react'

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
              Foundation v0.1
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

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Open Cases" value="0" trend="neutral" />
        <StatCard label="Customers" value="0" trend="neutral" />
        <StatCard label="Resolved Today" value="0" trend="neutral" />
        <StatCard label="Escalations" value="0" trend="neutral" />
      </div>

      <div className="bg-white rounded-xl border border-surface-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-brand-50 flex items-center justify-center">
            <svg className="w-5 h-5 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-surface-900">SmartResolve Engine</h3>
            <p className="text-xs text-surface-500">AI-powered telecom resolution assistant</p>
          </div>
        </div>

        <div className="bg-surface-50 rounded-lg border border-surface-200 p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-surface-100 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <h4 className="text-sm font-medium text-surface-700 mb-1">Workspace Ready</h4>
          <p className="text-xs text-surface-500 max-w-sm mx-auto">
            Foundation initialized. Customer data, case management, AI reasoning, and resolution engine will be available in upcoming releases.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <InfoCard
          title="System Status"
          items={[
            { label: 'API', value: 'Healthy', status: 'ok' },
            { label: 'Database', value: 'Connected', status: 'ok' },
            { label: 'Gemini API', value: 'Not Configured', status: 'warn' },
            { label: 'RAG Index', value: 'Pending', status: 'neutral' },
          ]}
        />
        <InfoCard
          title="Upcoming Features"
          items={[
            { label: 'Customer Lookup', value: 'Planned', status: 'neutral' },
            { label: 'Case Resolution', value: 'Planned', status: 'neutral' },
            { label: 'Knowledge RAG', value: 'Planned', status: 'neutral' },
            { label: 'Escalation Rules', value: 'Planned', status: 'neutral' },
          ]}
        />
      </div>
    </div>
  )
}

function StatCard({ label, value, trend }: { label: string; value: string; trend: 'up' | 'down' | 'neutral' }) {
  return (
    <div className="bg-white rounded-xl border border-surface-200 p-4">
      <div className="text-xs font-medium text-surface-500 mb-1">{label}</div>
      <div className="text-2xl font-bold text-surface-900">{value}</div>
      <div className="flex items-center gap-1 mt-2 text-xs">
        {trend === 'up' && <span className="text-emerald-600">+0%</span>}
        {trend === 'down' && <span className="text-red-500">-0%</span>}
        {trend === 'neutral' && <span className="text-surface-400">Baseline</span>}
      </div>
    </div>
  )
}

function InfoCard({ title, items }: { title: string; items: { label: string; value: string; status: 'ok' | 'warn' | 'error' | 'neutral' }[] }) {
  const statusColors = {
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

export default App
