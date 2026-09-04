export type DashboardMetrics = {
  open_tickets: number
  high_priority_tickets: number
  active_incidents: number
  network_sites: number
  affected_customers: number
  total_customers: number
}

export type TicketBreakdown = {
  by_status: Record<string, number>
  by_priority: Record<string, number>
  by_category: Record<string, number>
}

export type NetworkHealth = {
  total: number
  operational: number
  degraded: number
  maintenance: number
  offline: number
  status: 'healthy' | 'degraded' | 'critical'
  active_events: number
}

export type RegionalImpact = {
  region: string
  open_tickets: number
  active_incidents: number
  affected_customers: number
}

export type ActiveIncidentSummary = {
  id: number
  incident_number: string
  title: string
  description: string
  affected_service: string
  severity: string
  region: string
  started_at: string
  resolved_at: string | null
  status: string
  affected_customers_estimate: number
}

export type PriorityCase = {
  ticket_number: string
  customer_name: string
  customer_number: string
  subject: string
  priority: string
  status: string
  region: string
  reasons: string[]
  score: number
  created_at: string
}

export type RecentActivity = {
  type: 'ticket_event' | 'incident' | 'network_event'
  timestamp: string
  description: string
  related_id: string
  event_type: string
}

export type DashboardOverview = {
  metrics: DashboardMetrics
  ticket_breakdown: TicketBreakdown
  network_health: NetworkHealth
  regional_impact: RegionalImpact[]
  active_incidents: ActiveIncidentSummary[]
  priority_cases: PriorityCase[]
  recent_activity: RecentActivity[]
}

export type Customer = {
  id: number
  customer_number: string
  name: string
  email: string
  phone: string
  segment: string
  status: string
  created_at: string
}

export type Ticket = {
  id: number
  ticket_number: string
  subject: string
  category: string
  priority: string
  status: string
  customer_name: string
  created_at: string
}

export type Incident = {
  id: number
  incident_number: string
  title: string
  severity: string
  status: string
  region: string
  affected_customers_estimate: number
  started_at: string
}

export type NetworkSite = {
  id: number
  site_code: string
  site_name: string
  technology: string
  region: string
  city: string
  capacity_percent: number
  status: string
}
