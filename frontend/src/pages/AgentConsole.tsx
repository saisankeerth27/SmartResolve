import { useState, useEffect, useCallback } from 'react'

// ── Types ─────────────────────────────────────────────

interface QueueItem {
  id: number
  ticket_number: string
  customer_id: number
  category: string
  priority: string
  subject: string
  status: string
  created_at: string
  customer_name?: string
  customer_segment?: string
  operator?: string
  review_status?: string
}

interface AnalysisResult {
  ticket_id: number
  ticket_number: string
  mode: string
  classification: {
    mode: string
    reason_codes: string[]
    confidence: number
    required_information: string[]
    escalation_required: boolean
    escalation_queue: string | null
    missing_fields: string[]
    blocking_reasons: string[]
    eligible_for_draft: boolean
  }
  draft: {
    draft_response: string
    reasoning_summary: string
    citations: { document_id: string; section: string }[]
    confidence: number
    limitations: string[]
    account_evidence: string[]
    operational_evidence: string[]
    knowledge_evidence: string[]
  } | null
  clarification: {
    question: string
    missing_field: string
    reason: string
    turn_number: number
  } | null
  handover: {
    case_id: string
    ticket_number: string
    customer_name: string
    customer_segment: string
    customer_phone: string
    account_service: string
    plan_name: string
    plan_type: string
    operator: string
    issue_summary: string
    original_message: string
    confirmed_facts: string[]
    missing_information: string[]
    previous_tickets: { ticket_number: string; subject: string; status: string }[]
    previous_troubleshooting: string[]
    network_context: Record<string, unknown>
    retrieval_result: string
    retrieval_confidence: number
    escalation_reasons: string[]
    escalation_queue: string
    severity: string
    timestamp: string
    current_status: string
    recommendations: string[]
    evidence_summary: string[]
  } | null
  conflicts: {
    conflict_type: string
    source_a: string
    source_b: string
    description: string
    impact: string
    human_action_required: string
  }[]
  retrieval_info: { total: number; average_score: number; chunks: unknown[] }
  errors: string[]
}

interface AuditEvent {
  ticket_id: number
  event_type: string
  details: Record<string, unknown> | null
  actor: string
  created_at: string
}

interface InvestigationContext {
  ticket: {
    id: number
    ticket_number: string
    category: string
    priority: string
    subject: string
    description: string
    status: string
    channel: string
    created_at: string
  }
  customer: {
    id: number
    customer_number: string
    name: string
    email: string
    phone: string
    segment: string
    status: string
  } | null
  subscription: {
    plan_name: string
    plan_code: string
    monthly_price: number
    data_limit_gb: number
    service_type: string
    service_number: string
    status: string
    site_name: string
    site_code: string
    technology: string
    region: string
    city: string
  } | null
  network: {
    site: {
      id: number
      site_code: string
      site_name: string
      technology: string
      region: string
      city: string
      state: string
      capacity_percent: number
      status: string
    } | null
    events: {
      id: number
      event_type: string
      severity: string
      title: string
      status: string
      started_at: string
    }[]
  }
  incidents: {
    id: number
    incident_number: string
    title: string
    severity: string
    region: string
    status: string
    started_at: string
  }[]
  investigation: {
    same_category_previous_tickets: number
    known_facts: string[]
    missing_information: string[]
    readiness: string
  }
}

// ── Support Queue (Left Panel) ────────────────────────

function SupportQueue({
  selectedId,
  onSelect,
  filter,
  onFilterChange,
}: {
  selectedId: number | null
  onSelect: (id: number) => void
  filter: string
  onFilterChange: (f: string) => void
}) {
  const [items, setItems] = useState<QueueItem[]>([])
  const [loading, setLoading] = useState(true)

  const fetchQueue = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filter && filter !== 'all') params.set('status', filter)
      params.set('page_size', '50')
      const res = await fetch(`/api/queue?${params.toString()}`)
      const data = await res.json()
      setItems(data.data || [])
    } catch {
      setItems([])
    }
    setLoading(false)
  }, [filter])

  useEffect(() => { fetchQueue() }, [fetchQueue])

  const getModeIndicator = (item: QueueItem) => {
    if (item.status === 'pending_agent_approval') return { color: 'bg-emerald-400', label: 'Routine', tooltip: 'Draft Ready' }
    if (item.status === 'needs_information') return { color: 'bg-amber-400', label: 'Info Needed', tooltip: 'Needs Information' }
    if (item.status === 'escalation_requested' || item.status === 'human_review') return { color: 'bg-red-400', label: 'Review', tooltip: 'Human Review Required' }
    if (item.status === 'analyzing') return { color: 'bg-blue-400', label: 'Analyzing', tooltip: 'Analysis in Progress' }
    if (item.status === 'resolved') return { color: 'bg-surface-300', label: 'Resolved', tooltip: 'Resolved' }
    return { color: 'bg-surface-300', label: item.status, tooltip: item.status }
  }

  const getPriorityColor = (p: string) => {
    if (p === 'critical') return 'text-red-600'
    if (p === 'high') return 'text-amber-600'
    return 'text-surface-500'
  }

  const filters = ['all', 'routine', 'needs_information', 'human_review', 'pending_approval', 'resolved']

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-3 border-b border-surface-200">
        <h3 className="text-xs font-semibold text-surface-900 uppercase tracking-wider mb-2">Support Queue</h3>
        <div className="flex flex-wrap gap-1">
          {filters.map(f => (
            <button
              key={f}
              onClick={() => onFilterChange(f)}
              className={`px-2 py-1 text-[10px] font-medium rounded transition-colors ${
                filter === f
                  ? 'bg-brand-100 text-brand-700'
                  : 'bg-surface-100 text-surface-600 hover:bg-surface-200'
              }`}
            >
              {f === 'all' ? 'All' : f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {loading && <div className="p-4 text-center text-xs text-surface-400">Loading queue...</div>}
        {!loading && items.length === 0 && <div className="p-4 text-center text-xs text-surface-400">No cases in queue</div>}
        {items.map(item => {
          const mode = getModeIndicator(item)
          return (
            <button
              key={item.id}
              onClick={() => onSelect(item.id)}
              className={`w-full text-left px-3 py-2.5 border-b border-surface-100 hover:bg-surface-50 transition-colors ${
                selectedId === item.id ? 'bg-brand-50 border-l-2 border-l-brand-500' : ''
              }`}
            >
              <div className="flex items-start gap-2">
                <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${mode.color}`} title={mode.tooltip} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-surface-400">{item.ticket_number}</span>
                    <span className={`text-[10px] font-medium ${getPriorityColor(item.priority)}`}>
                      {item.priority.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-xs font-medium text-surface-800 truncate mt-0.5">{item.customer_name || 'Unknown'}</p>
                  <p className="text-[10px] text-surface-500 truncate">{item.subject}</p>
                  {item.operator && (
                    <span className="inline-block mt-0.5 text-[9px] font-medium text-surface-400 bg-surface-100 px-1.5 py-0.5 rounded">
                      {item.operator}
                    </span>
                  )}
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

// ── Customer Context (Right Panel) ────────────────────

function CustomerContext({ investigation }: { investigation: InvestigationContext | null }) {
  if (!investigation) {
    return (
      <div className="flex items-center justify-center h-full text-xs text-surface-400">
        Select a case to view context
      </div>
    )
  }

  const { customer, subscription, network, incidents, investigation: inv } = investigation

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Customer */}
      <div className="px-3 py-3 border-b border-surface-200">
        <h4 className="text-[10px] font-semibold text-surface-500 uppercase tracking-wider mb-2">Customer</h4>
        {customer ? (
          <div className="space-y-1">
            <p className="text-xs font-medium text-surface-900">{customer.name}</p>
            <p className="text-[10px] text-surface-500">{customer.customer_number}</p>
            <p className="text-[10px] text-surface-500">{customer.phone}</p>
            <span className={`inline-block text-[9px] font-medium px-1.5 py-0.5 rounded ${
              customer.segment === 'enterprise' ? 'bg-purple-50 text-purple-700' :
              customer.segment === 'small_business' ? 'bg-blue-50 text-blue-700' :
              'bg-surface-100 text-surface-600'
            }`}>
              {customer.segment}
            </span>
          </div>
        ) : (
          <p className="text-[10px] text-surface-400">No customer data</p>
        )}
      </div>

      {/* Service */}
      <div className="px-3 py-3 border-b border-surface-200">
        <h4 className="text-[10px] font-semibold text-surface-500 uppercase tracking-wider mb-2">Service</h4>
        {subscription ? (
          <div className="space-y-1">
            <p className="text-xs font-medium text-surface-800">{subscription.plan_name}</p>
            <p className="text-[10px] text-surface-500">{subscription.service_type} - {subscription.service_number}</p>
            <p className="text-[10px] text-surface-500">Price: ₹{subscription.monthly_price}/mo</p>
            <p className="text-[10px] text-surface-500">Data: {subscription.data_limit_gb}GB</p>
            <span className={`inline-block text-[9px] font-medium px-1.5 py-0.5 rounded ${
              subscription.status === 'active' ? 'bg-emerald-50 text-emerald-700' :
              'bg-amber-50 text-amber-700'
            }`}>
              {subscription.status}
            </span>
          </div>
        ) : (
          <p className="text-[10px] text-surface-400">No subscription data</p>
        )}
      </div>

      {/* Network */}
      <div className="px-3 py-3 border-b border-surface-200">
        <h4 className="text-[10px] font-semibold text-surface-500 uppercase tracking-wider mb-2">Network</h4>
        {network.site ? (
          <div className="space-y-1">
            <p className="text-xs font-medium text-surface-800">{network.site.site_code}</p>
            <p className="text-[10px] text-surface-500">{network.site.technology} - {network.site.region}</p>
            <p className="text-[10px] text-surface-500">{network.site.city}, {network.site.state}</p>
            <p className="text-[10px] text-surface-500">Capacity: {network.site.capacity_percent}%</p>
            <span className={`inline-block text-[9px] font-medium px-1.5 py-0.5 rounded ${
              network.site.status === 'operational' ? 'bg-emerald-50 text-emerald-700' :
              network.site.status === 'degraded' ? 'bg-amber-50 text-amber-700' :
              network.site.status === 'offline' ? 'bg-red-50 text-red-700' :
              'bg-surface-100 text-surface-600'
            }`}>
              {network.site.status}
            </span>
          </div>
        ) : (
          <p className="text-[10px] text-surface-400">No site data</p>
        )}
        {network.events.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="text-[9px] font-medium text-surface-500 uppercase">Active Events</p>
            {network.events.filter(e => e.status === 'active').slice(0, 3).map(ev => (
              <div key={ev.id} className="text-[10px] text-surface-600">
                <span className={`font-medium ${
                  ev.severity === 'critical' ? 'text-red-600' :
                  ev.severity === 'high' ? 'text-amber-600' :
                  'text-surface-500'
                }`}>{ev.severity.toUpperCase()}</span> {ev.title}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Incidents */}
      {incidents.length > 0 && (
        <div className="px-3 py-3 border-b border-surface-200">
          <h4 className="text-[10px] font-semibold text-surface-500 uppercase tracking-wider mb-2">Active Incidents</h4>
          <div className="space-y-1">
            {incidents.filter(i => i.status !== 'resolved').slice(0, 3).map(inc => (
              <div key={inc.id} className="text-[10px]">
                <span className={`font-medium ${
                  inc.severity === 'critical' ? 'text-red-600' :
                  inc.severity === 'high' ? 'text-amber-600' :
                  'text-surface-500'
                }`}>{inc.severity.toUpperCase()}</span>
                <span className="text-surface-700 ml-1">{inc.incident_number}</span>
                <p className="text-surface-500 truncate">{inc.title}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Investigation */}
      <div className="px-3 py-3 border-b border-surface-200">
        <h4 className="text-[10px] font-semibold text-surface-500 uppercase tracking-wider mb-2">Investigation</h4>
        <div className="space-y-1">
          <p className="text-[10px] text-surface-600">
            <span className="font-medium">Previous tickets:</span> {inv.same_category_previous_tickets}
          </p>
          <p className="text-[10px] text-surface-600">
            <span className="font-medium">Readiness:</span> {inv.readiness}
          </p>
          {inv.known_facts.length > 0 && (
            <div className="mt-1">
              <p className="text-[9px] font-medium text-surface-500 uppercase">Known Facts</p>
              {inv.known_facts.slice(0, 3).map((fact, i) => (
                <p key={i} className="text-[10px] text-surface-600">• {fact}</p>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Conflict Display ──────────────────────────────────

function ConflictDisplay({ conflicts }: { conflicts: AnalysisResult['conflicts'] }) {
  if (conflicts.length === 0) return null

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <h4 className="text-xs font-semibold text-red-700">CONFLICT DETECTED</h4>
      </div>
      {conflicts.map((c, i) => (
        <div key={i} className="text-[10px] space-y-1">
          <p className="text-red-800 font-medium">{c.description}</p>
          <p className="text-red-600">Source A: {c.source_a}</p>
          <p className="text-red-600">Source B: {c.source_b}</p>
          <p className="text-red-700 font-medium">Impact: {c.impact}</p>
          <p className="text-red-700">Action: {c.human_action_required}</p>
        </div>
      ))}
    </div>
  )
}

// ── Mode A: Resolution Draft ──────────────────────────

function ResolutionDraft({
  draft,
  onAction,
}: {
  draft: AnalysisResult['draft']
  onAction: (action: string, data?: Record<string, unknown>) => void
}) {
  const [notes, setNotes] = useState('')

  if (!draft) return null

  return (
    <div className="space-y-3">
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h4 className="text-xs font-semibold text-emerald-800">GROUNDED RECOMMENDATION</h4>
          <span className="text-[10px] text-emerald-600 ml-auto">
            Confidence: {(draft.confidence * 100).toFixed(0)}%
          </span>
        </div>
        <div className="text-xs text-emerald-900 whitespace-pre-wrap">{draft.draft_response}</div>
      </div>

      {draft.reasoning_summary && (
        <div className="bg-surface-50 border border-surface-200 rounded-lg p-3">
          <h5 className="text-[10px] font-semibold text-surface-500 uppercase mb-1">Reasoning</h5>
          <p className="text-xs text-surface-700">{draft.reasoning_summary}</p>
        </div>
      )}

      {draft.account_evidence.length > 0 && (
        <div className="bg-surface-50 border border-surface-200 rounded-lg p-3">
          <h5 className="text-[10px] font-semibold text-surface-500 uppercase mb-1">Account Evidence</h5>
          <ul className="space-y-0.5">
            {draft.account_evidence.map((ev, i) => (
              <li key={i} className="text-[10px] text-surface-700">• {ev}</li>
            ))}
          </ul>
        </div>
      )}

      {draft.citations.length > 0 && (
        <div className="bg-surface-50 border border-surface-200 rounded-lg p-3">
          <h5 className="text-[10px] font-semibold text-surface-500 uppercase mb-1">Knowledge Citations</h5>
          <div className="flex flex-wrap gap-1">
            {draft.citations.map((cit, i) => (
              <span key={i} className="text-[9px] bg-brand-50 text-brand-700 px-1.5 py-0.5 rounded">
                {cit.document_id}
              </span>
            ))}
          </div>
        </div>
      )}

      {draft.limitations.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <h5 className="text-[10px] font-semibold text-amber-700 uppercase mb-1">Limitations</h5>
          <ul className="space-y-0.5">
            {draft.limitations.map((lim, i) => (
              <li key={i} className="text-[10px] text-amber-800">• {lim}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => onAction('approve', { notes })}
          className="flex-1 px-3 py-2 text-xs font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
        >
          Approve Recommendation
        </button>
        <button
          onClick={() => onAction('dismiss', { reason: notes })}
          className="px-3 py-2 text-xs font-medium text-surface-600 bg-surface-100 rounded-lg hover:bg-surface-200 transition-colors"
        >
          Dismiss
        </button>
        <button
          onClick={() => onAction('escalate', { reason: notes })}
          className="px-3 py-2 text-xs font-medium text-amber-700 bg-amber-50 rounded-lg hover:bg-amber-100 transition-colors"
        >
          Escalate
        </button>
      </div>
      <button
        onClick={() => onAction('resolve-final', { resolution: notes || 'Case resolved after recommendation approval' })}
        className="w-full px-3 py-2 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors"
      >
        Mark Resolved
      </button>
      <input
        type="text"
        placeholder="Add notes (optional)..."
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        className="w-full px-3 py-1.5 text-xs border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
      />
    </div>
  )
}

// ── Mode B: Clarification ─────────────────────────────

function ClarificationPanel({
  clarification,
  onSubmitAnswer,
}: {
  clarification: AnalysisResult['clarification']
  onSubmitAnswer: (field: string, answer: string) => void
}) {
  const [answer, setAnswer] = useState('')

  if (!clarification) return null

  return (
    <div className="space-y-3">
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h4 className="text-xs font-semibold text-amber-800">INFORMATION NEEDED</h4>
          <span className="text-[10px] text-amber-600 ml-auto">Turn {clarification.turn_number}</span>
        </div>
        <p className="text-xs text-amber-900 mb-1">{clarification.reason}</p>
        <div className="bg-white rounded p-2 mt-2">
          <p className="text-xs font-medium text-surface-800">{clarification.question}</p>
        </div>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Type customer response..."
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && answer.trim()) {
              onSubmitAnswer(clarification.missing_field, answer.trim())
              setAnswer('')
            }
          }}
          className="flex-1 px-3 py-2 text-xs border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <button
          onClick={() => {
            if (answer.trim()) {
              onSubmitAnswer(clarification.missing_field, answer.trim())
              setAnswer('')
            }
          }}
          disabled={!answer.trim()}
          className="px-3 py-2 text-xs font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50"
        >
          Send Question
        </button>
      </div>
    </div>
  )
}

// ── Mode C: Escalation Handover ───────────────────────

function HandoverPanel({ handover, onAction }: { handover: AnalysisResult['handover']; onAction: (action: string, data?: Record<string, unknown>) => void }) {
  if (!handover) return null

  const severityColors = {
    critical: 'bg-red-100 text-red-700 border-red-200',
    high: 'bg-amber-100 text-amber-700 border-amber-200',
    medium: 'bg-blue-100 text-blue-700 border-blue-200',
    low: 'bg-surface-100 text-surface-600 border-surface-200',
  }

  return (
    <div className="space-y-3">
      <div className="bg-red-50 border border-red-200 rounded-lg p-3">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <h4 className="text-xs font-semibold text-red-700">HUMAN REVIEW REQUIRED</h4>
          <span className={`text-[9px] font-medium px-1.5 py-0.5 rounded border ml-auto ${severityColors[handover.severity as keyof typeof severityColors]}`}>
            {handover.severity.toUpperCase()}
          </span>
        </div>
        <p className="text-[10px] text-red-600">Route: {handover.escalation_queue}</p>
      </div>

      <div className="bg-surface-50 border border-surface-200 rounded-lg p-3">
        <h5 className="text-[10px] font-semibold text-surface-500 uppercase mb-2">Escalation Reasons</h5>
        <ul className="space-y-0.5">
          {handover.escalation_reasons.map((r, i) => (
            <li key={i} className="text-[10px] text-surface-700">• {r}</li>
          ))}
        </ul>
      </div>

      {handover.confirmed_facts.length > 0 && (
        <div className="bg-surface-50 border border-surface-200 rounded-lg p-3">
          <h5 className="text-[10px] font-semibold text-surface-500 uppercase mb-2">Confirmed Facts</h5>
          <ul className="space-y-0.5">
            {handover.confirmed_facts.map((f, i) => (
              <li key={i} className="text-[10px] text-surface-700">• {f}</li>
            ))}
          </ul>
        </div>
      )}

      {handover.missing_information.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <h5 className="text-[10px] font-semibold text-amber-700 uppercase mb-2">Missing Information</h5>
          <ul className="space-y-0.5">
            {handover.missing_information.map((m, i) => (
              <li key={i} className="text-[10px] text-amber-800">• {m}</li>
            ))}
          </ul>
        </div>
      )}

      {handover.previous_tickets.length > 0 && (
        <div className="bg-surface-50 border border-surface-200 rounded-lg p-3">
          <h5 className="text-[10px] font-semibold text-surface-500 uppercase mb-2">Previous Tickets</h5>
          <div className="space-y-1">
            {handover.previous_tickets.map((pt, i) => (
              <div key={i} className="text-[10px]">
                <span className="font-mono text-surface-400">{pt.ticket_number}</span>
                <span className="text-surface-700 ml-1">{pt.subject}</span>
                <span className={`ml-1 ${pt.status === 'resolved' ? 'text-emerald-600' : 'text-amber-600'}`}>
                  ({pt.status})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {handover.recommendations.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <h5 className="text-[10px] font-semibold text-blue-700 uppercase mb-2">Recommendations</h5>
          <ul className="space-y-0.5">
            {handover.recommendations.map((r, i) => (
              <li key={i} className="text-[10px] text-blue-800">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => onAction('escalate', { reason: handover.escalation_reasons.join('; '), queue: handover.escalation_queue })}
          className="flex-1 px-3 py-2 text-xs font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
        >
          Open Human Review
        </button>
        <button
          onClick={() => onAction('resolve-final', { resolution: 'Case resolved after human review' })}
          className="px-3 py-2 text-xs font-medium text-emerald-700 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition-colors"
        >
          Resolve Case
        </button>
      </div>
    </div>
  )
}

// ── Audit Trail ───────────────────────────────────────

function AuditTrail({ events }: { events: AuditEvent[] }) {
  if (events.length === 0) return null

  const getEventIcon = (type: string) => {
    if (type.includes('approved')) return '✓'
    if (type.includes('dismissed')) return '✕'
    if (type.includes('escalat')) return '↑'
    if (type.includes('clarif')) return '?'
    if (type.includes('draft')) return '📝'
    if (type.includes('mode')) return '◎'
    if (type.includes('retrieval')) return '🔍'
    if (type.includes('conflict')) return '⚠'
    if (type.includes('ai_failed')) return '⚡'
    return '•'
  }

  return (
    <div className="bg-surface-50 border border-surface-200 rounded-lg p-3">
      <h5 className="text-[10px] font-semibold text-surface-500 uppercase mb-2">Audit Trail</h5>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {events.map((ev, i) => (
          <div key={i} className="flex items-start gap-2 text-[10px]">
            <span className="text-surface-400 shrink-0">{getEventIcon(ev.event_type)}</span>
            <div className="min-w-0">
              <span className="text-surface-700 font-medium">{ev.event_type.replace(/_/g, ' ')}</span>
              <span className="text-surface-400 ml-1">
                {new Date(ev.created_at).toLocaleTimeString()}
              </span>
              {ev.details && typeof ev.details === 'object' && (
                <p className="text-surface-500 truncate">
                  {Object.entries(ev.details).map(([k, v]) => `${k}: ${String(v)}`).join(', ')}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main Agent Console ────────────────────────────────

export default function AgentConsolePage() {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [filter, setFilter] = useState('all')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [investigation, setInvestigation] = useState<InvestigationContext | null>(null)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [analyzing, setAnalyzing] = useState(false)
  const [errors, setErrors] = useState<string[]>([])

  const loadCase = useCallback(async (ticketId: number) => {
    setSelectedId(ticketId)
    setAnalysis(null)
    setInvestigation(null)
    setAuditEvents([])
    setErrors([])

    try {
      const invRes = await fetch(`/api/cases/${ticketId}/investigation`)
      if (invRes.ok) {
        const invData = await invRes.json()
        setInvestigation(invData)
      }
    } catch {
      // Investigation failed
    }
  }, [])

  const runAnalysis = useCallback(async () => {
    if (!selectedId) return
    setAnalyzing(true)
    setErrors([])

    try {
      const res = await fetch(`/api/cases/${selectedId}/analyze`, { method: 'POST' })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Analysis failed' }))
        setErrors([errData.detail || 'Analysis failed'])
        setAnalyzing(false)
        return
      }
      const data = await res.json()
      setAnalysis(data)

      if (data.errors?.length > 0) {
        setErrors(data.errors)
      }

      // Load audit trail
      const auditRes = await fetch(`/api/cases/${selectedId}/audit`)
      if (auditRes.ok) {
        const auditData = await auditRes.json()
        setAuditEvents(auditData.audit || [])
      }

      // Refresh investigation
      const invRes = await fetch(`/api/cases/${selectedId}/investigation`)
      if (invRes.ok) {
        setInvestigation(await invRes.json())
      }
    } catch {
      setErrors(['Failed to run analysis. Please try again.'])
    }
    setAnalyzing(false)
  }, [selectedId])

  const handleAgentAction = useCallback(async (action: string, data?: Record<string, unknown>) => {
    if (!selectedId) return

    try {
      const res = await fetch(`/api/cases/${selectedId}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data || {}),
      })
      const result = await res.json()
      if (res.ok && result.success) {
        // Refresh the case
        await loadCase(selectedId)
        setAnalysis(null)
        // Trigger queue refresh by updating filter
        setFilter(f => f)
      } else if (!res.ok) {
        setErrors([result.detail || 'Action failed'])
      }
    } catch {
      setErrors(['Action failed. Please try again.'])
    }
  }, [selectedId, loadCase])

  const handleSubmitAnswer = useCallback(async (field: string, answer: string) => {
    if (!selectedId) return

    try {
      const res = await fetch(`/api/cases/${selectedId}/clarify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ field, answer }),
      })
      if (res.ok) {
        const data = await res.json()
        // Update analysis with new mode
        setAnalysis(prev => prev ? { ...prev, mode: data.new_mode, classification: data.classification, draft: data.draft, clarification: data.clarification } : null)
      }
    } catch {
      // Clarification failed
    }
  }, [selectedId])

  return (
    <div className="flex h-[calc(100vh-3.5rem)] -m-4 lg:-m-6">
      {/* Left: Support Queue */}
      <div className="w-72 border-r border-surface-200 bg-white shrink-0 hidden md:flex flex-col">
        <SupportQueue
          selectedId={selectedId}
          onSelect={loadCase}
          filter={filter}
          onFilterChange={setFilter}
        />
      </div>

      {/* Center: Case Workspace */}
      <div className="flex-1 flex flex-col min-w-0 bg-surface-50">
        {!selectedId ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-surface-100 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 className="text-sm font-medium text-surface-700 mb-1">Select a Case</h3>
              <p className="text-xs text-surface-500">Choose a case from the support queue to begin analysis</p>
            </div>
          </div>
        ) : (
          <>
            {/* Case Header */}
            <div className="px-4 py-3 bg-white border-b border-surface-200 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-surface-400">
                    {investigation?.ticket.ticket_number || `#${selectedId}`}
                  </span>
                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                    investigation?.ticket.priority === 'critical' ? 'bg-red-50 text-red-700' :
                    investigation?.ticket.priority === 'high' ? 'bg-amber-50 text-amber-700' :
                    'bg-surface-100 text-surface-600'
                  }`}>
                    {investigation?.ticket.priority?.toUpperCase()}
                  </span>
                  {analysis && (
                    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                      analysis.mode === 'A' ? 'bg-emerald-50 text-emerald-700' :
                      analysis.mode === 'B' ? 'bg-amber-50 text-amber-700' :
                      'bg-red-50 text-red-700'
                    }`}>
                      Mode {analysis.mode}
                    </span>
                  )}
                </div>
                <p className="text-xs text-surface-700 mt-0.5">
                  {investigation?.ticket.subject || 'Loading...'}
                </p>
              </div>
              <button
                onClick={runAnalysis}
                disabled={analyzing}
                className="px-4 py-2 text-xs font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700 transition-colors disabled:opacity-50"
              >
                {analyzing ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Analyzing...
                  </span>
                ) : (
                  'Analyze Case'
                )}
              </button>
            </div>

            {/* Case Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Error Display */}
              {errors.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <h4 className="text-xs font-semibold text-red-700 mb-1">Errors</h4>
                  {errors.map((err, i) => (
                    <p key={i} className="text-[10px] text-red-600">• {err}</p>
                  ))}
                </div>
              )}

              {/* Conflicts */}
              {analysis && analysis.conflicts.length > 0 && (
                <ConflictDisplay conflicts={analysis.conflicts} />
              )}

              {/* Mode A: Resolution Draft */}
              {analysis && analysis.mode === 'A' && analysis.draft && (
                <ResolutionDraft
                  draft={analysis.draft}
                  onAction={handleAgentAction}
                />
              )}

              {/* Mode B: Clarification */}
              {analysis && analysis.mode === 'B' && analysis.clarification && (
                <ClarificationPanel
                  clarification={analysis.clarification}
                  onSubmitAnswer={handleSubmitAnswer}
                />
              )}

              {/* Mode C: Escalation Handover */}
              {analysis && analysis.mode === 'C' && analysis.handover && (
                <HandoverPanel handover={analysis.handover} onAction={handleAgentAction} />
              )}

              {/* Classification Details */}
              {analysis && (
                <div className="bg-surface-50 border border-surface-200 rounded-lg p-3">
                  <h5 className="text-[10px] font-semibold text-surface-500 uppercase mb-2">Classification Details</h5>
                  <div className="space-y-1">
                    <p className="text-[10px] text-surface-600">
                      <span className="font-medium">Mode:</span> {analysis.mode} ({analysis.mode === 'A' ? 'Routine' : analysis.mode === 'B' ? 'Missing Info' : 'Escalation'})
                    </p>
                    <p className="text-[10px] text-surface-600">
                      <span className="font-medium">Confidence:</span> {(analysis.classification.confidence * 100).toFixed(0)}%
                    </p>
                    {analysis.classification.escalation_required && (
                      <p className="text-[10px] text-red-600">
                        <span className="font-medium">Escalation Queue:</span> {analysis.classification.escalation_queue}
                      </p>
                    )}
                    {analysis.classification.reason_codes.length > 0 && (
                      <div>
                        <p className="text-[9px] font-medium text-surface-500 uppercase">Reason Codes</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {analysis.classification.reason_codes.map((code, i) => (
                            <span key={i} className="text-[9px] bg-surface-100 text-surface-600 px-1.5 py-0.5 rounded">
                              {code.split(':')[0]}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Retrieval Info */}
              {analysis && analysis.retrieval_info.total > 0 && (
                <div className="bg-surface-50 border border-surface-200 rounded-lg p-3">
                  <h5 className="text-[10px] font-semibold text-surface-500 uppercase mb-2">Retrieval</h5>
                  <p className="text-[10px] text-surface-600">
                    {analysis.retrieval_info.total} articles retrieved (avg score: {analysis.retrieval_info.average_score.toFixed(2)})
                  </p>
                </div>
              )}

              {/* Audit Trail */}
              {auditEvents.length > 0 && (
                <AuditTrail events={auditEvents} />
              )}

              {/* No analysis yet */}
              {!analysis && !analyzing && (
                <div className="text-center py-8">
                  <p className="text-xs text-surface-500">Click "Analyze Case" to run Mode A/B/C classification</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Right: Customer Context */}
      <div className="w-80 border-l border-surface-200 bg-white shrink-0 hidden lg:flex flex-col">
        <div className="px-3 py-3 border-b border-surface-200">
          <h3 className="text-xs font-semibold text-surface-900 uppercase tracking-wider">Case Context</h3>
        </div>
        <CustomerContext investigation={investigation} />
      </div>
    </div>
  )
}
