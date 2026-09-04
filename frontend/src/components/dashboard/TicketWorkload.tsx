import type { TicketBreakdown } from '../../types'

const STATUS_COLORS: Record<string, string> = {
  open: 'bg-amber-400',
  in_progress: 'bg-blue-400',
  pending_customer: 'bg-orange-400',
  resolved: 'bg-emerald-400',
  escalated: 'bg-red-400',
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-amber-400',
  low: 'bg-surface-300',
}

const CATEGORY_COLORS: Record<string, string> = {
  network: 'bg-violet-400',
  connectivity: 'bg-blue-400',
  billing: 'bg-emerald-400',
  voice: 'bg-cyan-400',
  sms: 'bg-pink-400',
  roaming: 'bg-orange-400',
  device: 'bg-amber-400',
  account: 'bg-surface-400',
}

function formatLabel(key: string) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function BreakdownSection({
  title,
  data,
  colorMap,
}: {
  title: string
  data: Record<string, number>
  colorMap: Record<string, string>
}) {
  const entries = Object.entries(data).sort(([, a], [, b]) => b - a)
  const total = entries.reduce((sum, [, v]) => sum + v, 0)

  return (
    <div>
      <h4 className="text-xs font-medium text-surface-500 uppercase tracking-wide mb-3">{title}</h4>
      <div className="space-y-2">
        {entries.map(([key, value]) => {
          const pct = total > 0 ? (value / total) * 100 : 0
          return (
            <div key={key} className="flex items-center gap-2">
              <span className="text-[11px] text-surface-600 w-28 shrink-0 truncate">{formatLabel(key)}</span>
              <div className="flex-1 h-1.5 bg-surface-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${colorMap[key] || 'bg-surface-300'}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-[11px] font-medium text-surface-700 w-6 text-right">{value}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function TicketWorkload({ breakdown }: { breakdown: TicketBreakdown }) {
  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <h3 className="text-sm font-semibold text-surface-900 mb-4">Ticket Workload</h3>
      <div className="space-y-5">
        <BreakdownSection title="By Status" data={breakdown.by_status} colorMap={STATUS_COLORS} />
        <BreakdownSection title="By Priority" data={breakdown.by_priority} colorMap={PRIORITY_COLORS} />
        <BreakdownSection title="By Category" data={breakdown.by_category} colorMap={CATEGORY_COLORS} />
      </div>
    </div>
  )
}
