import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import logo from './assets/logo.png'
import { OverviewPage } from './pages/Overview'
import CustomerChatPage from './pages/CustomerChat'
import AgentConsolePage from './pages/AgentConsole'
import { CasesPage } from './pages/Cases'
import { CaseDetailPage } from './pages/CaseDetail'
import { KnowledgePage } from './pages/Knowledge'
import { KnowledgeDetailPage } from './pages/KnowledgeDetail'

const NAV = [
  { to: '/', label: 'Overview', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { to: '/chat', label: 'New Conversation', icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' },
  { to: '/console', label: 'Agent Console', icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
  { to: '/cases', label: 'Cases', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
  { to: '/knowledge', label: 'Knowledge', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
]

function Sidebar() {
  const location = useLocation()
  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  return (
    <div className="w-56 bg-[#0f172a] text-white flex flex-col shrink-0 h-full">
      <div className="px-4 py-2 border-b border-white/10">
        <div className="flex items-center justify-center">
          <img src={logo} alt="SmartResolve" className="h-20 w-full object-contain" />
        </div>
      </div>
      <nav className="flex-1 py-3 space-y-0.5 px-2">
        {NAV.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              isActive(item.to)
                ? 'bg-blue-600/20 text-blue-300 font-medium'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
            </svg>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="px-4 py-3 border-t border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="text-[11px] text-slate-400">System Operational</span>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-surface-50 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto p-4 lg:p-5">
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/chat" element={<CustomerChatPage />} />
            <Route path="/console" element={<AgentConsolePage />} />
            <Route path="/cases" element={<CasesPage />} />
            <Route path="/cases/:ticketId" element={<CaseDetailPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route path="/knowledge/:id" element={<KnowledgeDetailPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
