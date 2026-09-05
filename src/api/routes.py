import logging
import math
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from src.api.schemas import (
    HealthResponse,
    PaginationMeta,
    CustomerResponse,
    CustomerListResponse,
    SubscriptionResponse,
    PlanResponse,
    TicketResponse,
    TicketListResponse,
    TicketEventResponse,
    TicketDetailResponse,
    NetworkSiteResponse,
    NetworkSiteListResponse,
    NetworkEventResponse,
    NetworkEventListResponse,
    IncidentResponse,
    IncidentListResponse,
    CustomerInteractionResponse,
    CustomerInteractionListResponse,
    DashboardStatsResponse,
    DashboardOverviewResponse,
    InvestigationContext,
    InvestigationSubscription,
    InvestigationNetworkSite,
    InvestigationNetworkEvent,
    InvestigationIncident,
    InvestigationTicketHistory,
    InvestigationInteraction,
    PreviousTicket,
    CustomerStats,
    InvestigationResult,
    KnowledgeDocumentSummary,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentDetail,
    KnowledgeCategoryInfo,
    KnowledgeCategoryListResponse,
    KnowledgeSearchResult,
    KnowledgeSearchResponse,
    KnowledgeChunk,
    KnowledgeChunkListResponse,
    KnowledgeSection,
    KnowledgeChunkPreview,
    CaseReasoningRequest,
    CaseReasoningResponse,
    RetrievalInfoSchema,
    AIReasoningResultSchema,
    CaseResolveRequest,
    ResolutionDecision,
    ReviewStateCreate,
    ReviewStateResponse,
)
from src.core.config import SERVICE_NAME, GEMINI_CONFIGURED, FRONTEND_DIST
from src.database.db import get_connection
from src.database.repositories.customer_repository import CustomerRepository
from src.database.repositories.ticket_repository import TicketRepository
from src.database.repositories.network_repository import NetworkRepository
from src.database.repositories.incident_repository import IncidentRepository
from src.database.repositories.plan_repository import PlanRepository
from src.services.dashboard_service import get_dashboard_overview
from src.services.case_investigation_service import get_case_investigation
from src.services import knowledge_service
from src.services.ai_reasoning_service import analyze_case
from src.services.resolution_service import resolve_case
from src.services.analysis_service import analyze_ticket
from src.tickets import transition_case, get_current_state, get_state_history, InvalidTransitionError
from src.clarify import record_clarification_answer, get_clarification_count
from src.audit import get_audit_trail
from src.escalate import build_handover

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def _paginate(total: int, page: int, page_size: int) -> PaginationMeta:
    return PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


# ── Health ──────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    from src.retrieval.vector_store import get_vector_store
    store = get_vector_store()
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        gemini_configured=GEMINI_CONFIGURED,
        faiss_loaded=store.is_loaded(),
        faiss_vectors=store.total_vectors,
    )


# ── Dashboard ───────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardStatsResponse)
async def dashboard_stats() -> DashboardStatsResponse:
    conn = get_connection()
    try:
        cr = CustomerRepository(conn)
        tr = TicketRepository(conn)
        nr = NetworkRepository(conn)
        ir = IncidentRepository(conn)
        return DashboardStatsResponse(
            total_customers=cr.count_all(),
            open_tickets=tr.count_all(),
            active_incidents=ir.count_active(),
            total_network_sites=nr.count_all_sites(),
            active_network_events=nr.count_active_events(),
            ticket_status_counts=tr.count_by_status(),
            incident_status_counts=ir.count_by_status(),
            site_status_counts=nr.count_by_status(),
        )
    finally:
        conn.close()


@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
async def dashboard_overview() -> DashboardOverviewResponse:
    conn = get_connection()
    try:
        data = get_dashboard_overview(conn)
        return DashboardOverviewResponse(**data)
    finally:
        conn.close()


# ── Customers ───────────────────────────────────────────

@router.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    search: str | None = Query(None),
    status: str | None = Query(None),
    segment: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> CustomerListResponse:
    conn = get_connection()
    try:
        repo = CustomerRepository(conn)
        data, total = repo.list_customers(
            search=search, status=status, segment=segment,
            page=page, page_size=page_size,
        )
        return CustomerListResponse(
            data=[CustomerResponse(**d) for d in data],
            pagination=_paginate(total, page, page_size),
        )
    finally:
        conn.close()


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int) -> CustomerResponse:
    conn = get_connection()
    try:
        repo = CustomerRepository(conn)
        customer = repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return CustomerResponse(**customer)
    finally:
        conn.close()


@router.get(
    "/customers/{customer_id}/subscriptions",
    response_model=list[SubscriptionResponse],
)
async def get_customer_subscriptions(customer_id: int) -> list[SubscriptionResponse]:
    conn = get_connection()
    try:
        repo = CustomerRepository(conn)
        customer = repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        subs = repo.get_subscriptions(customer_id)
        return [SubscriptionResponse(**s) for s in subs]
    finally:
        conn.close()


@router.get(
    "/customers/{customer_id}/tickets",
    response_model=TicketListResponse,
)
async def get_customer_tickets(
    customer_id: int,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TicketListResponse:
    conn = get_connection()
    try:
        repo = CustomerRepository(conn)
        customer = repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        data, total = repo.get_tickets(
            customer_id, status=status, page=page, page_size=page_size,
        )
        return TicketListResponse(
            data=[TicketResponse(**d) for d in data],
            pagination=_paginate(total, page, page_size),
        )
    finally:
        conn.close()


@router.get(
    "/customers/{customer_id}/interactions",
    response_model=CustomerInteractionListResponse,
)
async def get_customer_interactions(
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> CustomerInteractionListResponse:
    conn = get_connection()
    try:
        repo = CustomerRepository(conn)
        customer = repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        data, total = repo.get_interactions(
            customer_id, page=page, page_size=page_size,
        )
        return CustomerInteractionListResponse(
            data=[CustomerInteractionResponse(**d) for d in data],
            pagination=_paginate(total, page, page_size),
        )
    finally:
        conn.close()


# ── Plans ───────────────────────────────────────────────

@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    plan_type: str | None = Query(None),
    status: str | None = Query(None),
) -> list[PlanResponse]:
    conn = get_connection()
    try:
        repo = PlanRepository(conn)
        plans = repo.list_plans(plan_type=plan_type, status=status)
        return [PlanResponse(**p) for p in plans]
    finally:
        conn.close()


# ── Network Sites ───────────────────────────────────────

@router.get("/network/sites", response_model=NetworkSiteListResponse)
async def list_network_sites(
    region: str | None = Query(None),
    technology: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> NetworkSiteListResponse:
    conn = get_connection()
    try:
        repo = NetworkRepository(conn)
        data, total = repo.list_sites(
            region=region, technology=technology, status=status,
            page=page, page_size=page_size,
        )
        return NetworkSiteListResponse(
            data=[NetworkSiteResponse(**d) for d in data],
            pagination=_paginate(total, page, page_size),
        )
    finally:
        conn.close()


@router.get("/network/sites/{site_id}", response_model=NetworkSiteResponse)
async def get_network_site(site_id: int) -> NetworkSiteResponse:
    conn = get_connection()
    try:
        repo = NetworkRepository(conn)
        site = repo.get_site_by_id(site_id)
        if not site:
            raise HTTPException(status_code=404, detail="Network site not found")
        return NetworkSiteResponse(**site)
    finally:
        conn.close()


@router.get(
    "/network/sites/{site_id}/events",
    response_model=NetworkEventListResponse,
)
async def get_site_events(
    site_id: int,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> NetworkEventListResponse:
    conn = get_connection()
    try:
        repo = NetworkRepository(conn)
        site = repo.get_site_by_id(site_id)
        if not site:
            raise HTTPException(status_code=404, detail="Network site not found")
        data, total = repo.get_site_events(
            site_id, status=status, page=page, page_size=page_size,
        )
        return NetworkEventListResponse(
            data=[NetworkEventResponse(**d) for d in data],
            pagination=_paginate(total, page, page_size),
        )
    finally:
        conn.close()


# ── Incidents ───────────────────────────────────────────

@router.get("/incidents", response_model=IncidentListResponse)
async def list_incidents(
    status: str | None = Query(None),
    severity: str | None = Query(None),
    region: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> IncidentListResponse:
    conn = get_connection()
    try:
        repo = IncidentRepository(conn)
        data, total = repo.list_incidents(
            status=status, severity=severity, region=region,
            page=page, page_size=page_size,
        )
        return IncidentListResponse(
            data=[IncidentResponse(**d) for d in data],
            pagination=_paginate(total, page, page_size),
        )
    finally:
        conn.close()


@router.get("/incidents/active", response_model=IncidentListResponse)
async def list_active_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> IncidentListResponse:
    conn = get_connection()
    try:
        repo = IncidentRepository(conn)
        data, total = repo.get_active_incidents(page=page, page_size=page_size)
        return IncidentListResponse(
            data=[IncidentResponse(**d) for d in data],
            pagination=_paginate(total, page, page_size),
        )
    finally:
        conn.close()


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: int) -> IncidentResponse:
    conn = get_connection()
    try:
        repo = IncidentRepository(conn)
        incident = repo.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        return IncidentResponse(**incident)
    finally:
        conn.close()


# ── Tickets ─────────────────────────────────────────────

@router.get("/tickets", response_model=TicketListResponse)
async def list_tickets(
    status: str | None = Query(None),
    priority: str | None = Query(None),
    category: str | None = Query(None),
    customer_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TicketListResponse:
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        data, total = repo.list_tickets(
            status=status, priority=priority, category=category,
            customer_id=customer_id, search=search,
            page=page, page_size=page_size,
        )
        return TicketListResponse(
            data=[TicketResponse(**d) for d in data],
            pagination=_paginate(total, page, page_size),
        )
    finally:
        conn.close()


@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(ticket_id: int) -> TicketDetailResponse:
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        history = repo.get_history(ticket_id)
        return TicketDetailResponse(
            **ticket,
            history=[TicketEventResponse(**h) for h in history],
        )
    finally:
        conn.close()


@router.get(
    "/tickets/{ticket_id}/history",
    response_model=list[TicketEventResponse],
)
async def get_ticket_history(ticket_id: int) -> list[TicketEventResponse]:
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        history = repo.get_history(ticket_id)
        return [TicketEventResponse(**h) for h in history]
    finally:
        conn.close()


# ── Case Investigation ─────────────────────────────────

@router.get("/cases/{ticket_id}/investigation")
async def get_investigation(ticket_id: int):
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        result = get_case_investigation(conn, ticket_id)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to build investigation context")

        return InvestigationContext(
            ticket=TicketResponse(**result["ticket"]),
            customer=CustomerResponse(**result["customer"]) if result["customer"] else None,
            subscription=InvestigationSubscription(**result["subscription"]) if result["subscription"] else None,
            previous_tickets=[PreviousTicket(**pt) for pt in result["previous_tickets"]],
            network={
                "site": InvestigationNetworkSite(**result["network"]["site"]) if result["network"]["site"] else None,
                "events": [InvestigationNetworkEvent(**e) for e in result["network"]["events"]],
            },
            incidents=[InvestigationIncident(**inc) for inc in result["incidents"]],
            ticket_history=[InvestigationTicketHistory(**h) for h in result["ticket_history"]],
            interactions=[InvestigationInteraction(**i) for i in result["interactions"]],
            customer_stats=CustomerStats(**result["customer_stats"]),
            investigation=InvestigationResult(**result["investigation"]),
        )
    finally:
        conn.close()


# ── Knowledge Base ──────────────────────────────────────

@router.get("/knowledge", response_model=KnowledgeDocumentListResponse)
async def list_knowledge_documents(
    category: str | None = Query(None),
) -> KnowledgeDocumentListResponse:
    docs = knowledge_service.list_documents(category=category)
    return KnowledgeDocumentListResponse(
        data=[KnowledgeDocumentSummary(**d) for d in docs],
        total=len(docs),
    )


@router.get("/knowledge/categories", response_model=KnowledgeCategoryListResponse)
async def list_knowledge_categories() -> KnowledgeCategoryListResponse:
    cats = knowledge_service.list_categories()
    return KnowledgeCategoryListResponse(
        data=[KnowledgeCategoryInfo(**c) for c in cats],
        total=len(cats),
    )


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    q: str = Query(..., min_length=1),
    category: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
) -> KnowledgeSearchResponse:
    results = knowledge_service.search_documents(query=q, category=category, limit=limit)
    search_results = []
    for r in results:
        chunks = [KnowledgeChunkPreview(**c) for c in r.get("matching_chunks", [])]
        search_results.append(KnowledgeSearchResult(
            id=r["id"],
            title=r["title"],
            category=r["category"],
            score=r["score"],
            matching_chunks=chunks,
            preview=r.get("preview", ""),
        ))
    return KnowledgeSearchResponse(
        query=q,
        category=category,
        results=search_results,
        total=len(search_results),
    )


@router.get("/knowledge/{document_id}", response_model=KnowledgeDocumentDetail)
async def get_knowledge_document(document_id: str) -> KnowledgeDocumentDetail:
    doc = knowledge_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    sections = [KnowledgeSection(**s) for s in doc["sections"]]
    return KnowledgeDocumentDetail(
        id=doc["id"],
        title=doc["title"],
        category=doc["category"],
        tags=doc["tags"],
        path=doc["path"],
        content=doc["content"],
        sections=sections,
    )


@router.get("/knowledge/{document_id}/chunks", response_model=KnowledgeChunkListResponse)
async def get_knowledge_chunks(document_id: str) -> KnowledgeChunkListResponse:
    doc = knowledge_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    chunks = knowledge_service.get_chunks(document_id)
    return KnowledgeChunkListResponse(
        document_id=document_id,
        chunks=[KnowledgeChunk(**c) for c in chunks],
        total=len(chunks),
    )


# ── AI Case Reasoning ───────────────────────────────────

@router.post("/cases/{ticket_id}/reason", response_model=CaseReasoningResponse)
async def reason_case(ticket_id: int, body: CaseReasoningRequest):
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        investigation = get_case_investigation(conn, ticket_id)
        if not investigation:
            raise HTTPException(status_code=500, detail="Failed to build investigation context")

        result = analyze_case(investigation, question=body.question)

        return CaseReasoningResponse(
            case_id=str(ticket_id),
            retrieval=RetrievalInfoSchema(**result["retrieval"]),
            reasoning=AIReasoningResultSchema(**result["reasoning"]),
        )
    finally:
        conn.close()


# ── Case Resolution Decision Engine ─────────────────────

@router.post("/cases/{ticket_id}/resolve", response_model=ResolutionDecision)
async def resolve_case_endpoint(ticket_id: int, body: CaseResolveRequest | None = None):
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        question = body.question if body else None
        result = resolve_case(conn, ticket_id, question=question)

        return ResolutionDecision(**result)
    finally:
        conn.close()


@router.post("/cases/{ticket_id}/review", response_model=ReviewStateResponse)
async def submit_review(ticket_id: int, body: ReviewStateCreate):
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        cursor = conn.execute(
            "SELECT id FROM review_states WHERE ticket_id = ? ORDER BY id DESC LIMIT 1",
            (ticket_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No resolution recommendation found for this case")

        review_id = row[0]
        conn.execute(
            "UPDATE review_states SET reviewer_decision = ?, reason = ?, updated_at = ? WHERE id = ?",
            (body.decision, body.reason or "", now, review_id),
        )
        conn.commit()

        cursor = conn.execute(
            "SELECT id, ticket_id, recommendation_category, recommendation_action, confidence, reviewer_decision, reason, created_at, updated_at FROM review_states WHERE id = ?",
            (review_id,),
        )
        r = cursor.fetchone()
        return ReviewStateResponse(
            id=r[0], ticket_id=r[1], recommendation_category=r[2],
            recommendation_action=r[3], confidence=r[4], reviewer_decision=r[5],
            reason=r[6], created_at=r[7], updated_at=r[8],
        )
    finally:
        conn.close()


@router.get("/cases/{ticket_id}/review", response_model=list[ReviewStateResponse])
async def get_review_states(ticket_id: int):
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        cursor = conn.execute(
            "SELECT id, ticket_id, recommendation_category, recommendation_action, confidence, reviewer_decision, reason, created_at, updated_at FROM review_states WHERE ticket_id = ? ORDER BY created_at DESC",
            (ticket_id,),
        )
        rows = cursor.fetchall()
        return [
            ReviewStateResponse(
                id=r[0], ticket_id=r[1], recommendation_category=r[2],
                recommendation_action=r[3], confidence=r[4], reviewer_decision=r[5],
                reason=r[6], created_at=r[7], updated_at=r[8],
            )
            for r in rows
        ]
    finally:
        conn.close()


# ── Case Analysis (Mode A/B/C) ─────────────────────────

@router.post("/cases/{ticket_id}/analyze")
async def analyze_case_endpoint(ticket_id: int):
    """Run full analysis on a case — classifies into Mode A/B/C and returns result."""
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        result = analyze_ticket(conn, ticket_id)
        return {
            "ticket_id": result.ticket_id,
            "ticket_number": result.ticket_number,
            "mode": result.mode,
            "classification": {
                "mode": result.classification.mode,
                "reason_codes": result.classification.reason_codes,
                "confidence": result.classification.confidence,
                "required_information": result.classification.required_information,
                "escalation_required": result.classification.escalation_required,
                "escalation_queue": result.classification.escalation_queue,
                "missing_fields": result.classification.missing_fields,
                "blocking_reasons": result.classification.blocking_reasons,
                "eligible_for_draft": result.classification.eligible_for_draft,
            },
            "draft": {
                "draft_response": result.draft.draft_response,
                "reasoning_summary": result.draft.reasoning_summary,
                "citations": result.draft.citations,
                "confidence": result.draft.confidence,
                "limitations": result.draft.limitations,
                "account_evidence": result.draft.account_evidence,
                "operational_evidence": result.draft.operational_evidence,
                "knowledge_evidence": result.draft.knowledge_evidence,
            } if result.draft else None,
            "clarification": {
                "question": result.clarification.question,
                "missing_field": result.clarification.missing_field,
                "reason": result.clarification.reason,
                "turn_number": result.clarification.turn_number,
            } if result.clarification else None,
            "handover": {
                "case_id": result.handover.case_id,
                "ticket_number": result.handover.ticket_number,
                "customer_name": result.handover.customer_name,
                "customer_segment": result.handover.customer_segment,
                "customer_phone": result.handover.customer_phone,
                "account_service": result.handover.account_service,
                "plan_name": result.handover.plan_name,
                "plan_type": result.handover.plan_type,
                "operator": result.handover.operator,
                "issue_summary": result.handover.issue_summary,
                "original_message": result.handover.original_message,
                "confirmed_facts": result.handover.confirmed_facts,
                "missing_information": result.handover.missing_information,
                "previous_tickets": result.handover.previous_tickets,
                "previous_troubleshooting": result.handover.previous_troubleshooting,
                "network_context": result.handover.network_context,
                "retrieval_result": result.handover.retrieval_result,
                "retrieval_confidence": result.handover.retrieval_confidence,
                "escalation_reasons": result.handover.escalation_reasons,
                "escalation_queue": result.handover.escalation_queue,
                "severity": result.handover.severity,
                "timestamp": result.handover.timestamp,
                "current_status": result.handover.current_status,
                "recommendations": result.handover.recommendations,
                "evidence_summary": result.handover.evidence_summary,
            } if result.handover else None,
            "conflicts": [
                {
                    "conflict_type": c.conflict_type,
                    "source_a": c.source_a,
                    "source_b": c.source_b,
                    "description": c.description,
                    "impact": c.impact,
                    "human_action_required": c.human_action_required,
                }
                for c in result.conflicts
            ],
            "retrieval_info": result.retrieval_info,
            "errors": result.errors,
            "state_transition": result.state_transition,
        }
    finally:
        conn.close()


# ── Clarification ───────────────────────────────────────

@router.post("/cases/{ticket_id}/clarify")
async def submit_clarification_answer(ticket_id: int, body: dict):
    """Submit customer answer to a clarification question."""
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        field = body.get("field", "")
        answer = body.get("answer", "")
        if not field or not answer:
            raise HTTPException(status_code=400, detail="field and answer are required")

        record_clarification_answer(conn, ticket_id, field, answer)

        # Re-analyze after clarification
        result = analyze_ticket(conn, ticket_id)
        return {
            "status": "ok",
            "field": field,
            "answer": answer,
            "new_mode": result.mode,
            "classification": {
                "mode": result.classification.mode,
                "reason_codes": result.classification.reason_codes,
                "confidence": result.classification.confidence,
            },
            "draft": {
                "draft_response": result.draft.draft_response,
                "reasoning_summary": result.draft.reasoning_summary,
                "citations": result.draft.citations,
                "confidence": result.draft.confidence,
                "limitations": result.draft.limitations,
                "account_evidence": result.draft.account_evidence,
                "operational_evidence": result.draft.operational_evidence,
            } if result.draft else None,
            "clarification": {
                "question": result.clarification.question,
                "missing_field": result.clarification.missing_field,
                "reason": result.clarification.reason,
                "turn_number": result.clarification.turn_number,
            } if result.clarification else None,
        }
    finally:
        conn.close()


# ── Agent Actions ───────────────────────────────────────

@router.post("/cases/{ticket_id}/approve")
async def approve_recommendation(ticket_id: int, body: dict | None = None):
    """Agent approves the resolution recommendation."""
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        current = get_current_state(conn, ticket_id)
        notes = (body or {}).get("notes", "")

        transition = transition_case(conn, ticket_id, current, "approved", "agent", notes)

        # Record audit event
        from src.audit import record_recommendation_approved
        record_recommendation_approved(conn, ticket_id, "agent", notes)

        return {"status": "ok", "transition": transition}
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.post("/cases/{ticket_id}/dismiss")
async def dismiss_recommendation(ticket_id: int, body: dict | None = None):
    """Agent dismisses the resolution recommendation."""
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        current = get_current_state(conn, ticket_id)
        reason = (body or {}).get("reason", "")

        transition = transition_case(conn, ticket_id, current, "dismissed", "agent", reason)

        from src.audit import record_recommendation_dismissed
        record_recommendation_dismissed(conn, ticket_id, "agent", reason)

        return {"status": "ok", "transition": transition}
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.post("/cases/{ticket_id}/escalate")
async def escalate_case(ticket_id: int, body: dict | None = None):
    """Agent manually escalates a case."""
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        current = get_current_state(conn, ticket_id)
        reason = (body or {}).get("reason", "Manual escalation by agent")
        queue = (body or {}).get("queue", "Technical Support - L1")

        transition = transition_case(conn, ticket_id, current, "escalation_requested", "agent", reason)

        from src.audit import record_escalation
        record_escalation(conn, ticket_id, queue, [reason])

        return {"status": "ok", "transition": transition}
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.post("/cases/{ticket_id}/resolve-final")
async def resolve_case_final(ticket_id: int, body: dict | None = None):
    """Agent marks case as resolved."""
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        current = get_current_state(conn, ticket_id)
        resolution = (body or {}).get("resolution", "")

        transition = transition_case(conn, ticket_id, current, "resolved", "agent", resolution)

        from src.audit import record_case_resolved
        record_case_resolved(conn, ticket_id, resolution)

        return {"status": "ok", "transition": transition}
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


# ── Audit & State History ───────────────────────────────

@router.get("/cases/{ticket_id}/audit")
async def get_case_audit(ticket_id: int):
    """Get full audit trail for a case."""
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        audit = get_audit_trail(conn, ticket_id)
        history = get_state_history(conn, ticket_id)
        return {"audit": audit, "state_history": history}
    finally:
        conn.close()


@router.get("/cases/{ticket_id}/handover")
async def get_case_handover(ticket_id: int):
    """Get escalation handover package for a case."""
    conn = get_connection()
    try:
        repo = TicketRepository(conn)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        cursor = conn.execute(
            "SELECT handover_summary FROM escalation_records WHERE ticket_id = ? ORDER BY created_at DESC LIMIT 1",
            (ticket_id,),
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="No handover package found for this case")

        import json
        handover = json.loads(row[0])
        return handover
    finally:
        conn.close()


# ── Queue Views ─────────────────────────────────────────

@router.get("/queue")
async def get_support_queue(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """Get cases filtered by queue/status for the support queue."""
    conn = get_connection()
    try:
        repo = TicketRepository(conn)

        # Map queue filters to ticket statuses
        status_filter = None
        if status:
            status_map = {
                "all": None,
                "routine": "pending_agent_approval",
                "needs_information": "needs_information",
                "human_review": "escalation_requested",
                "pending_approval": "pending_agent_approval",
                "resolved": "resolved",
                "analyzing": "analyzing",
            }
            status_filter = status_map.get(status)

        data, total = repo.list_tickets(status=status_filter, page=page, page_size=page_size)

        # Enrich with customer name and operator
        enriched = []
        for d in data:
            enriched_ticket = dict(d)
            if d.get("customer_id"):
                cursor = conn.execute(
                    "SELECT name, segment FROM customers WHERE id = ?",
                    (d["customer_id"],),
                )
                cust = cursor.fetchone()
                if cust:
                    enriched_ticket["customer_name"] = cust[0]
                    enriched_ticket["customer_segment"] = cust[1]

            if d.get("subscription_id"):
                cursor = conn.execute(
                    """SELECT tp.name FROM subscriptions s
                       JOIN plans p ON s.plan_id = p.id
                       JOIN telecom_providers tp ON p.provider_id = tp.id
                       WHERE s.id = ?""",
                    (d["subscription_id"],),
                )
                sub = cursor.fetchone()
                if sub:
                    enriched_ticket["operator"] = sub[0]

            if d.get("id"):
                cursor = conn.execute(
                    "SELECT reviewer_decision FROM review_states WHERE ticket_id = ? ORDER BY created_at DESC LIMIT 1",
                    (d["id"],),
                )
                rev = cursor.fetchone()
                enriched_ticket["review_status"] = rev[0] if rev else None

            enriched.append(enriched_ticket)

        return {
            "data": enriched,
            "pagination": _paginate(total, page, page_size),
        }
    finally:
        conn.close()


# ── Frontend Serving ────────────────────────────────────

def serve_frontend(app) -> None:
    dist = FRONTEND_DIST
    index_file = dist / "index.html"

    if not dist.exists() or not index_file.exists():
        @app.get("/{full_path:path}")
        async def serve_frontend_fallback(full_path: str):
            return JSONResponse(
                status_code=200,
                content={
                    "message": "SmartResolve API is running. Frontend not built yet.",
                    "hint": "Run 'npm run build' inside frontend/ to build the UI.",
                    "docs": "/docs",
                },
            )
        return

    @app.get("/{full_path:path}")
    async def serve_frontend_assets(full_path: str):
        file_path = dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(index_file)
