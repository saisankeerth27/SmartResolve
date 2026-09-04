import type { CaseInvestigationContext } from '../types/case'

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
