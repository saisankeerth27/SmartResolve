import type { DashboardMetrics } from '../../types'

type KpiData = {
  label: string
  value: string
  detail: string
  icon: string
  color: string
}

export function KpiCards({ metrics }: { metrics: DashboardMetrics }) {
  const kpis: KpiData[] = [
    {
      label: 'Open Tickets',
      value: String(metrics.open_tickets),
      detail: `${metrics.high_priority_tickets} high priority`,
      icon: 'M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
      color: metrics.high_priority_tickets > 5 ? 'bg-red-50 border-red-200' : 'bg-white border-surface-200',
    },
    {
      label: 'High Priority',
      value: String(metrics.high_priority_tickets),
      detail: `${metrics.open_tickets} total open`,
      icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
      color: metrics.high_priority_tickets > 10 ? 'bg-orange-50 border-orange-200' : 'bg-white border-surface-200',
    },
    {
      label: 'Active Incidents',
      value: String(metrics.active_incidents),
      detail: `${metrics.affected_customers.toLocaleString()} customers affected`,
      icon: 'M13 10V3L4 14h7v7l9-11h-7z',
      color: metrics.active_incidents > 0 ? 'bg-amber-50 border-amber-200' : 'bg-white border-surface-200',
    },
    {
      label: 'Network Sites',
      value: String(metrics.network_sites),
      detail: `${metrics.total_customers.toLocaleString()} total customers`,
      icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
      color: 'bg-white border-surface-200',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi) => (
        <div key={kpi.label} className={`rounded-xl border p-4 transition-colors ${kpi.color}`}>
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">{kpi.label}</p>
              <p className="text-2xl font-bold text-surface-900 mt-1">{kpi.value}</p>
            </div>
            <div className="w-9 h-9 rounded-lg bg-surface-100 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-surface-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={kpi.icon} />
              </svg>
            </div>
          </div>
          <p className="text-xs text-surface-500 mt-2">{kpi.detail}</p>
        </div>
      ))}
    </div>
  )
}
