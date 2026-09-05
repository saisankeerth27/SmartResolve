"""Main analysis orchestrator — ties together classification, retrieval, and mode-specific handling.

This is the central service that:
1. Builds investigation context
2. Runs retrieval
3. Classifies the case (Mode A/B/C)
4. Routes to appropriate handler
5. Records audit events
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any

from src.classify import classify_case, ClassificationResult
from src.services.case_investigation_service import get_case_investigation
from src.services.ai_reasoning_service import analyze_case
from src.retrieval.retriever import retrieve_relevant_chunks
from src.retrieval.context_builder import build_retrieval_query
from src.config import CATEGORY_KNOWLEDGE_MAP
from src.draft import generate_draft, DraftResult
from src.clarify import generate_clarification, ClarificationRequest
from src.escalate import build_handover, HandoverPackage, store_escalation
from src.rules.conflict import detect_conflicts, Conflict
from src.rules.escalation import evaluate_escalation
from src.tickets import transition_case, get_current_state, InvalidTransitionError
from src.audit import (
    record_analysis_started,
    record_mode_selected,
    record_retrieval,
    record_draft_generated,
    record_clarification,
    record_escalation,
    record_ai_called,
    record_ai_failed,
    record_conflict_detected,
    record_state_changed,
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Complete result of case analysis."""
    ticket_id: int
    ticket_number: str
    classification: ClassificationResult
    mode: str  # "A", "B", or "C"
    draft: DraftResult | None = None
    clarification: ClarificationRequest | None = None
    handover: HandoverPackage | None = None
    conflicts: list[Conflict] = field(default_factory=list)
    retrieval_info: dict = field(default_factory=dict)
    investigation: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    state_transition: dict | None = None


def analyze_ticket(
    conn,
    ticket_id: int,
    question: str | None = None,
    already_asked: list[str] | None = None,
) -> AnalysisResult:
    """Run full analysis on a ticket.

    Returns AnalysisResult with the appropriate mode handler result.
    """
    # Record analysis started
    record_analysis_started(conn, ticket_id)

    # Get current state
    current_state = get_current_state(conn, ticket_id)

    # Build investigation context
    investigation = get_case_investigation(conn, ticket_id)
    if not investigation:
        return AnalysisResult(
            ticket_id=ticket_id,
            ticket_number="",
            classification=ClassificationResult(mode="C", reason_codes=["INVESTIGATION-FAILED"]),
            mode="C",
            errors=["Could not build investigation context."],
        )

    ticket = investigation.get("ticket", {})
    ticket_number = ticket.get("ticket_number", str(ticket_id))

    clarification_rows = conn.execute(
        "SELECT missing_field, COUNT(*) FROM clarification_requests WHERE ticket_id = ? GROUP BY missing_field",
        (ticket_id,),
    ).fetchall()
    clarification_attempts = {row[0]: row[1] for row in clarification_rows}
    confirmed_answers = conn.execute(
        "SELECT missing_field, answer FROM clarification_requests WHERE ticket_id = ? AND answer IS NOT NULL ORDER BY id",
        (ticket_id,),
    ).fetchall()
    if confirmed_answers:
        investigation.setdefault("investigation", {}).setdefault("known_facts", []).extend(
            f"Customer confirmed {field}: {answer}" for field, answer in confirmed_answers
        )

    # Run retrieval
    retrieval_chunks = []
    retrieval_info = {"total": 0, "average_score": 0.0, "chunks": []}
    try:
        category = ticket.get("category", "network")
        candidate_categories = CATEGORY_KNOWLEDGE_MAP.get(category, [category])
        query = build_retrieval_query(investigation)
        retrieval_chunks = retrieve_relevant_chunks(query, candidate_categories, top_k=5)
        if retrieval_chunks:
            scores = [c.get("score", 0) for c in retrieval_chunks]
            retrieval_info = {
                "total": len(retrieval_chunks),
                "average_score": sum(scores) / len(scores) if scores else 0.0,
                "chunks": retrieval_chunks,
            }
            record_retrieval(conn, ticket_id, len(retrieval_chunks), retrieval_info["average_score"], candidate_categories)
    except Exception as e:
        logger.warning("Retrieval failed: %s", e)
        retrieval_info = {"total": 0, "average_score": 0.0, "chunks": [], "error": str(e)}

    # Add retrieval info to context for classification
    context = dict(investigation)
    context["retrieval"] = retrieval_info
    context["clarification_attempts"] = clarification_attempts

    # Detect conflicts
    conflicts = detect_conflicts(context)
    if conflicts:
        for c in conflicts:
            record_conflict_detected(conn, ticket_id, c.conflict_type, c.description)

    # Check escalation matrix
    escalation = evaluate_escalation(context)

    # Classify the case
    classification = classify_case(context, already_asked)
    record_mode_selected(conn, ticket_id, classification.mode, classification.reason_codes)

    # Determine target state based on mode
    target_state = _get_target_state(classification.mode, classification)

    # Attempt state transition
    state_transition = None
    try:
        if current_state in ("open", "new"):
            state_transition = transition_case(conn, ticket_id, current_state, "analyzing", "system", "Analysis started")
            current_state = "analyzing"

        if current_state == "analyzing" and target_state and target_state != "analyzing":
            state_transition = transition_case(conn, ticket_id, "analyzing", target_state, "system", f"Mode {classification.mode} selected")
            current_state = target_state
        elif current_state == target_state:
            pass  # already in target state
        elif current_state in ("pending_agent_approval", "needs_information", "human_review", "escalation_requested") and target_state != current_state:
            # Re-analysis from an active state - transition back through analyzing
            try:
                state_transition = transition_case(conn, ticket_id, current_state, "analyzing", "system", "Re-analysis triggered")
                current_state = "analyzing"
                if target_state and target_state != "analyzing":
                    state_transition = transition_case(conn, ticket_id, "analyzing", target_state, "system", f"Mode {classification.mode} selected")
                    current_state = target_state
            except (InvalidTransitionError, ValueError):
                pass  # Keep current state if transition fails
    except (InvalidTransitionError, ValueError) as e:
        logger.warning("State transition failed: %s", e)
        classification.reason_codes.append(f"STATE-TRANSITION-ERROR: {e}")

    result = AnalysisResult(
        ticket_id=ticket_id,
        ticket_number=ticket_number,
        classification=classification,
        mode=classification.mode,
        conflicts=conflicts,
        retrieval_info=retrieval_info,
        investigation=investigation,
        state_transition=state_transition,
    )

    # Route to mode-specific handler
    if classification.mode == "A":
        result.draft = _handle_mode_a(conn, ticket_id, context, investigation)
    elif classification.mode == "B":
        result.clarification = _handle_mode_b(conn, ticket_id, classification, context, investigation)
    elif classification.mode == "C":
        result.handover = _handle_mode_c(conn, ticket_id, classification, context, investigation, retrieval_info)

    try:
        save_analysis_result(conn, result)
    except Exception as e:
        logger.warning("Failed to save analysis result for ticket %s: %s", ticket_id, e)

    return result


def _ensure_analysis_table(conn) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS case_analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL REFERENCES tickets(id),
            mode TEXT NOT NULL CHECK (mode IN ('A', 'B', 'C')),
            classification_json TEXT NOT NULL,
            draft_json TEXT,
            clarification_json TEXT,
            handover_json TEXT,
            conflicts_json TEXT,
            retrieval_info_json TEXT,
            errors_json TEXT,
            state_transition_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_case_analysis_ticket ON case_analysis_results(ticket_id)")


def format_analysis_dict(result: AnalysisResult) -> dict:
    """Format an AnalysisResult into a standard dictionary representation."""
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
            "citations": [
                {"document_id": c.document_id, "document_title": c.document_title, "section_heading": c.section_heading}
                if hasattr(c, "document_id") else c
                for c in (result.draft.citations or [])
            ] if isinstance(result.draft.citations, list) else result.draft.citations,
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
                "conflict_type": c.conflict_type if hasattr(c, "conflict_type") else (c.get("conflict_type") if isinstance(c, dict) else str(c)),
                "source_a": c.source_a if hasattr(c, "source_a") else (c.get("source_a") if isinstance(c, dict) else ""),
                "source_b": c.source_b if hasattr(c, "source_b") else (c.get("source_b") if isinstance(c, dict) else ""),
                "description": c.description if hasattr(c, "description") else (c.get("description") if isinstance(c, dict) else ""),
                "impact": c.impact if hasattr(c, "impact") else (c.get("impact") if isinstance(c, dict) else ""),
                "human_action_required": c.human_action_required if hasattr(c, "human_action_required") else (c.get("human_action_required") if isinstance(c, dict) else ""),
            }
            for c in result.conflicts
        ],
        "retrieval_info": result.retrieval_info,
        "errors": result.errors,
        "state_transition": result.state_transition,
    }


def save_analysis_result(conn, result: AnalysisResult) -> None:
    """Persist the full AnalysisResult to database."""
    _ensure_analysis_table(conn)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    data = format_analysis_dict(result)

    existing = conn.execute(
        "SELECT id FROM case_analysis_results WHERE ticket_id = ?",
        (result.ticket_id,),
    ).fetchone()

    if existing:
        conn.execute(
            """UPDATE case_analysis_results SET
               mode = ?, classification_json = ?, draft_json = ?,
               clarification_json = ?, handover_json = ?, conflicts_json = ?,
               retrieval_info_json = ?, errors_json = ?, state_transition_json = ?,
               updated_at = ?
               WHERE id = ?""",
            (
                result.mode,
                json.dumps(data["classification"]),
                json.dumps(data["draft"]) if data["draft"] else None,
                json.dumps(data["clarification"]) if data["clarification"] else None,
                json.dumps(data["handover"]) if data["handover"] else None,
                json.dumps(data["conflicts"]),
                json.dumps(data["retrieval_info"]),
                json.dumps(data["errors"]),
                json.dumps(data["state_transition"]) if data["state_transition"] else None,
                now,
                existing[0],
            ),
        )
    else:
        conn.execute(
            """INSERT INTO case_analysis_results
               (ticket_id, mode, classification_json, draft_json, clarification_json,
                handover_json, conflicts_json, retrieval_info_json, errors_json,
                state_transition_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.ticket_id,
                result.mode,
                json.dumps(data["classification"]),
                json.dumps(data["draft"]) if data["draft"] else None,
                json.dumps(data["clarification"]) if data["clarification"] else None,
                json.dumps(data["handover"]) if data["handover"] else None,
                json.dumps(data["conflicts"]),
                json.dumps(data["retrieval_info"]),
                json.dumps(data["errors"]),
                json.dumps(data["state_transition"]) if data["state_transition"] else None,
                now,
                now,
            ),
        )
    conn.commit()


def get_last_analysis(conn, ticket_id: int) -> dict | None:
    """Retrieve the most recent analysis result for a ticket."""
    _ensure_analysis_table(conn)
    cursor = conn.execute(
        """SELECT r.mode, r.classification_json, r.draft_json, r.clarification_json,
                  r.handover_json, r.conflicts_json, r.retrieval_info_json,
                  r.errors_json, r.state_transition_json, t.ticket_number
           FROM case_analysis_results r
           JOIN tickets t ON r.ticket_id = t.id
           WHERE r.ticket_id = ?
           ORDER BY r.updated_at DESC LIMIT 1""",
        (ticket_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    return {
        "ticket_id": ticket_id,
        "ticket_number": row[9],
        "mode": row[0],
        "classification": json.loads(row[1]) if row[1] else {},
        "draft": json.loads(row[2]) if row[2] else None,
        "clarification": json.loads(row[3]) if row[3] else None,
        "handover": json.loads(row[4]) if row[4] else None,
        "conflicts": json.loads(row[5]) if row[5] else [],
        "retrieval_info": json.loads(row[6]) if row[6] else {},
        "errors": json.loads(row[7]) if row[7] else [],
        "state_transition": json.loads(row[8]) if row[8] else None,
    }


def _get_target_state(mode: str, classification: ClassificationResult) -> str:
    """Determine the target state for the ticket based on mode."""
    if mode == "A":
        return "pending_agent_approval"
    elif mode == "B":
        return "needs_information"
    elif mode == "C":
        if classification.escalation_required:
            return "escalation_requested"
        return "human_review"
    return "analyzing"


def _handle_mode_a(
    conn,
    ticket_id: int,
    context: dict,
    investigation: dict,
) -> DraftResult | None:
    """Handle Mode A — grounded resolution draft."""
    record_ai_called(conn, ticket_id, "draft_generation")

    try:
        from src.core.config import GEMINI_CONFIGURED
        if not GEMINI_CONFIGURED:
            record_ai_failed(conn, ticket_id, "draft_generation", "Gemini not configured")
            return None

        from src.ai.gemini_client import get_client
        gemini = get_client()
        if not gemini:
            record_ai_failed(conn, ticket_id, "draft_generation", "Gemini client unavailable")
            return None

        draft = generate_draft(context, gemini)
        if draft:
            record_draft_generated(conn, ticket_id, draft.confidence, draft.limitations)
        else:
            record_ai_failed(conn, ticket_id, "draft_generation", "Failed to generate draft")
        return draft
    except Exception as e:
        logger.warning("Mode A draft generation failed: %s", e)
        record_ai_failed(conn, ticket_id, "draft_generation", str(e))
        return None


def _handle_mode_b(
    conn,
    ticket_id: int,
    classification: ClassificationResult,
    context: dict,
    investigation: dict,
) -> ClarificationRequest | None:
    """Handle Mode B — targeted clarification."""
    missing_fields = classification.missing_fields or classification.required_information
    if not missing_fields:
        return None

    try:
        from src.core.config import GEMINI_CONFIGURED
        gemini_client = None
        if GEMINI_CONFIGURED:
            from src.ai.gemini_client import get_client
            gemini_client = get_client()

        clarification = generate_clarification(
            conn,
            ticket_id,
            missing_fields,
            gemini_available=GEMINI_CONFIGURED and gemini_client is not None,
            investigation=investigation,
            gemini_client=gemini_client,
        )

        if clarification:
            record_clarification(conn, ticket_id, clarification.missing_field, clarification.question, clarification.turn_number)

        return clarification
    except Exception as e:
        logger.warning("Mode B clarification failed: %s", e)
        return None


def _handle_mode_c(
    conn,
    ticket_id: int,
    classification: ClassificationResult,
    context: dict,
    investigation: dict,
    retrieval_info: dict,
) -> HandoverPackage | None:
    """Handle Mode C — escalation handover."""
    handover = build_handover(context, classification, retrieval_info)
    store_escalation(conn, ticket_id, handover)
    record_escalation(conn, ticket_id, handover.escalation_queue, classification.reason_codes)
    return handover
