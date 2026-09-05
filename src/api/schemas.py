from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    gemini_configured: bool
    faiss_loaded: bool = False
    faiss_vectors: int = 0


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class CustomerResponse(BaseModel):
    id: int
    customer_number: str
    name: str
    email: str
    phone: str
    segment: str
    status: str
    created_at: str


class CustomerListResponse(BaseModel):
    data: list[CustomerResponse]
    pagination: PaginationMeta


class SubscriptionResponse(BaseModel):
    id: int
    customer_id: int
    plan_id: int
    service_number: str
    service_type: str
    activation_date: str
    status: str
    network_site_id: int
    data_usage_gb: float
    billing_cycle_day: int
    plan_name: str
    plan_code: str
    monthly_price: float
    data_limit_gb: int
    site_name: str
    site_code: str
    technology: str
    region: str
    city: str


class PlanResponse(BaseModel):
    id: int
    plan_code: str
    plan_name: str
    plan_type: str
    monthly_price: float
    data_limit_gb: int
    voice_minutes: int
    sms_limit: int
    speed_mbps: int
    roaming_enabled: int
    status: str


class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    subscription_id: int | None
    category: str
    priority: str
    subject: str
    description: str
    status: str
    channel: str
    assigned_team: str | None
    created_at: str
    updated_at: str
    resolved_at: str | None
    customer_name: str | None = None
    customer_number: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None
    service_number: str | None = None
    service_type: str | None = None
    plan_name: str | None = None
    archived: bool = False


class TicketListResponse(BaseModel):
    data: list[TicketResponse]
    pagination: PaginationMeta


class TicketEventResponse(BaseModel):
    id: int
    ticket_id: int
    event_type: str
    actor_type: str
    description: str
    created_at: str


class TicketDetailResponse(TicketResponse):
    history: list[TicketEventResponse]


class NetworkSiteResponse(BaseModel):
    id: int
    site_code: str
    site_name: str
    technology: str
    region: str
    city: str
    latitude: float
    longitude: float
    capacity_percent: int
    status: str
    last_maintenance_at: str | None


class NetworkSiteListResponse(BaseModel):
    data: list[NetworkSiteResponse]
    pagination: PaginationMeta


class NetworkEventResponse(BaseModel):
    id: int
    site_id: int
    event_type: str
    severity: str
    title: str
    description: str
    started_at: str
    resolved_at: str | None
    status: str
    site_code: str | None = None
    site_name: str | None = None


class NetworkEventListResponse(BaseModel):
    data: list[NetworkEventResponse]
    pagination: PaginationMeta


class IncidentResponse(BaseModel):
    id: int
    incident_number: str
    title: str
    description: str
    affected_service: str
    severity: str
    region: str
    started_at: str
    resolved_at: str | None
    status: str
    affected_customers_estimate: int


class IncidentListResponse(BaseModel):
    data: list[IncidentResponse]
    pagination: PaginationMeta


class CustomerInteractionResponse(BaseModel):
    id: int
    customer_id: int
    ticket_id: int | None
    interaction_type: str
    summary: str
    sentiment: str
    created_at: str
    ticket_number: str | None = None


class CustomerInteractionListResponse(BaseModel):
    data: list[CustomerInteractionResponse]
    pagination: PaginationMeta


class DashboardStatsResponse(BaseModel):
    total_customers: int
    open_tickets: int
    active_incidents: int
    total_network_sites: int
    active_network_events: int
    ticket_status_counts: dict
    incident_status_counts: dict
    site_status_counts: dict


# ── Dashboard Overview Schemas ───────────────────────────

class DashboardMetrics(BaseModel):
    open_tickets: int
    high_priority_tickets: int
    active_incidents: int
    network_sites: int
    affected_customers: int
    total_customers: int


class TicketBreakdown(BaseModel):
    by_status: dict
    by_priority: dict
    by_category: dict


class NetworkHealth(BaseModel):
    total: int
    operational: int
    degraded: int
    maintenance: int
    offline: int
    status: str
    active_events: int


class RegionalImpact(BaseModel):
    region: str
    open_tickets: int
    active_incidents: int
    affected_customers: int


class ActiveIncidentSummary(BaseModel):
    id: int
    incident_number: str
    title: str
    description: str
    affected_service: str
    severity: str
    region: str
    started_at: str
    resolved_at: str | None
    status: str
    affected_customers_estimate: int


class PriorityCase(BaseModel):
    ticket_number: str
    customer_name: str
    customer_number: str
    subject: str
    priority: str
    status: str
    region: str
    reasons: list[str]
    score: int
    created_at: str


class RecentActivity(BaseModel):
    type: str
    timestamp: str
    description: str
    related_id: str
    event_type: str


class DashboardOverviewResponse(BaseModel):
    metrics: DashboardMetrics
    ticket_breakdown: TicketBreakdown
    network_health: NetworkHealth
    regional_impact: list[RegionalImpact]
    active_incidents: list[ActiveIncidentSummary]
    priority_cases: list[PriorityCase]
    recent_activity: list[RecentActivity]


# ── Case Investigation Schemas ─────────────────────────

class InvestigationSubscription(BaseModel):
    id: int
    customer_id: int
    plan_id: int
    service_number: str
    service_type: str
    activation_date: str
    status: str
    network_site_id: int
    data_usage_gb: float
    billing_cycle_day: int
    plan_name: str
    plan_code: str
    plan_type: str
    monthly_price: float
    data_limit_gb: int
    voice_minutes: int
    sms_limit: int
    speed_mbps: int
    site_code: str
    site_name: str
    technology: str
    region: str
    city: str
    capacity_percent: int
    site_status: str
    last_maintenance_at: str | None


class InvestigationNetworkSite(BaseModel):
    id: int
    site_code: str
    site_name: str
    technology: str
    region: str
    city: str
    latitude: float
    longitude: float
    capacity_percent: int
    status: str
    last_maintenance_at: str | None


class InvestigationNetworkEvent(BaseModel):
    id: int
    site_id: int
    event_type: str
    severity: str
    title: str
    description: str
    started_at: str
    resolved_at: str | None
    status: str
    site_code: str | None = None
    site_name: str | None = None


class InvestigationIncident(BaseModel):
    id: int
    incident_number: str
    title: str
    description: str
    affected_service: str
    severity: str
    region: str
    started_at: str
    resolved_at: str | None
    status: str
    affected_customers_estimate: int


class InvestigationTicketHistory(BaseModel):
    id: int
    ticket_id: int
    event_type: str
    actor_type: str
    description: str
    created_at: str


class InvestigationInteraction(BaseModel):
    id: int
    customer_id: int
    ticket_id: int | None
    interaction_type: str
    summary: str
    sentiment: str
    created_at: str
    ticket_number: str | None = None


class PreviousTicket(BaseModel):
    id: int
    ticket_number: str
    subject: str
    category: str
    priority: str
    status: str
    created_at: str
    resolved_at: str | None
    assigned_team: str | None


class CustomerStats(BaseModel):
    active_subscriptions: int
    total_tickets: int
    total_interactions: int


class InvestigationResult(BaseModel):
    readiness: str
    known_facts: list[str]
    missing_information: list[str]
    same_category_previous_tickets: int


class InvestigationContext(BaseModel):
    ticket: TicketResponse
    customer: CustomerResponse | None
    subscription: InvestigationSubscription | None
    previous_tickets: list[PreviousTicket]
    network: dict
    incidents: list[InvestigationIncident]
    ticket_history: list[InvestigationTicketHistory]
    interactions: list[InvestigationInteraction]
    customer_stats: CustomerStats
    investigation: InvestigationResult


# ── Knowledge Base Schemas ──────────────────────────────

class KnowledgeChunkPreview(BaseModel):
    chunk_id: str
    section_heading: str
    preview: str
    score: int


class KnowledgeSearchResult(BaseModel):
    id: str
    title: str
    category: str
    score: int
    matching_chunks: list[KnowledgeChunkPreview]
    preview: str


class KnowledgeSearchResponse(BaseModel):
    query: str
    category: str | None
    results: list[KnowledgeSearchResult]
    total: int


class KnowledgeDocumentSummary(BaseModel):
    id: str
    title: str
    category: str
    tags: list[str]
    path: str
    sections_count: int


class KnowledgeDocumentListResponse(BaseModel):
    data: list[KnowledgeDocumentSummary]
    total: int


class KnowledgeSection(BaseModel):
    heading: str
    content: str


class KnowledgeDocumentDetail(BaseModel):
    id: str
    title: str
    category: str
    tags: list[str]
    path: str
    content: str
    sections: list[KnowledgeSection]


class KnowledgeCategoryInfo(BaseModel):
    category: str
    count: int


class KnowledgeCategoryListResponse(BaseModel):
    data: list[KnowledgeCategoryInfo]
    total: int


class KnowledgeChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    category: str
    section_heading: str
    chunk_index: int
    content: str
    word_count: int


class KnowledgeChunkListResponse(BaseModel):
    document_id: str
    chunks: list[KnowledgeChunk]
    total: int


# ── AI Reasoning Schemas ────────────────────────────────

class PossibleCauseSchema(BaseModel):
    cause: str
    evidence: list[str]


class KnowledgeCitationSchema(BaseModel):
    document_id: str
    document_title: str
    section: str


class AIReasoningResultSchema(BaseModel):
    status: str
    summary: str
    possible_causes: list[PossibleCauseSchema]
    recommended_next_steps: list[str]
    knowledge_citations: list[KnowledgeCitationSchema]
    limitations: list[str]
    confidence: str


class RetrievalResultSchema(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    section_heading: str
    content: str
    score: float


class RetrievalInfoSchema(BaseModel):
    status: str
    query: str
    results: list[RetrievalResultSchema]
    total: int


class CaseReasoningRequest(BaseModel):
    question: str = "What is the most likely explanation for this case?"


class CaseReasoningResponse(BaseModel):
    case_id: str
    retrieval: RetrievalInfoSchema
    reasoning: AIReasoningResultSchema


# ── Resolution Decision Schemas ─────────────────────────

class ResolutionRecommendation(BaseModel):
    category: str
    action: str


class ResolutionEvidence(BaseModel):
    type: str
    source: str
    reference: str
    statement: str


class ResolutionKnowledgeSource(BaseModel):
    document_id: str
    section: str


class ResolutionAIAssessment(BaseModel):
    summary: str | None = None
    confidence: str | None = None
    status: str | None = None


class ResolutionDecision(BaseModel):
    case_id: str
    decision_status: str
    primary_recommendation: ResolutionRecommendation
    alternative_actions: list[ResolutionRecommendation]
    deterministic_findings: list[str]
    ai_assessment: ResolutionAIAssessment | None = None
    evidence: list[ResolutionEvidence]
    knowledge_sources: list[ResolutionKnowledgeSource]
    confidence: str
    confidence_reasons: list[str]
    limitations: list[str]
    conflicts: list[str]
    requires_human_review: bool
    review_reasons: list[str] = []


class CaseResolveRequest(BaseModel):
    question: str | None = "What is the recommended next action for this case?"


class ReviewStateCreate(BaseModel):
    decision: str
    reason: str | None = ""


class ReviewStateResponse(BaseModel):
    id: int
    ticket_id: int
    recommendation_category: str | None
    recommendation_action: str | None
    confidence: str | None
    reviewer_decision: str | None
    reason: str | None
    created_at: str
    updated_at: str
