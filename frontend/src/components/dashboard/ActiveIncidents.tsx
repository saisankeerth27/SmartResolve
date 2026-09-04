import type { ActiveIncidentSummary } from '../../types'
import { SeverityIndicator, StatusBadge } from '../common/Badges'
import { EmptyState } from '../common/States'

function formatTimeAgo(dateStr: string) {
  try {
    const now = new Date()
    const then = new Date(dateStr)
    const diffMs = now.getTime() - then.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHrs = Math.floor(diffMins / 60)
    if (diffHrs < 24) return `${diffHrs}h ago`
    const diffDays = Math.floor(diffHrs / 24)
    return `${diffDays}d ago`
  } catch {
    return dateStr
  }
}

export function ActiveIncidentsPanel({ incidents }: { incidents: ActiveIncidentSummary[] }) {
  if (incidents.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-surface-200 p-5">
        <h3 className="text-sm font-semibold text-surface-900 mb-4">Active Incidents</h3>
        <EmptyState message="No active incidents" />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-surface-900">Active Incidents</h3>
        <span className="text-xs text-surface-500">{incidents.length} active</span>
      </div>
      <div className="space-y-3">
        {incidents.map((inc) => (
          <div key={inc.id} className="border border-surface-100 rounded-lg p-3 hover:bg-surface-50 transition-colors">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-mono text-surface-400">{inc.incident_number}</span>
                  <SeverityIndicator severity={inc.severity} />
                </div>
                <p className="text-sm font-medium text-surface-800 mt-1 line-clamp-1">{inc.title}</p>
                <p className="text-xs text-surface-500 mt-1 line-clamp-2">{inc.description}</p>
              </div>
              <StatusBadge status={inc.status} />
            </div>
            <div className="flex items-center gap-4 mt-2 text-[11px] text-surface-500">
              <span>{inc.region}</span>
              <span>{inc.affected_service}</span>
              <span>{inc.affected_customers_estimate.toLocaleString()} affected</span>
              <span>{formatTimeAgo(inc.started_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
