export type KnowledgeDocumentSummary = {
  id: string
  title: string
  category: string
  tags: string[]
  path: string
  sections_count: number
}

export type KnowledgeCategoryInfo = {
  category: string
  count: number
}

export type KnowledgeSection = {
  heading: string
  content: string
}

export type KnowledgeDocumentDetail = {
  id: string
  title: string
  category: string
  tags: string[]
  path: string
  content: string
  sections: KnowledgeSection[]
}

export type KnowledgeSearchResult = {
  id: string
  title: string
  category: string
  score: number
  matching_chunks: {
    chunk_id: string
    section_heading: string
    preview: string
    score: number
  }[]
  preview: string
}

export type KnowledgeSearchResponse = {
  query: string
  category: string | null
  results: KnowledgeSearchResult[]
  total: number
}

export type KnowledgeDocumentListResponse = {
  data: KnowledgeDocumentSummary[]
  total: number
}

export type KnowledgeCategoryListResponse = {
  data: KnowledgeCategoryInfo[]
  total: number
}
