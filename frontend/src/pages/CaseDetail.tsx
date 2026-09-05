import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchInvestigation, fetchReasoning, fetchResolution, submitReview } from '../services/api'
import type { CaseInvestigationContext, CaseReasoningResponse, ResolutionDecision } from '../types/case'
import { StatusBadge, PriorityBadge, SeverityIndicator, TechBadge, SegmentBadge } from '../components/common/Badges'
import { LoadingState, ErrorState } from '../components/common/States'

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

function formatTimestamp(dateStr: string) {
  try {
    const d = new Date(dateStr)
    return d.toLocaleString('en-US', {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}

function PanelCard({ title, children, className = '' }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-xl border border-surface-200 ${className}`}>
      <div className="px-4 py-3 border-b border-surface-100">
        <h3 className="text-sm font-semibold text-surface-900">{title}</h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  )
}

function FieldRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="flex items-baseline justify-between py-1.5">
      <span className="text-xs text-surface-500">{label}</span>
      <span className="text-sm font-medium text-surface-800 text-right">{value ?? 'Not available'}</span>
    </div>
  )
}

function ReadinessIndicator({ readiness }: { readiness: string }) {
  const config: Record<string, { bg: string; text: string; border: string; label: string }> = {
    'READY': { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', label: 'Ready for Analysis' },
    'PARTIAL': { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', label: 'Partial Context' },
    'INSUFFICIENT DATA': { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', label: 'Insufficient Data' },
  }
  const c = config[readiness] || config['PARTIAL']
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg border ${c.bg} ${c.border}`}>
      <span className={`text-sm font-semibold ${c.text}`}>{readiness}</span>
      <span className={`text-xs ${c.text} opacity-70`}>{c.label}</span>
    </div>
  )
}

function TimelineItem({ event, isLast }: { event: { event_type: string; actor_type: string; description: string; created_at: string }; isLast: boolean }) {
  const iconColor: Record<string, string> = {
    created: 'bg-blue-100 text-blue-600',
    assigned: 'bg-surface-100 text-surface-600',
    troubleshooting: 'bg-amber-100 text-amber-600',
    customer_reply: 'bg-emerald-100 text-emerald-600',
    agent_note: 'bg-surface-100 text-surface-600',
    status_changed: 'bg-blue-100 text-blue-600',
    escalation: 'bg-red-100 text-red-600',
    resolved: 'bg-emerald-100 text-emerald-600',
  }
  const icon: Record<string, string> = {
    created: 'M12 4v16m8-8H4',
    assigned: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    troubleshooting: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
    customer_reply: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z',
    agent_note: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    status_changed: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
    escalation: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
    resolved: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  }
  const color = iconColor[event.event_type] || 'bg-surface-100 text-surface-600'
  const ic = icon[event.event_type] || icon.created

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${color}`}>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d={ic} />
          </svg>
        </div>
        {!isLast && <div className="w-px flex-1 bg-surface-200 mt-1" />}
      </div>
      <div className={`pb-4 ${isLast ? '' : ''}`}>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-medium text-surface-400 uppercase">{event.event_type.replace(/_/g, ' ')}</span>
          <span className="text-[10px] text-surface-400">{formatTimestamp(event.created_at)}</span>
        </div>
        <p className="text-xs text-surface-700 mt-0.5">{event.description}</p>
      </div>
    </div>
  )
}

function InteractionIcon({ type }: { type: string }) {
  const colors: Record<string, string> = {
    call: 'bg-blue-100 text-blue-600',
    chat: 'bg-emerald-100 text-emerald-600',
    email: 'bg-amber-100 text-amber-600',
    sms: 'bg-purple-100 text-purple-600',
    app: 'bg-surface-100 text-surface-600',
  }
  const icons: Record<string, string> = {
    call: 'M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z',
    chat: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    email: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
    sms: 'M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z',
    app: 'M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z',
  }
  return (
    <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${colors[type] || colors.app}`}>
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d={icons[type] || icons.app} />
      </svg>
    </div>
  )
}

function AiResultPanel({ result, onReanalyze }: { result: CaseReasoningResponse; onReanalyze: () => void }) {
  const navigate = useNavigate()
  const { reasoning, retrieval } = result
  const isGrounded = reasoning.status === 'grounded'

  const confidenceConfig: Record<string, { bg: string; text: string; border: string; label: string }> = {
    high: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', label: 'HIGH' },
    medium: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', label: 'MEDIUM' },
    low: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', label: 'LOW' },
  }
  const conf = confidenceConfig[reasoning.confidence] || confidenceConfig.low

  return (
    <div className="space-y-4">
      {/* Status Banner */}
      <div className={`px-3 py-2 rounded-lg border ${isGrounded ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200'}`}>
        <div className="flex items-center gap-2">
          {isGrounded ? (
            <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          )}
          <span className={`text-xs font-semibold ${isGrounded ? 'text-emerald-700' : 'text-amber-700'}`}>
            {isGrounded ? 'Grounded Assessment' : 'Insufficient Evidence'}
          </span>
        </div>
      </div>

      {/* Summary */}
      <div>
        <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Summary</h4>
        <p className="text-sm text-surface-700 leading-relaxed">{reasoning.summary}</p>
      </div>

      {/* Possible Causes */}
      {reasoning.possible_causes.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Possible Causes</h4>
          <div className="space-y-2">
            {reasoning.possible_causes.map((cause, i) => (
              <div key={i} className="border border-surface-100 rounded-lg p-2.5">
                <p className="text-sm font-medium text-surface-800">{cause.cause}</p>
                {cause.evidence.length > 0 && (
                  <div className="mt-1.5 space-y-1">
                    {cause.evidence.map((ev, j) => (
                      <div key={j} className="flex items-start gap-1.5">
                        <span className="text-[10px] text-surface-400 mt-0.5">evidence</span>
                        <span className="text-xs text-surface-600">{ev}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Next Steps */}
      {reasoning.recommended_next_steps.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Recommended Next Steps</h4>
          <ol className="space-y-1.5">
            {reasoning.recommended_next_steps.map((step, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-xs font-mono text-brand-600 mt-0.5 shrink-0">{i + 1}.</span>
                <span className="text-xs text-surface-700">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Confidence */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-surface-500">Confidence:</span>
        <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded border ${conf.bg} ${conf.text} ${conf.border}`}>
          {conf.label}
        </span>
      </div>

      {/* Knowledge Sources */}
      {reasoning.knowledge_citations.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Knowledge Sources</h4>
          <div className="space-y-1.5">
            {reasoning.knowledge_citations.map((cit, i) => (
              <button
                key={i}
                onClick={() => navigate(`/knowledge/${cit.document_id}`)}
                className="w-full text-left p-2 rounded-lg border border-surface-100 hover:border-brand-200 hover:bg-brand-50/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-brand-600">{cit.document_id}</span>
                </div>
                <p className="text-xs text-surface-600 mt-0.5">{cit.document_title}</p>
                <p className="text-[10px] text-surface-400 mt-0.5">Section: {cit.section}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Operational Evidence Indicator */}
      {retrieval.results.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Operational Evidence</h4>
          <div className="space-y-1">
            {retrieval.results.slice(0, 3).map((r, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <svg className="w-3 h-3 text-emerald-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-surface-600">{r.document_title} — {r.section_heading}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Limitations */}
      {reasoning.limitations.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Limitations</h4>
          <div className="space-y-1">
            {reasoning.limitations.map((lim, i) => (
              <div key={i} className="flex items-start gap-2">
                <svg className="w-3 h-3 text-surface-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
                <span className="text-xs text-surface-500">{lim}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Re-analyze */}
      <button
        onClick={onReanalyze}
        className="w-full px-3 py-1.5 text-xs font-medium text-surface-600 bg-surface-50 border border-surface-200 rounded-lg hover:bg-surface-100 transition-colors"
      >
        Re-analyze
      </button>
    </div>
  )
}

function ResolutionPanel({
  resolution,
  status,
  error,
  onRunResolution,
  onReviewDecision,
  reviewDecision,
  evidenceExpanded,
  setEvidenceExpanded,
}: {
  resolution: ResolutionDecision | null
  status: 'idle' | 'loading' | 'done' | 'error'
  error: string | null
  onRunResolution: () => void
  onReviewDecision: (decision: string) => void
  reviewDecision: string | null
  evidenceExpanded: boolean
  setEvidenceExpanded: (v: boolean) => void
}) {
  const navigate = useNavigate()

  const categoryLabels: Record<string, string> = {
    network_investigation: 'Network Investigation',
    incident_review: 'Incident Review',
    customer_troubleshooting: 'Customer Troubleshooting',
    billing_review: 'Billing Review',
    device_diagnostics: 'Device Diagnostics',
    service_configuration_review: 'Service Configuration Review',
    monitoring: 'Monitoring',
    human_escalation: 'Human Escalation',
    insufficient_evidence: 'Insufficient Evidence',
  }

  const categoryIcons: Record<string, string> = {
    network_investigation: 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z',
    incident_review: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
    customer_troubleshooting: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
    billing_review: 'M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z',
    device_diagnostics: 'M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z',
    service_configuration_review: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
    monitoring: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z',
    human_escalation: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    insufficient_evidence: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  }

  const confidenceConfig: Record<string, { bg: string; text: string; border: string; label: string }> = {
    high: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', label: 'HIGH' },
    medium: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', label: 'MEDIUM' },
    low: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', label: 'LOW' },
  }
  const conf = confidenceConfig[resolution?.confidence || 'low'] || confidenceConfig.low

  return (
    <div className="space-y-4">
      {status === 'idle' && (
        <>
          <p className="text-xs text-surface-500">Combine deterministic rules, operational evidence, and grounded AI reasoning into a structured resolution recommendation.</p>
          <button
            onClick={onRunResolution}
            className="w-full px-4 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            Generate Resolution
          </button>
        </>
      )}

      {status === 'loading' && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-brand-600">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span className="text-sm font-medium">Building resolution recommendation...</span>
          </div>
          <div className="text-xs text-surface-400 space-y-1 pl-6">
            <p>Evaluating deterministic rules...</p>
            <p>Running grounded AI analysis...</p>
            <p>Combining evidence sources...</p>
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="space-y-2">
          <div className="px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-xs text-red-700">{error}</p>
          </div>
          <button
            onClick={onRunResolution}
            className="w-full px-3 py-1.5 text-xs font-medium text-brand-600 bg-brand-50 border border-brand-200 rounded-lg hover:bg-brand-100 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {resolution && status === 'done' && (
        <div className="space-y-4">
          {/* Primary Recommendation */}
          <div className={`px-3 py-3 rounded-lg border ${resolution.conflicts.length > 0 ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50 border-emerald-200'}`}>
            <div className="flex items-start gap-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${resolution.conflicts.length > 0 ? 'bg-amber-100' : 'bg-emerald-100'}`}>
                <svg className={`w-4 h-4 ${resolution.conflicts.length > 0 ? 'text-amber-600' : 'text-emerald-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={categoryIcons[resolution.primary_recommendation.category] || categoryIcons.monitoring} />
                </svg>
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-medium text-surface-500 uppercase tracking-wide">{categoryLabels[resolution.primary_recommendation.category] || resolution.primary_recommendation.category}</p>
                <p className="text-sm font-medium text-surface-900 mt-0.5">{resolution.primary_recommendation.action}</p>
              </div>
            </div>
          </div>

          {/* Confidence + Human Review */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-xs text-surface-500">Confidence:</span>
              <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded border ${conf.bg} ${conf.text} ${conf.border}`}>
                {conf.label}
              </span>
            </div>
            {resolution.requires_human_review && (
              <div className="flex items-center gap-1.5 px-2 py-0.5 bg-amber-50 border border-amber-200 rounded">
                <svg className="w-3 h-3 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span className="text-[10px] font-semibold text-amber-700">HUMAN REVIEW REQUIRED</span>
              </div>
            )}
          </div>

          {/* Why SmartResolve recommends this */}
          {resolution.confidence_reasons.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Why SmartResolve recommends this</h4>
              <div className="space-y-1.5">
                {resolution.confidence_reasons.map((reason, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <svg className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-xs text-surface-700">{reason}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Conflicts */}
          {resolution.conflicts.length > 0 && (
            <div className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
              <h4 className="text-xs font-semibold text-amber-700 mb-1">Conflicts Detected</h4>
              {resolution.conflicts.map((c, i) => (
                <p key={i} className="text-xs text-amber-600">{c}</p>
              ))}
            </div>
          )}

          {/* Evidence (expandable) */}
          {resolution.evidence.length > 0 && (
            <div>
              <button
                onClick={() => setEvidenceExpanded(!evidenceExpanded)}
                className="flex items-center gap-2 text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5 hover:text-surface-900"
              >
                <svg className={`w-3 h-3 transition-transform ${evidenceExpanded ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                Evidence ({resolution.evidence.length})
              </button>
              {evidenceExpanded && (
                <div className="space-y-2 mt-2">
                  {resolution.evidence.map((ev, i) => (
                    <div key={i} className="p-2 rounded-lg bg-surface-50 border border-surface-100">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className={`text-[9px] font-semibold uppercase px-1.5 py-0.5 rounded ${
                          ev.type === 'operational' ? 'bg-blue-100 text-blue-700' :
                          ev.type === 'knowledge' ? 'bg-purple-100 text-purple-700' :
                          'bg-surface-200 text-surface-600'
                        }`}>
                          {ev.type}
                        </span>
                        <span className="text-[10px] text-surface-400">{ev.source}</span>
                        {ev.reference && <span className="text-[10px] font-mono text-surface-400">{ev.reference}</span>}
                      </div>
                      <p className="text-xs text-surface-700">{ev.statement}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Deterministic Findings */}
          {resolution.deterministic_findings.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Deterministic Findings</h4>
              <div className="space-y-1">
                {resolution.deterministic_findings.map((f, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-[10px] font-mono text-brand-600 mt-0.5 shrink-0">RULE</span>
                    <span className="text-xs text-surface-700">{f}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Alternative Actions */}
          {resolution.alternative_actions.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Alternative Actions</h4>
              <div className="space-y-1.5">
                {resolution.alternative_actions.map((alt, i) => (
                  <div key={i} className="p-2 rounded-lg border border-surface-100">
                    <p className="text-[10px] font-medium text-surface-500 uppercase">{categoryLabels[alt.category] || alt.category}</p>
                    <p className="text-xs text-surface-700 mt-0.5">{alt.action}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Knowledge Sources */}
          {resolution.knowledge_sources.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Knowledge Sources</h4>
              <div className="space-y-1.5">
                {resolution.knowledge_sources.map((src, i) => (
                  <button
                    key={i}
                    onClick={() => navigate(`/knowledge/${src.document_id}`)}
                    className="w-full text-left p-2 rounded-lg border border-surface-100 hover:border-brand-200 hover:bg-brand-50/30 transition-colors"
                  >
                    <span className="text-xs font-mono text-brand-600">{src.document_id}</span>
                    {src.section && <span className="text-xs text-surface-500 ml-2">/ {src.section}</span>}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* AI Assessment */}
          {resolution.ai_assessment && resolution.ai_assessment.summary && (
            <div>
              <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">AI Assessment</h4>
              <div className="p-2.5 rounded-lg bg-surface-50 border border-surface-100">
                <p className="text-xs text-surface-700 leading-relaxed">{resolution.ai_assessment.summary}</p>
              </div>
            </div>
          )}

          {/* Limitations */}
          {resolution.limitations.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-1.5">Limitations</h4>
              <div className="space-y-1">
                {resolution.limitations.map((lim, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <svg className="w-3 h-3 text-surface-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="text-xs text-surface-500">{lim}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Human Decision Controls */}
          {resolution.requires_human_review && (
            <div className="pt-3 border-t border-surface-100">
              <h4 className="text-xs font-semibold text-surface-700 uppercase tracking-wide mb-2">Human Decision</h4>
              {reviewDecision ? (
                <div className="px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-lg">
                  <p className="text-xs text-emerald-700 font-medium">Decision recorded: {reviewDecision.replace(/_/g, ' ').toUpperCase()}</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => onReviewDecision('approved')}
                    className="px-3 py-2 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => onReviewDecision('needs_information')}
                    className="px-3 py-2 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 transition-colors"
                  >
                    Need Info
                  </button>
                  <button
                    onClick={() => onReviewDecision('escalation_requested')}
                    className="px-3 py-2 text-xs font-medium text-red-700 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors"
                  >
                    Escalate
                  </button>
                  <button
                    onClick={() => onReviewDecision('dismissed')}
                    className="px-3 py-2 text-xs font-medium text-surface-600 bg-surface-50 border border-surface-200 rounded-lg hover:bg-surface-100 transition-colors"
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Regenerate */}
          <button
            onClick={onRunResolution}
            className="w-full px-3 py-1.5 text-xs font-medium text-surface-600 bg-surface-50 border border-surface-200 rounded-lg hover:bg-surface-100 transition-colors"
          >
            Regenerate Resolution
          </button>
        </div>
      )}
    </div>
  )
}

export function CaseDetailPage() {
  const { ticketId } = useParams<{ ticketId: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<CaseInvestigationContext | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [aiResult, setAiResult] = useState<CaseReasoningResponse | null>(null)
  const [aiError, setAiError] = useState<string | null>(null)
  const [aiStatus, setAiStatus] = useState<'idle' | 'analyzing' | 'done' | 'error'>('idle')
  const [resolution, setResolution] = useState<ResolutionDecision | null>(null)
  const [resolutionStatus, setResolutionStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [resolutionError, setResolutionError] = useState<string | null>(null)
  const [reviewDecision, setReviewDecision] = useState<string | null>(null)
  const [evidenceExpanded, setEvidenceExpanded] = useState(false)

  const fetchData = useCallback(async () => {
    if (!ticketId) return
    setLoading(true)
    setError(null)
    try {
      const result = await fetchInvestigation(Number(ticketId))
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load investigation')
    } finally {
      setLoading(false)
    }
  }, [ticketId])

  const runAnalysis = useCallback(async () => {
    if (!ticketId) return
    setAiError(null)
    setAiStatus('analyzing')
    setAiResult(null)
    try {
      const result = await fetchReasoning(Number(ticketId), 'What is the most likely explanation for this case?')
      setAiResult(result)
      setAiStatus('done')
    } catch (err) {
      setAiError(err instanceof Error ? err.message : 'AI analysis failed')
      setAiStatus('error')
    }
  }, [ticketId])

  const runResolution = useCallback(async () => {
    if (!ticketId) return
    setResolutionError(null)
    setResolutionStatus('loading')
    setResolution(null)
    try {
      const result = await fetchResolution(Number(ticketId))
      setResolution(result)
      setResolutionStatus('done')
    } catch (err) {
      setResolutionError(err instanceof Error ? err.message : 'Resolution analysis failed')
      setResolutionStatus('error')
    }
  }, [ticketId])

  const handleReviewDecision = useCallback(async (decision: string) => {
    if (!ticketId || !resolution) return
    try {
      await submitReview(Number(ticketId), decision, `Reviewer selected: ${decision}`)
      setReviewDecision(decision)
    } catch (err) {
      console.error('Failed to submit review:', err)
    }
  }, [ticketId, resolution])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (loading) return <LoadingState message="Loading investigation..." />
  if (error) return <ErrorState message={error} onRetry={fetchData} />
  if (!data) return null

  const { ticket, customer, subscription, network, incidents, ticket_history, interactions, previous_tickets, customer_stats, investigation } = data

  return (
    <div className="space-y-4">
      {/* Back button */}
      <button
        onClick={() => navigate('/cases')}
        className="inline-flex items-center gap-1.5 text-sm text-surface-500 hover:text-surface-700 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Cases
      </button>

      {/* Case Header */}
      <div className="bg-white rounded-xl border border-surface-200 p-4 lg:p-5">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono text-surface-400">{ticket.ticket_number}</span>
              <PriorityBadge priority={ticket.priority} />
              <StatusBadge status={ticket.status} />
            </div>
            <h2 className="text-lg font-semibold text-surface-900 mt-1.5">{ticket.subject}</h2>
            <p className="text-sm text-surface-500 mt-1 max-w-2xl">{ticket.description}</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={fetchData}
              className="px-3 py-1.5 text-xs font-medium text-surface-600 bg-surface-50 border border-surface-200 rounded-lg hover:bg-surface-100 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-3 flex-wrap">
          <span className="text-xs text-surface-500">Category: <span className="font-medium text-surface-700 capitalize">{ticket.category}</span></span>
          <span className="text-xs text-surface-500">Channel: <span className="font-medium text-surface-700 capitalize">{ticket.channel?.replace(/_/g, ' ')}</span></span>
          {ticket.assigned_team && (
            <span className="text-xs text-surface-500">Team: <span className="font-medium text-surface-700">{ticket.assigned_team}</span></span>
          )}
          <span className="text-xs text-surface-500">Created: <span className="font-medium text-surface-700">{formatTimeAgo(ticket.created_at)}</span></span>
          {ticket.updated_at && (
            <span className="text-xs text-surface-500">Updated: <span className="font-medium text-surface-700">{formatTimeAgo(ticket.updated_at)}</span></span>
          )}
        </div>
      </div>

      {/* Readiness */}
      <div className="bg-white rounded-xl border border-surface-200 p-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h3 className="text-sm font-semibold text-surface-900">Investigation Readiness</h3>
          <ReadinessIndicator readiness={investigation.readiness} />
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left column - Customer + Service + Network */}
        <div className="lg:col-span-2 space-y-4">
          {/* Customer Profile */}
          {customer && (
            <PanelCard title="Customer">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
                <div>
                  <FieldRow label="Customer Number" value={customer.customer_number} />
                  <FieldRow label="Name" value={customer.name} />
                  <FieldRow label="Email" value={customer.email} />
                  <FieldRow label="Phone" value={customer.phone} />
                </div>
                <div>
                  <div className="py-1.5">
                    <span className="text-xs text-surface-500">Segment</span>
                    <div className="mt-0.5"><SegmentBadge segment={customer.segment} /></div>
                  </div>
                  <FieldRow label="Account Status" value={customer.status} />
                  <FieldRow label="Active Subscriptions" value={customer_stats.active_subscriptions} />
                  <FieldRow label="Total Tickets" value={customer_stats.total_tickets} />
                </div>
              </div>
            </PanelCard>
          )}

          {/* Service / Subscription */}
          {subscription && (
            <PanelCard title="Service & Subscription">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
                <div>
                  <FieldRow label="Service Number" value={subscription.service_number} />
                  <FieldRow label="Service Type" value={subscription.service_type} />
                  <FieldRow label="Plan" value={subscription.plan_name} />
                  <FieldRow label="Plan Type" value={subscription.plan_type} />
                  <FieldRow label="Monthly Price" value={`₹${subscription.monthly_price}`} />
                </div>
                <div>
                  <FieldRow label="Activation Date" value={subscription.activation_date?.split('T')[0]} />
                  <FieldRow label="Subscription Status" value={subscription.status} />
                  <div className="py-1.5">
                    <span className="text-xs text-surface-500">Data Usage</span>
                    <div className="mt-1">
                      <div className="flex items-baseline gap-1">
                        <span className="text-sm font-medium text-surface-800">{subscription.data_usage_gb} GB</span>
                        <span className="text-xs text-surface-400">/ {subscription.data_limit_gb} GB</span>
                      </div>
                      <div className="w-full h-1.5 bg-surface-100 rounded-full mt-1 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            (subscription.data_usage_gb / subscription.data_limit_gb) > 0.9 ? 'bg-red-400' :
                            (subscription.data_usage_gb / subscription.data_limit_gb) > 0.7 ? 'bg-amber-400' : 'bg-emerald-400'
                          }`}
                          style={{ width: `${Math.min(100, (subscription.data_usage_gb / subscription.data_limit_gb) * 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <FieldRow label="Speed" value={`${subscription.speed_mbps} Mbps`} />
                </div>
              </div>
            </PanelCard>
          )}

          {/* Network Context */}
          {network.site && (
            <PanelCard title="Network Context">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
                <div>
                  <FieldRow label="Site Code" value={network.site.site_code} />
                  <FieldRow label="Site Name" value={network.site.site_name} />
                  <div className="py-1.5">
                    <span className="text-xs text-surface-500">Technology</span>
                    <div className="mt-0.5"><TechBadge technology={network.site.technology} /></div>
                  </div>
                  <FieldRow label="Region" value={network.site.region} />
                  <FieldRow label="City" value={network.site.city} />
                </div>
                <div>
                  <FieldRow label="Status" value={network.site.status} />
                  <div className="py-1.5">
                    <span className="text-xs text-surface-500">Capacity</span>
                    <div className="mt-1">
                      <div className="flex items-baseline gap-1">
                        <span className="text-sm font-medium text-surface-800">{network.site.capacity_percent}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-surface-100 rounded-full mt-1 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            network.site.capacity_percent > 85 ? 'bg-red-400' :
                            network.site.capacity_percent > 65 ? 'bg-amber-400' : 'bg-emerald-400'
                          }`}
                          style={{ width: `${network.site.capacity_percent}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <FieldRow label="Last Maintenance" value={network.site.last_maintenance_at?.split('T')[0]} />
                </div>
              </div>

              {/* Network Events */}
              {network.events.length > 0 && (
                <div className="mt-4 pt-4 border-t border-surface-100">
                  <h4 className="text-xs font-medium text-surface-500 uppercase tracking-wide mb-3">Recent Network Events</h4>
                  <div className="space-y-2">
                    {network.events.map((ev) => (
                      <div key={ev.id} className="flex items-start gap-3 p-2 rounded-lg bg-surface-50">
                        <SeverityIndicator severity={ev.severity} />
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-surface-800">{ev.title}</p>
                          <p className="text-[10px] text-surface-500 mt-0.5">{formatTimeAgo(ev.started_at)} · {ev.status}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {network.events.length === 0 && (
                <div className="mt-4 pt-4 border-t border-surface-100">
                  <p className="text-xs text-surface-400">No recent network events at serving site.</p>
                </div>
              )}
            </PanelCard>
          )}

          {!network.site && !subscription && (
            <PanelCard title="Network Context">
              <p className="text-sm text-surface-500">Network context unavailable.</p>
            </PanelCard>
          )}

          {/* Active Incidents */}
          <PanelCard title="Active Incidents">
            {incidents.length > 0 ? (
              <div className="space-y-3">
                {incidents.map((inc) => (
                  <div key={inc.id} className="border border-surface-100 rounded-lg p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono text-surface-400">{inc.incident_number}</span>
                          <SeverityIndicator severity={inc.severity} />
                          <StatusBadge status={inc.status} />
                        </div>
                        <p className="text-sm font-medium text-surface-800 mt-1">{inc.title}</p>
                        <p className="text-xs text-surface-500 mt-0.5">{inc.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 mt-2 text-[10px] text-surface-400">
                      <span>{inc.region} region</span>
                      <span>{inc.affected_service}</span>
                      <span>{inc.affected_customers_estimate.toLocaleString()} estimated affected</span>
                      <span>{formatTimeAgo(inc.started_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-surface-500">No active incident currently linked to this case.</p>
            )}
          </PanelCard>

          {/* Previous Tickets */}
          {previous_tickets.length > 0 && (
            <PanelCard title={`Previous Tickets (${previous_tickets.length})`}>
              {investigation.same_category_previous_tickets > 0 && (
                <div className="mb-3 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-xs text-amber-700">
                    {investigation.same_category_previous_tickets} previous {ticket.category} ticket(s) found for this customer.
                  </p>
                </div>
              )}
              <div className="space-y-2">
                {previous_tickets.map((pt) => (
                  <div key={pt.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-surface-50">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-surface-400">{pt.ticket_number}</span>
                        <PriorityBadge priority={pt.priority} />
                        <StatusBadge status={pt.status} />
                      </div>
                      <p className="text-xs text-surface-700 mt-0.5 truncate max-w-md">{pt.subject}</p>
                      <div className="flex items-center gap-2 mt-0.5 text-[10px] text-surface-400">
                        <span className="capitalize">{pt.category}</span>
                        <span>{formatTimeAgo(pt.created_at)}</span>
                        {pt.resolved_at && <span>Resolved {formatTimeAgo(pt.resolved_at)}</span>}
                      </div>
                    </div>
                    <button
                      onClick={() => navigate(`/cases/${pt.id}`)}
                      className="shrink-0 text-xs text-brand-600 hover:text-brand-700 font-medium ml-2"
                    >
                      View
                    </button>
                  </div>
                ))}
              </div>
            </PanelCard>
          )}
        </div>

        {/* Right column - Investigation Summary + AI + Timeline + Interactions */}
        <div className="space-y-4">
          {/* AI Investigation Panel */}
          <PanelCard title="AI Investigation" className="border-brand-200">
            <div className="space-y-3">
              <p className="text-xs text-surface-500">Analyze this case using operational data and telecom knowledge.</p>

              {aiStatus === 'idle' && (
                <button
                  onClick={runAnalysis}
                  className="w-full px-4 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Analyze Case
                </button>
              )}

              {aiStatus === 'analyzing' && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-brand-600">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span className="text-sm font-medium">Analyzing operational evidence...</span>
                  </div>
                  <div className="text-xs text-surface-400 space-y-1 pl-6">
                    <p>Retrieving relevant procedures...</p>
                    <p>Generating grounded assessment...</p>
                  </div>
                </div>
              )}

              {aiStatus === 'error' && (
                <div className="space-y-2">
                  <div className="px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-xs text-red-700">{aiError}</p>
                  </div>
                  <button
                    onClick={runAnalysis}
                    className="w-full px-3 py-1.5 text-xs font-medium text-brand-600 bg-brand-50 border border-brand-200 rounded-lg hover:bg-brand-100 transition-colors"
                  >
                    Retry Analysis
                  </button>
                </div>
              )}

              {aiResult && aiStatus === 'done' && (
                <AiResultPanel result={aiResult} onReanalyze={runAnalysis} />
              )}
            </div>
          </PanelCard>

          {/* Resolution Recommendation Panel */}
          <PanelCard title="Resolution Recommendation" className="border-brand-200">
            <ResolutionPanel
              resolution={resolution}
              status={resolutionStatus}
              error={resolutionError}
              onRunResolution={runResolution}
              onReviewDecision={handleReviewDecision}
              reviewDecision={reviewDecision}
              evidenceExpanded={evidenceExpanded}
              setEvidenceExpanded={setEvidenceExpanded}
            />
          </PanelCard>

          {/* Investigation Summary */}
          <PanelCard title="Investigation Summary">
            <div className="space-y-1">
              <FieldRow label="Customer" value={customer ? `${customer.name} (${customer.customer_number})` : 'Not found'} />
              <FieldRow label="Issue" value={ticket.subject} />
              <FieldRow label="Service" value={subscription ? `${subscription.plan_name} ${subscription.service_type}` : 'Not linked'} />
              <FieldRow label="Network Site" value={network.site ? network.site.site_code : 'Not available'} />
              <FieldRow label="Network Status" value={network.site ? network.site.status : 'Not available'} />
              <FieldRow label="Active Network Events" value={network.events.filter(e => e.status === 'active').length} />
              <FieldRow label="Regional Incidents" value={incidents.length} />
              <FieldRow label="Previous Related Tickets" value={investigation.same_category_previous_tickets} />
            </div>
          </PanelCard>

          {/* Known Information */}
          <PanelCard title="Known Information">
            <div className="space-y-1.5">
              {investigation.known_facts.map((fact, i) => (
                <div key={i} className="flex items-start gap-2">
                  <svg className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-xs text-surface-700">{fact}</span>
                </div>
              ))}
            </div>
          </PanelCard>

          {/* Missing Information */}
          <PanelCard title="Missing / Unverified Information">
            <div className="space-y-1.5">
              {investigation.missing_information.map((info, i) => (
                <div key={i} className="flex items-start gap-2">
                  <svg className="w-3.5 h-3.5 text-surface-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span className="text-xs text-surface-500">{info}</span>
                </div>
              ))}
            </div>
          </PanelCard>

          {/* Ticket Timeline */}
          <PanelCard title="Ticket History">
            {ticket_history.length > 0 ? (
              <div className="space-y-0">
                {ticket_history.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()).map((event, i) => (
                  <TimelineItem key={event.id} event={event} isLast={i === ticket_history.length - 1} />
                ))}
              </div>
            ) : (
              <p className="text-xs text-surface-400">No ticket history available.</p>
            )}
          </PanelCard>

          {/* Customer Interactions */}
          <PanelCard title={`Customer Interactions (${interactions.length})`}>
            {interactions.length > 0 ? (
              <div className="space-y-3">
                {interactions.map((inter) => (
                  <div key={inter.id} className="flex items-start gap-3">
                    <InteractionIcon type={inter.interaction_type} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-medium text-surface-500 uppercase">{inter.interaction_type}</span>
                        <span className="text-[10px] text-surface-400">{formatTimeAgo(inter.created_at)}</span>
                      </div>
                      <p className="text-xs text-surface-700 mt-0.5">{inter.summary}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-surface-400">No customer interactions recorded.</p>
            )}
          </PanelCard>
        </div>
      </div>
    </div>
  )
}
