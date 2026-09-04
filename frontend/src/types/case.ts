export type CaseTicket = {
  id: number
  ticket_number: string
  customer_id: number
  subscription_id: number | null
  category: string
  priority: string
  subject: string
  description: string
  status: string
  channel: string
  assigned_team: string | null
  created_at: string
  updated_at: string
  resolved_at: string | null
  customer_name: string | null
  customer_number: string | null
  customer_phone: string | null
  customer_email: string | null
  service_number: string | null
  service_type: string | null
  plan_name: string | null
}

export type CaseCustomer = {
  id: number
  customer_number: string
  name: string
  email: string
  phone: string
  segment: string
  status: string
  created_at: string
}

export type CaseSubscription = {
  id: number
  customer_id: number
  plan_id: number
  service_number: string
  service_type: string
  activation_date: string
  status: string
  network_site_id: number
  data_usage_gb: number
  billing_cycle_day: number
  plan_name: string
  plan_code: string
  plan_type: string
  monthly_price: number
  data_limit_gb: number
  voice_minutes: number
  sms_limit: number
  speed_mbps: number
  site_code: string
  site_name: string
  technology: string
  region: string
  city: string
  capacity_percent: number
  site_status: string
  last_maintenance_at: string | null
}

export type CaseNetworkSite = {
  id: number
  site_code: string
  site_name: string
  technology: string
  region: string
  city: string
  latitude: number
  longitude: number
  capacity_percent: number
  status: string
  last_maintenance_at: string | null
}

export type CaseNetworkEvent = {
  id: number
  site_id: number
  event_type: string
  severity: string
  title: string
  description: string
  started_at: string
  resolved_at: string | null
  status: string
  site_code: string | null
  site_name: string | null
}

export type CaseIncident = {
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

export type CaseTicketHistory = {
  id: number
  ticket_id: number
  event_type: string
  actor_type: string
  description: string
  created_at: string
}

export type CaseInteraction = {
  id: number
  customer_id: number
  ticket_id: number | null
  interaction_type: string
  summary: string
  sentiment: string
  created_at: string
  ticket_number: string | null
}

export type CasePreviousTicket = {
  id: number
  ticket_number: string
  subject: string
  category: string
  priority: string
  status: string
  created_at: string
  resolved_at: string | null
  assigned_team: string | null
}

export type CaseCustomerStats = {
  active_subscriptions: number
  total_tickets: number
  total_interactions: number
}

export type CaseInvestigationResult = {
  readiness: 'READY' | 'PARTIAL' | 'INSUFFICIENT DATA'
  known_facts: string[]
  missing_information: string[]
  same_category_previous_tickets: number
}

export type CaseInvestigationContext = {
  ticket: CaseTicket
  customer: CaseCustomer | null
  subscription: CaseSubscription | null
  previous_tickets: CasePreviousTicket[]
  network: {
    site: CaseNetworkSite | null
    events: CaseNetworkEvent[]
  }
  incidents: CaseIncident[]
  ticket_history: CaseTicketHistory[]
  interactions: CaseInteraction[]
  customer_stats: CaseCustomerStats
  investigation: CaseInvestigationResult
}
