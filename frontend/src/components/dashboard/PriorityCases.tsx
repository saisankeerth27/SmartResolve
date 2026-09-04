import type { PriorityCase } from '../../types'
import { PriorityBadge } from '../common/Badges'
import { EmptyState } from '../common/States'

export function PriorityCases({ cases }: { cases: PriorityCase[] }) {
  if (cases.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-surface-200 p-5">
        <h3 className="text-sm font-semibold text-surface-900 mb-4">Cases Requiring Attention</h3>
        <EmptyState message="No priority cases" />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-surface-900">Cases Requiring Attention</h3>
        <span className="text-xs text-surface-500">{cases.length} cases</span>
      </div>
      <div className="overflow-x-auto -mx-5 px-5">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-100">
              <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide pb-2 pr-4">Ticket</th>
              <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide pb-2 pr-4 hidden sm:table-cell">Customer</th>
              <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide pb-2 pr-4">Issue</th>
              <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide pb-2 pr-4 hidden md:table-cell">Priority</th>
              <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide pb-2 pr-4 hidden lg:table-cell">Region</th>
              <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide pb-2">Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-50">
            {cases.map((c) => (
              <tr key={c.ticket_number} className="hover:bg-surface-50 transition-colors">
                <td className="py-2.5 pr-4">
                  <span className="text-xs font-mono text-surface-400">{c.ticket_number}</span>
                </td>
                <td className="py-2.5 pr-4 hidden sm:table-cell">
                  <span className="text-xs text-surface-600">{c.customer_name}</span>
                </td>
                <td className="py-2.5 pr-4">
                  <p className="text-xs text-surface-800 max-w-[200px] truncate">{c.subject}</p>
                </td>
                <td className="py-2.5 pr-4 hidden md:table-cell">
                  <PriorityBadge priority={c.priority} />
                </td>
                <td className="py-2.5 pr-4 hidden lg:table-cell">
                  <span className="text-xs text-surface-500">{c.region}</span>
                </td>
                <td className="py-2.5">
                  <div className="flex flex-wrap gap-1">
                    {c.reasons.map((reason, i) => (
                      <span key={i} className="text-[10px] text-surface-500 bg-surface-100 px-1.5 py-0.5 rounded">
                        {reason}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
