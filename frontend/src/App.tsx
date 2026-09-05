import { useState } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { OverviewPage } from './pages/Overview'
import { CasesPage } from './pages/Cases'
import { CaseDetailPage } from './pages/CaseDetail'
import { KnowledgePage } from './pages/Knowledge'
import { KnowledgeDetailPage } from './pages/KnowledgeDetail'
import AgentConsolePage from './pages/AgentConsole'
import CustomerChatPage from './pages/CustomerChat'

type NavItem = {
  id: string
  label: string
  icon: string
  path: string
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', path: '/', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2' },
  { id: 'chat', label: 'New Conversation', path: '/chat', icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' },
  { id: 'console', label: 'Agent Console', path: '/console', icon: 'M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' },
  { id: 'cases', label: 'Cases', path: '/cases', icon: 'M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
  { id: 'knowledge', label: 'Knowledge', path: '/knowledge', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
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
    if (path === '/') return { title: 'Overview', desc: 'Support workload and key metrics' }
    if (path === '/chat') return { title: 'Customer Chat', desc: 'Start or continue a customer conversation' }
    if (path === '/console') return { title: 'Agent Console', desc: 'Analyze cases with Mode A/B/C deterministic classification' }
    if (path.startsWith('/cases/')) return { title: 'Case Investigation', desc: 'Investigate customer issue using operational and service data' }
    if (path === '/cases') return { title: 'Cases', desc: 'Investigate customer issues using operational and service data' }
    if (path.startsWith('/knowledge')) return { title: 'Knowledge Base', desc: 'Telecom policies and procedures' }
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
              <Route path="/chat" element={<CustomerChatPage />} />
              <Route path="/console" element={<AgentConsolePage />} />
              <Route path="/cases" element={<CasesPage />} />
              <Route path="/cases/:ticketId" element={<CaseDetailPage />} />
              <Route path="/knowledge" element={<KnowledgePage />} />
              <Route path="/knowledge/:documentId" element={<KnowledgeDetailPage />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  )
}
