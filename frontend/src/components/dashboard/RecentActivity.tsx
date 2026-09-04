import type { RecentActivity as ActivityType } from '../../types'
import { EmptyState } from '../common/States'

function formatTimeAgo(dateStr: string) {
  try {
    const now = new Date()
    const then = new Date(dateStr)
    const diffMs = now.getTime() - then.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHrs = Math.floor(diffMins / 60)
    if (diffHrs < 24) return `${diffHrs}h ago`
    const diffDays = Math.floor(diffHrs / 24)
    return `${diffDays}d ago`
  } catch {
    return dateStr
  }
}

function ActivityIcon({ type }: { type: string }) {
  if (type === 'incident') {
    return (
      <div className="w-7 h-7 rounded-full bg-red-100 flex items-center justify-center shrink-0">
        <svg className="w-3.5 h-3.5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>
    )
  }
  if (type === 'network_event') {
    return (
      <div className="w-7 h-7 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
        <svg className="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </div>
    )
  }
  return (
    <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
      <svg className="w-3.5 h-3.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    </div>
  )
}

export function RecentActivityPanel({ activities }: { activities: ActivityType[] }) {
  if (activities.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-surface-200 p-5">
        <h3 className="text-sm font-semibold text-surface-900 mb-4">Recent Activity</h3>
        <EmptyState message="No recent activity" />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <h3 className="text-sm font-semibold text-surface-900 mb-4">Recent Activity</h3>
      <div className="space-y-1">
        {activities.map((a, i) => (
          <div key={i} className="flex items-start gap-3 py-2">
            <ActivityIcon type={a.type} />
            <div className="min-w-0 flex-1">
              <p className="text-xs text-surface-700 line-clamp-2">{a.description}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] text-surface-400">{formatTimeAgo(a.timestamp)}</span>
                {a.related_id && (
                  <span className="text-[10px] font-mono text-surface-400">{a.related_id}</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
