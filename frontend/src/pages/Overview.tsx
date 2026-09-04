import { useEffect, useState, useCallback } from 'react'
import type { DashboardOverview } from '../types'
import { fetchApi } from '../services/api'
import { LoadingState, ErrorState, SkeletonCard } from '../components/common/States'
import { KpiCards } from '../components/dashboard/KpiCards'
import { NetworkHealthPanel } from '../components/dashboard/NetworkHealth'
import { TicketWorkload } from '../components/dashboard/TicketWorkload'
import { ActiveIncidentsPanel } from '../components/dashboard/ActiveIncidents'
import { RegionalImpact } from '../components/dashboard/RegionalImpact'
import { PriorityCases } from '../components/dashboard/PriorityCases'
import { RecentActivityPanel } from '../components/dashboard/RecentActivity'

export function OverviewPage() {
  const [data, setData] = useState<DashboardOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchApi<DashboardOverview>('/api/dashboard/overview')
      setData(result)
      setLastRefresh(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <LoadingState message="Loading operations data..." />
      </div>
    )
  }

  if (error && !data) {
    return <ErrorState message={`Unable to load operations data. ${error}`} onRetry={fetchData} />
  }

  if (!data) return null

  return (
    <div className="space-y-6">
      {/* Refresh bar */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-surface-500">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-surface-600 bg-white border border-surface-200 rounded-lg hover:bg-surface-50 disabled:opacity-50 transition-colors"
        >
          <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <KpiCards metrics={data.metrics} />

      {/* Network Health + Ticket Workload */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <NetworkHealthPanel health={data.network_health} />
        <TicketWorkload breakdown={data.ticket_breakdown} />
      </div>

      {/* Active Incidents + Regional Impact */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ActiveIncidentsPanel incidents={data.active_incidents} />
        <RegionalImpact regions={data.regional_impact} />
      </div>

      {/* Priority Cases */}
      <PriorityCases cases={data.priority_cases} />

      {/* Recent Activity */}
      <RecentActivityPanel activities={data.recent_activity} />
    </div>
  )
}
