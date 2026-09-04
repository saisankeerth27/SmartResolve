import type { RegionalImpact as RegionalImpactType } from '../../types'
import { EmptyState } from '../common/States'

export function RegionalImpact({ regions }: { regions: RegionalImpactType[] }) {
  if (regions.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-surface-200 p-5">
        <h3 className="text-sm font-semibold text-surface-900 mb-4">Regional Impact</h3>
        <EmptyState message="No regional data available" />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <h3 className="text-sm font-semibold text-surface-900 mb-4">Regional Impact</h3>
      <div className="space-y-3">
        {regions.map((r) => {
          const impactLevel = r.affected_customers > 10000 ? 'critical' :
                            r.affected_customers > 0 ? 'elevated' : 'normal'
          return (
            <div
              key={r.region}
              className={`border rounded-lg p-3 transition-colors ${
                impactLevel === 'critical' ? 'border-red-200 bg-red-50/30' :
                impactLevel === 'elevated' ? 'border-amber-200 bg-amber-50/30' :
                'border-surface-100 hover:bg-surface-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-surface-800">{r.region}</span>
                {r.affected_customers > 0 && (
                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                    impactLevel === 'critical' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                  }`}>
                    {r.affected_customers.toLocaleString()} affected
                  </span>
                )}
              </div>
              <div className="flex items-center gap-4 mt-2 text-xs text-surface-500">
                <span>{r.open_tickets} tickets</span>
                <span>{r.active_incidents} incidents</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
