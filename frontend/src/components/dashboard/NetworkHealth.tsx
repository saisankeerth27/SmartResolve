import type { NetworkHealth as NetworkHealthType } from '../../types'

function HealthBar({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? (count / total) * 100 : 0
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-surface-600 w-24 shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-surface-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-surface-700 w-8 text-right">{count}</span>
    </div>
  )
}

export function NetworkHealthPanel({ health }: { health: NetworkHealthType }) {
  const statusLabel = health.status === 'healthy' ? 'Healthy' : health.status === 'degraded' ? 'Degraded' : 'Critical'

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-surface-900">Network Health</h3>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${
            health.status === 'healthy' ? 'bg-emerald-400' :
            health.status === 'degraded' ? 'bg-amber-400' : 'bg-red-400'
          }`} />
          <span className="text-xs font-medium text-surface-600">{statusLabel}</span>
        </div>
      </div>

      <div className="space-y-3">
        <HealthBar label="Operational" count={health.operational} total={health.total} color="bg-emerald-400" />
        <HealthBar label="Degraded" count={health.degraded} total={health.total} color="bg-amber-400" />
        <HealthBar label="Maintenance" count={health.maintenance} total={health.total} color="bg-blue-400" />
        <HealthBar label="Offline" count={health.offline} total={health.total} color="bg-red-400" />
      </div>

      <div className="mt-4 pt-3 border-t border-surface-100">
        <div className="flex items-center justify-between text-xs">
          <span className="text-surface-500">Total Sites</span>
          <span className="font-medium text-surface-700">{health.total}</span>
        </div>
        <div className="flex items-center justify-between text-xs mt-1">
          <span className="text-surface-500">Active Events</span>
          <span className={`font-medium ${health.active_events > 0 ? 'text-amber-600' : 'text-surface-700'}`}>
            {health.active_events}
          </span>
        </div>
      </div>
    </div>
  )
}
