import type { CaseInvestigationContext } from '../types/case'
import type { CaseReasoningResponse } from '../types/case'
import type { ResolutionDecision, ReviewState } from '../types/case'

export async function fetchApi<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export async function fetchInvestigation(ticketId: number): Promise<CaseInvestigationContext> {
  return fetchApi<CaseInvestigationContext>(`/api/cases/${ticketId}/investigation`)
}

export async function fetchReasoning(ticketId: number, question: string): Promise<CaseReasoningResponse> {
  const response = await fetch(`/api/cases/${ticketId}/reason`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export async function fetchResolution(ticketId: number, question?: string): Promise<ResolutionDecision> {
  const response = await fetch(`/api/cases/${ticketId}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: question || undefined }),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export async function fetchReviewStates(ticketId: number): Promise<ReviewState[]> {
  return fetchApi<ReviewState[]>(`/api/cases/${ticketId}/review`)
}

export async function submitReview(ticketId: number, decision: string, reason?: string): Promise<ReviewState> {
  const response = await fetch(`/api/cases/${ticketId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, reason: reason || '' }),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}
