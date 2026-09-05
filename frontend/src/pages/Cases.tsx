import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchApi } from '../services/api'
import { StatusBadge, PriorityBadge } from '../components/common/Badges'
import { LoadingState, ErrorState, EmptyState } from '../components/common/States'

type CaseTicket = {
  id: number
  ticket_number: string
  subject: string
  category: string
  priority: string
  status: string
  created_at: string
  assigned_team: string | null
  customer_name: string
  customer_number: string
  customer_phone: string | null
  archived: boolean
}

type TicketListResponse = {
  data: CaseTicket[]
  pagination: {
    total: number
    page: number
    page_size: number
    total_pages: number
  }
}

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

export function CasesPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [category, setCategory] = useState('')
  const [archived, setArchived] = useState(false)
  const [page, setPage] = useState(1)
  const [data, setData] = useState<TicketListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      params.set('page', String(page))
      params.set('page_size', '20')
      if (search) params.set('search', search)
      if (status) params.set('status', status)
      if (priority) params.set('priority', priority)
      if (category) params.set('category', category)
      params.set('archived', String(archived))
      const result = await fetchApi<TicketListResponse>(`/api/tickets?${params.toString()}`)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cases')
    } finally {
      setLoading(false)
    }
  }, [page, search, status, priority, category, archived])

  const updateTicket = async (ticketId: number, path: string, body: Record<string, unknown> = {}) => {
    const response = await fetch(`/api/tickets/${ticketId}${path}`, {
      method: path === '' ? 'PATCH' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!response.ok) throw new Error((await response.json()).detail || 'Ticket update failed')
    await fetchData()
  }

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const clearFilters = () => {
    setSearch('')
    setStatus('')
    setPriority('')
    setCategory('')
    setArchived(false)
    setPage(1)
  }

  const hasFilters = search || status || priority || category || archived

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-surface-900">Cases</h2>
        <p className="text-sm text-surface-500 mt-0.5">
          Investigate customer issues using operational and service data.
        </p>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search by ticket, customer, or subject..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="w-full pl-9 pr-3 py-2 text-sm border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          />
        </div>
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1) }}
          className="px-3 py-2 text-sm border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All Statuses</option>
          <option value="open">New / Open</option>
          <option value="in_progress">In Progress</option>
          <option value="pending_customer">Pending Customer</option>
          <option value="analyzing">Analyzing</option>
          <option value="pending_agent_approval">Pending Approval</option>
          <option value="needs_information">Needs Information</option>
          <option value="escalation_requested">Escalation Requested</option>
          <option value="human_review">Human Review</option>
          <option value="approved">Approved</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
          <option value="escalated">Escalated</option>
          <option value="dismissed">Dismissed</option>
        </select>
        <button
          onClick={() => { setArchived(value => !value); setPage(1) }}
          className={`px-3 py-2 text-sm border rounded-lg ${archived ? 'border-brand-300 bg-brand-50 text-brand-700' : 'border-surface-200 bg-white text-surface-700'}`}
        >
          {archived ? 'Archived' : 'Active'}
        </button>
        <select
          value={priority}
          onChange={(e) => { setPriority(e.target.value); setPage(1) }}
          className="px-3 py-2 text-sm border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1) }}
          className="px-3 py-2 text-sm border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All Categories</option>
          <option value="network">Network</option>
          <option value="connectivity">Connectivity</option>
          <option value="billing">Billing</option>
          <option value="voice">Voice</option>
          <option value="sms">SMS</option>
          <option value="roaming">Roaming</option>
          <option value="device">Device</option>
          <option value="account">Account</option>
        </select>
      </div>

      {hasFilters && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-surface-500">Active filters:</span>
          {search && <span className="text-xs bg-surface-100 text-surface-600 px-2 py-0.5 rounded">Search: {search}</span>}
          {status && <span className="text-xs bg-surface-100 text-surface-600 px-2 py-0.5 rounded">Status: {status}</span>}
          {priority && <span className="text-xs bg-surface-100 text-surface-600 px-2 py-0.5 rounded">Priority: {priority}</span>}
          {category && <span className="text-xs bg-surface-100 text-surface-600 px-2 py-0.5 rounded">Category: {category}</span>}
          <button onClick={clearFilters} className="text-xs text-brand-600 hover:text-brand-700 font-medium ml-1">
            Clear all
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && !data && <LoadingState message="Loading cases..." />}

      {/* Error */}
      {error && <ErrorState message={error} onRetry={fetchData} />}

      {/* Desktop Table */}
      {data && !loading && (
        <>
          <div className="hidden md:block bg-white rounded-xl border border-surface-200 overflow-hidden">
            {data.data.length === 0 ? (
              <EmptyState message="No cases match your filters" />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-surface-200 bg-surface-50">
                      <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide px-4 py-2.5">Ticket</th>
                      <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide px-4 py-2.5">Customer</th>
                      <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide px-4 py-2.5">Issue</th>
                      <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide px-4 py-2.5 hidden lg:table-cell">Category</th>
                      <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide px-4 py-2.5">Priority</th>
                      <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide px-4 py-2.5">Status</th>
                      <th className="text-left text-[10px] font-medium text-surface-500 uppercase tracking-wide px-4 py-2.5 hidden sm:table-cell">Created</th>
                      <th className="text-right text-[10px] font-medium text-surface-500 uppercase tracking-wide px-4 py-2.5">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-100">
                    {data.data.map((ticket) => (
                      <tr
                        key={ticket.id}
                        className="hover:bg-surface-50 cursor-pointer transition-colors"
                        onClick={() => navigate(`/cases/${ticket.id}`)}
                      >
                        <td className="px-4 py-3">
                          <span className="text-xs font-mono text-surface-400">{ticket.ticket_number}</span>
                        </td>
                        <td className="px-4 py-3">
                          <p className="text-sm font-medium text-surface-800 truncate max-w-[160px]">{ticket.customer_name}</p>
                          <p className="text-[10px] text-surface-400 font-mono">{ticket.customer_number}</p>
                        </td>
                        <td className="px-4 py-3">
                          <p className="text-sm text-surface-800 truncate max-w-[220px]">{ticket.subject}</p>
                          {ticket.assigned_team && (
                            <p className="text-[10px] text-surface-400 mt-0.5">{ticket.assigned_team}</p>
                          )}
                        </td>
                        <td className="px-4 py-3 hidden lg:table-cell">
                          <span className="text-xs text-surface-600 capitalize">{ticket.category}</span>
                        </td>
                        <td className="px-4 py-3">
                          <PriorityBadge priority={ticket.priority} />
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={ticket.status} />
                        </td>
                        <td className="px-4 py-3 hidden sm:table-cell">
                          <span className="text-xs text-surface-500">{formatTimeAgo(ticket.created_at)}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={(e) => { e.stopPropagation(); navigate(`/cases/${ticket.id}`) }}
                            className="px-3 py-1.5 text-xs font-medium text-brand-600 bg-brand-50 rounded-lg hover:bg-brand-100 transition-colors"
                          >
                            Investigate
                          </button>
                          <select
                            value={ticket.status}
                            onChange={async (event) => {
                              event.stopPropagation()
                              try { await updateTicket(ticket.id, '/status', { status: event.target.value, reason: 'Updated from Cases list' }) } catch (err) { setError(err instanceof Error ? err.message : 'Status update failed') }
                            }}
                            onClick={event => event.stopPropagation()}
                            className="ml-2 px-2 py-1.5 text-[11px] border border-surface-200 rounded-lg bg-white"
                          >
                            {['open', 'in_progress', 'needs_information', 'pending_customer', 'resolved', 'escalated', 'closed'].map(value => <option key={value} value={value}>{value.replace(/_/g, ' ')}</option>)}
                          </select>
                          <button
                            onClick={async (event) => {
                              event.stopPropagation()
                              try { await updateTicket(ticket.id, archived ? '/restore' : '/archive') } catch (err) { setError(err instanceof Error ? err.message : 'Archive update failed') }
                            }}
                            className="ml-2 px-2 py-1.5 text-[11px] font-medium text-surface-600 bg-surface-100 rounded-lg hover:bg-surface-200"
                          >
                            {archived ? 'Restore' : 'Archive'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Mobile Cards */}
          <div className="md:hidden space-y-3">
            {data.data.length === 0 ? (
              <EmptyState message="No cases match your filters" />
            ) : (
              data.data.map((ticket) => (
                <div
                  key={ticket.id}
                  onClick={() => navigate(`/cases/${ticket.id}`)}
                  className="bg-white rounded-xl border border-surface-200 p-4 cursor-pointer hover:border-brand-300 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-mono text-surface-400">{ticket.ticket_number}</span>
                        <PriorityBadge priority={ticket.priority} />
                        <StatusBadge status={ticket.status} />
                      </div>
                      <p className="text-sm font-medium text-surface-800 mt-1.5 truncate">{ticket.subject}</p>
                      <p className="text-xs text-surface-500 mt-0.5">{ticket.customer_name}</p>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); navigate(`/cases/${ticket.id}`) }}
                      className="shrink-0 px-2.5 py-1.5 text-[11px] font-medium text-brand-600 bg-brand-50 rounded-lg hover:bg-brand-100"
                    >
                      Open
                    </button>
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-surface-400">
                    <span className="capitalize">{ticket.category}</span>
                    <span>{ticket.assigned_team || 'Unassigned'}</span>
                    <span>{formatTimeAgo(ticket.created_at)}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-3" onClick={event => event.stopPropagation()}>
                    <select
                      value={ticket.status}
                      onChange={async event => {
                        try { await updateTicket(ticket.id, '/status', { status: event.target.value, reason: 'Updated from Cases list' }) } catch (err) { setError(err instanceof Error ? err.message : 'Status update failed') }
                      }}
                      className="flex-1 px-2 py-1.5 text-[11px] border border-surface-200 rounded-lg bg-white"
                    >
                      {['open', 'in_progress', 'needs_information', 'pending_customer', 'resolved', 'escalated', 'closed'].map(value => <option key={value} value={value}>{value.replace(/_/g, ' ')}</option>)}
                    </select>
                    <button
                      onClick={async () => {
                        try { await updateTicket(ticket.id, archived ? '/restore' : '/archive') } catch (err) { setError(err instanceof Error ? err.message : 'Archive update failed') }
                      }}
                      className="px-2.5 py-1.5 text-[11px] font-medium text-surface-600 bg-surface-100 rounded-lg"
                    >{archived ? 'Restore' : 'Archive'}</button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          {data.pagination.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-xs text-surface-500">
                Showing {((data.pagination.page - 1) * data.pagination.page_size) + 1} -{' '}
                {Math.min(data.pagination.page * data.pagination.page_size, data.pagination.total)} of {data.pagination.total}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => p - 1)}
                  disabled={page <= 1}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-xs text-surface-500">
                  Page {data.pagination.page} of {data.pagination.total_pages}
                </span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= data.pagination.total_pages}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
