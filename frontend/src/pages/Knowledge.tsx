import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import type { KnowledgeDocumentSummary, KnowledgeCategoryInfo, KnowledgeSearchResult } from '../types/knowledge'

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

export function KnowledgePage() {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState<KnowledgeDocumentSummary[]>([])
  const [categories, setCategories] = useState<KnowledgeCategoryInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)

  useEffect(() => {
    Promise.all([
      fetch('/api/knowledge').then(r => r.json()),
      fetch('/api/knowledge/categories').then(r => r.json()),
    ]).then(([docs, cats]) => {
      setDocuments(docs.data || [])
      setCategories(cats.data || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      setIsSearching(false)
      return
    }
    const timer = setTimeout(() => {
      setIsSearching(true)
      const params = new URLSearchParams({ q: searchQuery })
      if (selectedCategory) params.set('category', selectedCategory)
      fetch(`/api/knowledge/search?${params.toString()}`)
        .then(r => r.json())
        .then(d => { setSearchResults(d.results || []); setIsSearching(false) })
        .catch(() => setIsSearching(false))
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery, selectedCategory])

  const filteredDocs = selectedCategory && !searchQuery
    ? documents.filter(d => d.category === selectedCategory)
    : documents

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-surface-900">Knowledge Base</h2>
        <p className="text-sm text-surface-500 mt-0.5">Telecom policies, runbooks, and operational procedures</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search knowledge base..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-3 py-2 text-sm border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-3 py-2 text-sm border border-surface-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All Categories</option>
          {categories.map(c => (
            <option key={c.category} value={c.category}>{CATEGORY_LABELS[c.category] || c.category} ({c.count})</option>
          ))}
        </select>
      </div>

      {searchQuery && (
        <div className="bg-white rounded-xl border border-surface-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-surface-700">
              Search Results for "{searchQuery}"
              {searchResults.length > 0 && (
                <span className="text-surface-400 ml-2">({searchResults.length} matches)</span>
              )}
            </h3>
          </div>
          {isSearching && <div className="text-sm text-surface-400">Searching...</div>}
          {!isSearching && searchResults.length === 0 && (
            <div className="text-sm text-surface-500">No results found</div>
          )}
          <div className="space-y-3">
            {searchResults.map(r => (
              <button
                key={r.id}
                onClick={() => navigate(`/knowledge/${r.id}`)}
                className="w-full text-left p-3 rounded-lg border border-surface-100 hover:border-brand-200 hover:bg-brand-50/30 transition-colors"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded border ${CATEGORY_COLORS[r.category] || 'bg-surface-50 text-surface-600 border-surface-200'}`}>
                    {CATEGORY_LABELS[r.category] || r.category}
                  </span>
                  <span className="text-xs text-surface-400">Score: {r.score}</span>
                </div>
                <p className="text-sm font-medium text-surface-900">{r.title}</p>
                {r.matching_chunks.length > 0 && (
                  <p className="text-xs text-surface-500 mt-1">
                    <span className="font-medium">{r.matching_chunks[0].section_heading}:</span>{' '}
                    {r.matching_chunks[0].preview}
                  </p>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div className="bg-white rounded-xl border border-surface-200 p-8 text-center">
          <div className="text-sm text-surface-400">Loading knowledge base...</div>
        </div>
      )}

      {!loading && !searchQuery && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {categories.map(c => (
              <button
                key={c.category}
                onClick={() => setSelectedCategory(selectedCategory === c.category ? '' : c.category)}
                className={`p-3 rounded-xl border text-left transition-colors ${
                  selectedCategory === c.category
                    ? 'border-brand-300 bg-brand-50'
                    : 'border-surface-200 bg-white hover:border-surface-300'
                }`}
              >
                <div className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded border mb-2 ${CATEGORY_COLORS[c.category] || 'bg-surface-50 text-surface-600 border-surface-200'}`}>
                  {CATEGORY_LABELS[c.category] || c.category}
                </div>
                <div className="text-lg font-semibold text-surface-900">{c.count}</div>
                <div className="text-xs text-surface-500">documents</div>
              </button>
            ))}
          </div>

          <div className="bg-white rounded-xl border border-surface-200">
            <div className="divide-y divide-surface-100">
              {filteredDocs.length === 0 && (
                <div className="p-8 text-center text-sm text-surface-400">No documents found</div>
              )}
              {filteredDocs.map(doc => (
                <button
                  key={doc.id}
                  onClick={() => navigate(`/knowledge/${doc.id}`)}
                  className="w-full px-5 py-3 text-left hover:bg-surface-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded border ${CATEGORY_COLORS[doc.category] || 'bg-surface-50 text-surface-600 border-surface-200'}`}>
                          {CATEGORY_LABELS[doc.category] || doc.category}
                        </span>
                        <span className="text-xs text-surface-400">{doc.sections_count} sections</span>
                      </div>
                      <p className="text-sm font-medium text-surface-900 truncate">{doc.title}</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {doc.tags.slice(0, 5).map(tag => (
                          <span key={tag} className="text-[10px] text-surface-400 bg-surface-50 px-1.5 py-0.5 rounded">{tag}</span>
                        ))}
                        {doc.tags.length > 5 && (
                          <span className="text-[10px] text-surface-400">+{doc.tags.length - 5}</span>
                        )}
                      </div>
                    </div>
                    <svg className="w-4 h-4 text-surface-300 shrink-0 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
