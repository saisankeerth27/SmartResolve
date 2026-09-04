export function StatusBadge({ status }: { status: string }) {
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
    healthy: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded border ${colors[status] || 'bg-surface-50 text-surface-600 border-surface-200'}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

export function PriorityBadge({ priority }: { priority: string }) {
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

export function SeverityIndicator({ severity }: { severity: string }) {
  const config: Record<string, { color: string; icon: string }> = {
    critical: { color: 'text-red-600', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z' },
    high: { color: 'text-orange-600', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z' },
    medium: { color: 'text-amber-600', icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
    low: { color: 'text-surface-500', icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
  }
  const { color, icon } = config[severity] || config.low
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${color}`}>
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
      </svg>
      {severity}
    </span>
  )
}

export function SegmentBadge({ segment }: { segment: string }) {
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

export function TechBadge({ technology }: { technology: string }) {
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
