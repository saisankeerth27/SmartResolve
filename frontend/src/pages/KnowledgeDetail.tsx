import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { KnowledgeDocumentDetail } from '../types/knowledge'

const CATEGORY_COLORS: Record<string, string> = {
  network: 'bg-blue-50 text-blue-700 border-blue-200',
  connectivity: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  billing: 'bg-amber-50 text-amber-700 border-amber-200',
  roaming: 'bg-purple-50 text-purple-700 border-purple-200',
  device: 'bg-rose-50 text-rose-700 border-rose-200',
  support: 'bg-teal-50 text-teal-700 border-teal-200',
  escalation: 'bg-orange-50 text-orange-700 border-orange-200',
  enterprise: 'bg-indigo-50 text-indigo-700 border-indigo-200',
}

const CATEGORY_LABELS: Record<string, string> = {
  network: 'Network',
  connectivity: 'Connectivity',
  billing: 'Billing',
  roaming: 'Roaming',
  device: 'Device',
  support: 'Support',
  escalation: 'Escalation',
  enterprise: 'Enterprise',
}

export function KnowledgeDetailPage() {
  const { id: documentId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [doc, setDoc] = useState<KnowledgeDocumentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeSection, setActiveSection] = useState(0)

  useEffect(() => {
    if (!documentId) return
    setLoading(true)
    fetch(`/api/knowledge/${documentId}`)
      .then(r => {
        if (!r.ok) throw new Error('Document not found')
        return r.json()
      })
      .then(d => { setDoc(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [documentId])

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="bg-white rounded-xl border border-surface-200 p-8 text-center">
          <div className="text-sm text-surface-400">Loading document...</div>
        </div>
      </div>
    )
  }

  if (error || !doc) {
    return (
      <div className="space-y-4">
        <div className="bg-white rounded-xl border border-surface-200 p-8 text-center">
          <div className="text-sm text-surface-500">{error || 'Document not found'}</div>
          <button onClick={() => navigate('/knowledge')} className="mt-3 text-sm text-brand-600 hover:text-brand-700">
            Back to Knowledge Base
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <button
          onClick={() => navigate('/knowledge')}
          className="p-1.5 rounded-lg hover:bg-surface-100 text-surface-500"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded border ${CATEGORY_COLORS[doc.category] || 'bg-surface-50 text-surface-600 border-surface-200'}`}>
          {CATEGORY_LABELS[doc.category] || doc.category}
        </span>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-surface-900">{doc.title}</h2>
        <div className="flex flex-wrap gap-1.5 mt-2">
          {doc.tags.map(tag => (
            <span key={tag} className="text-xs text-surface-500 bg-surface-100 px-2 py-0.5 rounded">{tag}</span>
          ))}
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-4">
        <nav className="lg:w-56 shrink-0">
          <div className="bg-white rounded-xl border border-surface-200 p-3 sticky top-4">
            <h3 className="text-xs font-medium text-surface-500 uppercase tracking-wider mb-2 px-1">Contents</h3>
            <div className="space-y-0.5">
              {doc.sections.map((section, i) => (
                <button
                  key={i}
                  onClick={() => setActiveSection(i)}
                  className={`w-full text-left px-2 py-1.5 text-xs rounded-md transition-colors ${
                    activeSection === i
                      ? 'bg-brand-50 text-brand-700 font-medium'
                      : 'text-surface-600 hover:bg-surface-50'
                  }`}
                >
                  {section.heading || 'Overview'}
                </button>
              ))}
            </div>
          </div>
        </nav>

        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-xl border border-surface-200">
            <div className="p-5">
              <h3 className="text-sm font-semibold text-surface-900 mb-3">
                {doc.sections[activeSection]?.heading || 'Overview'}
              </h3>
              <div className="prose prose-sm max-w-none text-surface-700">
                {doc.sections[activeSection]?.content.split('\n\n').map((paragraph, pi) => {
                  const trimmed = paragraph.trim()
                  if (!trimmed) return null
                  if (trimmed.startsWith('### ')) {
                    return (
                      <h4 key={pi} className="text-sm font-semibold text-surface-800 mt-4 mb-2">
                        {trimmed.replace(/^###\s+/, '')}
                      </h4>
                    )
                  }
                  if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                    const items = trimmed.split('\n').filter(l => l.trim().startsWith('- ') || l.trim().startsWith('* '))
                    return (
                      <ul key={pi} className="list-disc list-inside space-y-1 my-2">
                        {items.map((item, ii) => (
                          <li key={ii} className="text-sm">{item.replace(/^[-*]\s+/, '')}</li>
                        ))}
                      </ul>
                    )
                  }
                  if (/^\d+\.\s/.test(trimmed)) {
                    const items = trimmed.split('\n').filter(l => /^\d+\.\s/.test(l.trim()))
                    return (
                      <ol key={pi} className="list-decimal list-inside space-y-1 my-2">
                        {items.map((item, ii) => (
                          <li key={ii} className="text-sm">{item.replace(/^\d+\.\s+/, '')}</li>
                        ))}
                      </ol>
                    )
                  }
                  return (
                    <p key={pi} className="text-sm leading-relaxed my-2">{trimmed}</p>
                  )
                })}
              </div>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-surface-400">
            <span>{doc.sections.length} sections</span>
            <span>{doc.path}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
