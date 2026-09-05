import logging
import math
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
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        gemini_configured=GEMINI_CONFIGURED,
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
