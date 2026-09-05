import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchApi } from '../services/api'
import { LoadingState, ErrorState, SkeletonCard } from '../components/common/States'

interface DashboardData {
  metrics: {
    open_tickets: number
    high_priority_tickets: number
    active_incidents: number
    network_sites: number
    affected_customers: number
    total_customers: number
  }
  ticket_breakdown: {
    by_status: Record<string, number>
    by_priority: Record<string, number>
    by_category: Record<string, number>
  }
  recent_activity: Array<{
    type: string
    timestamp: string
    description: string
    related_id: string
    event_type: string
  }>
}

const statusColors: Record<string, string> = {
  open: 'bg-blue-100 text-blue-800',
  analyzing: 'bg-indigo-100 text-indigo-800',
  pending_agent_approval: 'bg-emerald-100 text-emerald-800',
  needs_information: 'bg-amber-100 text-amber-800',
  escalation_requested: 'bg-orange-100 text-orange-800',
  human_review: 'bg-red-100 text-red-800',
  approved: 'bg-green-100 text-green-800',
  resolved: 'bg-green-100 text-green-800',
  dismissed: 'bg-surface-100 text-surface-600',
  in_progress: 'bg-yellow-100 text-yellow-800',
  pending_customer: 'bg-orange-100 text-orange-800',
  escalated: 'bg-red-100 text-red-800',
}

const statusLabels: Record<string, string> = {
  open: 'Open',
  analyzing: 'Analyzing',
  pending_agent_approval: 'Pending Approval',
  needs_information: 'Needs Info',
  escalation_requested: 'Escalation Requested',
  human_review: 'Human Review',
  approved: 'Approved',
  resolved: 'Resolved',
  dismissed: 'Dismissed',
  in_progress: 'In Progress',
  pending_customer: 'Pending Customer',
  escalated: 'Escalated',
}

export function OverviewPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchApi<DashboardData>('/api/dashboard/overview')
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
        <LoadingState message="Loading overview..." />
      </div>
    )
  }

  if (error && !data) return <ErrorState message={error} onRetry={fetchData} />
  if (!data) return null

  const statusBreakdown = data.ticket_breakdown.by_status
  const totalTickets = Object.values(statusBreakdown).reduce((a, b) => a + b, 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-surface-900">Support Overview</h2>
        <button onClick={fetchData} disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-surface-600 bg-white border border-surface-200 rounded-lg hover:bg-surface-50 disabled:opacity-50 transition-colors">
          <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Open Tickets', value: (statusBreakdown.open || 0) + (statusBreakdown.analyzing || 0), color: 'text-blue-600', bg: 'bg-blue-50', icon: '🔵', onClick: () => navigate('/console') },
          { label: 'Pending Approval', value: statusBreakdown.pending_agent_approval || 0, color: 'text-emerald-600', bg: 'bg-emerald-50', icon: '🟢', onClick: () => navigate('/console') },
          { label: 'Needs Information', value: statusBreakdown.needs_information || 0, color: 'text-amber-600', bg: 'bg-amber-50', icon: '🟡', onClick: () => navigate('/console') },
          { label: 'Human Review', value: (statusBreakdown.human_review || 0) + (statusBreakdown.escalation_requested || 0), color: 'text-red-600', bg: 'bg-red-50', icon: '🔴', onClick: () => navigate('/console') },
        ].map(kpi => (
          <button key={kpi.label} onClick={kpi.onClick}
            className={`${kpi.bg} rounded-xl p-4 text-left hover:shadow-md transition-shadow`}>
            <div className="text-sm font-medium text-surface-500">{kpi.label}</div>
            <div className={`text-3xl font-bold ${kpi.color} mt-1`}>{kpi.value}</div>
            <div className="text-xs text-surface-400 mt-1">{totalTickets} total tickets</div>
          </button>
        ))}
      </div>

      {/* Ticket Status Breakdown */}
      <div className="bg-white rounded-xl border border-surface-200 p-5">
        <h3 className="text-sm font-semibold text-surface-900 mb-3">Ticket Status</h3>
        <div className="space-y-2">
          {Object.entries(statusBreakdown).sort((a, b) => b[1] - a[1]).map(([status, count]) => (
            <div key={status} className="flex items-center gap-3">
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusColors[status] || 'bg-surface-100 text-surface-600'}`}>
                {statusLabels[status] || status}
              </span>
              <div className="flex-1 h-2 bg-surface-100 rounded-full overflow-hidden">
                <div className="h-full bg-brand-500 rounded-full" style={{ width: `${totalTickets > 0 ? (count / totalTickets) * 100 : 0}%` }} />
              </div>
              <span className="text-sm font-medium text-surface-700 w-8 text-right">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="bg-white rounded-xl border border-surface-200 p-5">
        <h3 className="text-sm font-semibold text-surface-900 mb-3">By Category</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Object.entries(data.ticket_breakdown.by_category).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
            <div key={cat} className="text-center p-3 bg-surface-50 rounded-lg">
              <div className="text-lg font-bold text-surface-900">{count}</div>
              <div className="text-xs text-surface-500 capitalize">{cat}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl border border-surface-200 p-5">
        <h3 className="text-sm font-semibold text-surface-900 mb-3">Recent Activity</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {data.recent_activity.slice(0, 10).map((act, i) => (
            <div key={i} className="flex items-start gap-3 py-2 border-b border-surface-50 last:border-0">
              <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                act.event_type === 'resolved' ? 'bg-green-400' :
                act.event_type === 'customer_reply' ? 'bg-blue-400' :
                act.event_type === 'escalation' ? 'bg-red-400' : 'bg-surface-300'
              }`} />
              <div className="min-w-0">
                <div className="text-sm text-surface-700 truncate">{act.description}</div>
                <div className="text-xs text-surface-400 mt-0.5">
                  {act.related_id} · {new Date(act.timestamp).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
