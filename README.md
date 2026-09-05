TRACK_ID=PS04

# SmartResolve

**India-Focused Telecom Operations Resolution Assistant**

SmartResolve is a grounded AI-assisted telecom operations system that combines customer information, operational records, support tickets, telecom policies, local RAG retrieval, Gemini reasoning, deterministic business rules, structured evidence, and human escalation into a unified resolution workspace.

The system provides grounded recommendations for human review. SmartResolve does not automatically resolve customer cases. A human operator always makes the final decision.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Router |
| Database | SQLite |
| Knowledge Base | Markdown documents, deterministic chunking, FAISS vector search |
| AI/LLM | Gemini 3.5 Flash (text), Gemini Embedding 001 (embeddings) |
| Rules Engine | Python deterministic rule evaluation with configurable thresholds |

## Operating Model

SmartResolve operates as a realistic Indian telecom L0/L1 support operation with three distinct modes:

### Mode A — Routine, Grounded Resolution

**When:** Customer request is clear, knowledge retrieval is strong, account/service data confirms eligibility, no conflicts, case is not sensitive/high-impact.

**Flow:**
```
Customer message → deterministic classification → retrieval/evidence checks → eligibility checks → Mode A → Gemini generates grounded resolution draft → citations/evidence attached → status becomes pending_agent_approval
```

**Key Points:**
- The assistant NEVER automatically sends the response to the customer
- It only prepares an approvable draft for the human agent
- The draft references customer/account facts, operational facts, and knowledge citations
- Agent can Approve, Edit, or Escalate the draft

### Mode B — Missing Information

**When:** Request is potentially resolvable but required information is missing, retrieval is ambiguous, or multiple possible causes exist.

**Flow:**
```
Customer message → missing-information detection → Mode B → Gemini generates one targeted clarification question → store question in audit history → wait for customer response → re-evaluate case
```

**Key Points:**
- The system asks exactly ONE targeted question per turn
- It remembers/logged questions so they are not repeatedly asked
- Maximum clarification turns are configurable (default: 3)
- Fallback questions are available when Gemini is unavailable

### Mode C — Human Escalation

**When:** Retrieval confidence is below safe threshold, no relevant article exists, account data conflicts, customer has repeated unresolved complaints, enterprise customer, active major incident, sensitive/legal/safety case, or Gemini/FAISS is unavailable.

**Flow:**
```
Customer message → escalation detection → Mode C → complete handover package generated → routed to appropriate specialist queue
```

**The handover includes:**
- Customer, account, service details
- Ticket ID and issue summary
- Original customer message
- Confirmed facts and missing information
- Previous tickets and troubleshooting
- Network/incident information
- Retrieval results and confidence
- Why the case was escalated
- Recommended human queue
- Timestamp and current status

**The specialist can understand the entire problem WITHOUT asking the customer to repeat everything.**

## Deterministic Classification Engine

The classification layer is pure Python logic — no Gemini calls for mode selection.

### Rule Precedence (highest to lowest)

1. **DATA INTEGRITY** — Missing customer/subscription → escalate
2. **SENSITIVE / LEGAL / SAFETY** — Fraud, legal, regulatory keywords → escalate
3. **CONFLICTING EVIDENCE** — Data source conflicts → escalate
4. **ACTIVE MAJOR INCIDENT** — Critical/high severity active incidents → escalate
5. **REPEAT COMPLAINT** — 2+ previous tickets in same category → escalate
6. **ENTERPRISE / HIGH-IMPACT** — Enterprise segment customers → escalate
7. **NETWORK DEGRADATION** — Offline site → escalate; Degraded → continue with note
8. **RETRIEVAL QUALITY** — Weak/missing retrieval → clarify or escalate
9. **ACCOUNT ELIGIBILITY** — Subscription status, data overage → clarify or escalate
10. **MODE SELECTION** — If info sufficient → Mode A; If missing → Mode B

### Configurable Thresholds

All thresholds are configurable via environment variables or `src/config.py`:

| Threshold | Default | Description |
|-----------|---------|-------------|
| `SAFE_RETRIEVAL_THRESHOLD` | 0.35 | Minimum retrieval score for Mode A |
| `STRONG_RETRIEVAL_THRESHOLD` | 0.55 | Strong retrieval score |
| `REPEAT_COMPLAINT_THRESHOLD` | 2 | Previous tickets before escalation |
| `CLARIFICATION_MAX_TURNS` | 3 | Maximum clarification rounds |
| `SENSITIVE_BILLING_LIMIT_INR` | 5000 | Billing amount triggering review |

## Escalation Matrix

| Severity | Trigger | Queue |
|----------|---------|-------|
| **CRITICAL** | Safety/legal/regulatory/fraud, site offline, major outage | Legal & Compliance / Network Operations |
| **HIGH** | Enterprise customer, repeated complaints, conflicting data | Enterprise Support / Customer Retention |
| **MEDIUM** | Insufficient evidence, weak retrieval, missing info | Technical Support L1 (clarify first) |
| **LOW** | Routine supported request | Grounded draft |

## Case State Machine

```
new → analyzing → needs_information → analyzing (loop until info complete)
                                    → pending_agent_approval → approved → resolved
                                    → escalation_requested → human_review → approved/dismissed
                 → pending_agent_approval → dismissed
                 → escalation_requested
```

Valid transitions are enforced. Invalid transitions return clear error messages.

## Audit Trail

Every important action is auditable:
- case_created, analysis_started, mode_selected
- retrieval_performed, clarification_asked/answered
- escalation_requested, draft_generated
- recommendation_approved/dismissed, case_resolved
- state_changed, ai_called/failed, conflict_detected

## Conflict Detection

The system explicitly detects and displays:
- Ticket status vs subscription status conflicts
- Network site status vs active events conflicts
- Multiple overlapping active incidents
- Previously resolved tickets with ongoing complaints

Conflicting evidence prevents automatic drafting and requires human action.

## AI Failure Handling

The application handles all failure scenarios gracefully:
- Gemini timeout/API error → safe fallback or escalation
- Invalid/missing/malformed JSON response → retry or escalate
- FAISS/unavailable retrieval → escalate
- Empty response → escalate

**Mode A:** Gemini failure does NOT produce a fake draft
**Mode B:** Uses deterministic fallback questions
**Mode C:** Handover works without Gemini

## Agent Console UX

The Agent Console provides a professional 3-panel support workspace:

| Panel | Content |
|-------|---------|
| **Left** | Support Queue with case ID, customer, issue, priority, mode/status indicators |
| **Center** | Case workspace with Analyze button, mode-specific display, customer conversation transcript, classification details, audit trail |
| **Right** | Customer/account context with service, network, incidents, investigation status |

### Mode Displays

- **Mode A (Routine):** Green grounded recommendation with draft, evidence, citations, limitations, and Approve/Dismiss/Escalate actions
- **Mode B (Missing Info):** Amber information-needed panel with targeted question and Send Question action
- **Mode C (Escalation):** Red human-review-required panel with escalation reasons, confirmed facts, missing info, previous tickets, recommendations, and Open Human Review/Add Note actions

### Queue Filters

- All, Routine, Needs Information, Human Review, Pending Approval, Resolved, Analyzing

## Customer Chat

The primary entry point for customers. Select a customer, start a conversation, describe the issue.

Every customer message goes through the existing deterministic classification pipeline:

```
Customer message → retrieve → classify → Mode A/B/C → response
```

- **Mode A:** Grounded recommendation prepared for agent approval
- **Mode B:** One targeted clarification question asked
- **Mode C:** Calm handoff message, full escalation package created

Agent Console immediately shows the case with full conversation transcript, customer context, and mode-specific actions.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/dashboard` | Dashboard statistics |
| GET | `/api/dashboard/overview` | Full operations dashboard |
| GET | `/api/customers` | List customers |
| GET | `/api/customers/{id}` | Customer detail |
| GET | `/api/customers/{id}/subscriptions` | Customer subscriptions |
| GET | `/api/customers/{id}/tickets` | Customer tickets |
| GET | `/api/customers/{id}/interactions` | Customer interactions |
| GET | `/api/plans` | List plans |
| GET | `/api/network/sites` | List network sites |
| GET | `/api/network/sites/{id}` | Site detail |
| GET | `/api/network/sites/{id}/events` | Site events |
| GET | `/api/incidents` | List incidents |
| GET | `/api/incidents/active` | Active incidents |
| GET | `/api/incidents/{id}` | Incident detail |
| GET | `/api/tickets` | List tickets |
| GET | `/api/tickets/{id}` | Ticket detail |
| GET | `/api/tickets/{id}/history` | Ticket history |
| GET | `/api/cases/{id}/investigation` | Case investigation context |
| POST | `/api/cases/{id}/reason` | AI reasoning (Gemini + RAG) |
| POST | `/api/cases/{id}/resolve` | Resolution decision engine |
| GET | `/api/cases/{id}/review` | Get review states |
| POST | `/api/cases/{id}/review` | Submit human review decision |
| POST | `/api/cases/{id}/analyze` | **Run Mode A/B/C classification** |
| POST | `/api/cases/{id}/clarify` | **Submit clarification answer** |
| POST | `/api/cases/{id}/approve` | **Approve recommendation** |
| POST | `/api/cases/{id}/dismiss` | **Dismiss recommendation** |
| POST | `/api/cases/{id}/escalate` | **Manual escalation** |
| POST | `/api/cases/{id}/resolve-final` | **Mark case resolved** |
| GET | `/api/cases/{id}/audit` | **Full audit trail** |
| GET | `/api/cases/{id}/handover` | **Escalation handover package** |
| GET | `/api/queue` | **Support queue with filters** |
| POST | `/api/chat/send` | **Send customer message through Mode A/B/C pipeline** |
| GET | `/api/chat/conversations/{id}` | **Customer conversations** |
| GET | `/api/chat/messages/{id}` | **Conversation messages** |
| GET | `/api/chat/ticket-messages/{id}` | **Messages for a ticket (agent view)** |
| GET | `/api/chat/customers` | **Customer list for chat** |
| POST | `/api/cases/{id}/need-info` | **Request more information** |
| POST | `/api/cases/{id}/reopen` | **Reopen resolved/dismissed case** |
| GET | `/api/knowledge` | List knowledge documents |
| GET | `/api/knowledge/categories` | Knowledge categories |
| GET | `/api/knowledge/search?q=` | Search knowledge base |
| GET | `/api/knowledge/{id}` | Knowledge document detail |
| GET | `/api/knowledge/{id}/chunks` | Document chunks |

## Demo Cases

The system includes 5 pre-seeded demo cases:

| Case | Mode | Description |
|------|------|-------------|
| TKT-DEMO-001 | A (Routine) | Billing dispute — duplicate charge with clear evidence |
| TKT-DEMO-002 | B (Missing Info) | Slow internet — missing location/timing/scope |
| TKT-DEMO-003 | C (Escalation) | Enterprise repeat complaint — 4th ticket, escalation required |
| TKT-DEMO-004 | Conflict | Site shows operational but has high-severity events |
| TKT-DEMO-005 | Edge Case | Missing subscription data |

## Database Schema (18 Tables)

| Entity | Description |
|--------|-------------|
| `telecom_providers` | Operator reference data (Jio, Airtel, Vi, BSNL) |
| `customers` | Customer accounts with Indian names and +91 phone numbers |
| `plans` | Telecom plans with INR pricing |
| `subscriptions` | Customer-plan-service associations |
| `network_sites` | Cell towers, fiber COs across Indian cities |
| `network_events` | Operational events at network sites |
| `incidents` | Regional outages and service incidents |
| `tickets` | Support tickets and cases |
| `ticket_events` | Ticket history and audit trail |
| `customer_interactions` | Customer contact records |
| `review_states` | Resolution recommendation audit trail |
| `case_state_history` | State machine transition history |
| `clarification_requests` | Mode B clarification questions and answers |
| `escalation_records` | Mode C escalation handover packages |
| `audit_events` | Full audit trail for all case actions |
| `conversations` | Customer chat conversations linked to tickets |
| `conversation_messages` | Individual messages in customer conversations |

## Architecture

SmartResolve is a modular system with a clean separation between the FastAPI API layer, the analysis service layer, deterministic rules, retrieval (RAG), and AI. Data flows from a React SPA → FastAPI → orchestration services → deterministic rule engine (with optional RAG retrieval and Gemini grounding).

### High-Level Flow

```
Customer Message (Chat)  or  Agent Action (Console)
                 |
                 v
  FastAPI Router (src/api/routes.py)  ── Pydantic validation (src/api/schemas.py)
                 |
                 v
  Analysis Orchestrator (src/services/analysis_service.py)
                 |
      +----------+----------+----------+
      |          |          |          |
      v          v          v          v
Context   Retrieval   Deterministic   State
Builder    (RAG)      Rules         Machine
                 |          |
                 v          v
        Gemini Grounding   Mode A / B / C routing
                 |
                 v
    Draft / Clarification / Escalation Handover
                 |
                 v
  SQLite (tickets, audit, review_states, escalation_records,
         case_analysis_results, conversations, ...)
                 |
                 v
  React SPA (Agent Console, Case Detail, Chat, Dashboard)
```

### Backend Modules

| Module | Responsibility |
|--------|----------------|
| `src/api/routes.py` | All REST endpoints (cases, tickets, chat, knowledge, dashboard, queue). Serves the prebuilt React build from `frontend/dist`. |
| `src/api/schemas.py` | Pydantic request/response models and validation. |
| `src/services/analysis_service.py` | Central orchestrator — builds context, runs retrieval, classifies, routes to Mode A/B/C, records audit events, persists results. |
| `src/services/ai_reasoning_service.py` | Grounded AI reasoning (Gemini + RAG) with a structured response parser. |
| `src/services/resolution_service.py` | Resolution decision engine combining deterministic rules, RAG evidence, and AI assessment into a recommendation. |
| `src/services/case_investigation_service.py` | Assembles investigation context (customer, subscription, network, incidents, tickets) for a case. |
| `src/services/dashboard_service.py` | Aggregates dashboard overview/KPI metrics. |
| `src/services/knowledge_service.py` | Knowledge document metadata, categories, and chunk listing. |

### Core PII & Classification

| Module | Responsibility |
|--------|----------------|
| `src/classify.py` | Deterministic classification engine (Mode A/B/C) — pure Python, no Gemini for mode selection. |
| `src/category_detector.py` | Maps free-text customer messages to service categories. |
| `src/draft.py` | Mode A grounded resolution-draft generation (grounding context + Gemini). |
| `src/clarify.py` | Mode B targeted clarification question generation with turn tracking. |
| `src/escalate.py` | Mode C complete escalation handover package builder + persistence. |
| `src/tickets.py` | Case state machine, transition validation, agent override targets. |
| `src/audit.py` | Full audit trail recording for every case action. |
| `src/chat.py` | Customer conversation handling — routes messages through the Mode A/B/C pipeline. |
| `src/config.py` | Configurable thresholds and category→knowledge maps. |

### Rules Engine

| Module | Responsibility |
|--------|----------------|
| `src/rules/escalation.py` | Evaluates the escalation matrix (severity → queue). |
| `src/rules/conflict.py` | Detects conflicting evidence across data sources (blocks auto-drafting). |
| `src/rules/resolution_rules.py` | Deterministic resolution recommendation rules (incident matching, plan checks, etc.). |

### Retrieval (RAG)

| Module | Responsibility |
|--------|----------------|
| `src/retrieval/knowledge_loader.py` | Loads markdown knowledge documents. |
| `src/retrieval/chunker.py` | Deterministic document chunking. |
| `src/retrieval/embedder.py` | Embeds documents/queries via Gemini Embedding 001. |
| `src/retrieval/vector_store.py` | FAISS index load/save (195 vectors, dim 3072). |
| `src/retrieval/retriever.py` | Retrieves top-k relevant chunks with scores. |
| `src/retrieval/context_builder.py` | Builds the retrieval query from case context. |

### AI Layer

| Module | Responsibility |
|--------|----------------|
| `src/ai/gemini_client.py` | Single gateway to Gemini — key loading, throttling, cache, fail-fast behavior. Model pinned to `gemini-3.5-flash` (text) and `gemini-embedding-001` (embeddings). |
| `src/ai/prompts.py` | Prompt templates for reasoning/draft/clarification. |
| `src/ai/models.py` | Typed AI result dataclasses. |

### Database Layer

| Module | Responsibility |
|--------|----------------|
| `src/database/db.py` | SQLite connection + init hook. |
| `src/database/init_db.py` | Schema creation (18 tables). |
| `src/database/seed.py` | India-focused synthetic dataset seeding. |
| `src/database/repositories/*` | Per-entity repositories (customer, ticket, network, incident, plan). |

### Frontend Modules (`frontend/src`)

| Area | Files |
|------|-------|
| Pages | `Overview`, `Cases`, `CaseDetail`, `AgentConsole`, `CustomerChat`, `Knowledge`, `KnowledgeDetail` |
| Dashboard widgets | `KpiCards`, `ActiveIncidents`, `NetworkHealth`, `PriorityCases`, `RecentActivity`, `RegionalImpact`, `TicketWorkload` |
| Common components | `Badges`, `States` |
| Services/Types | `services/api.ts`, `types/*` |

### Key Design Properties

- **API layer is thin** — routes validate with Pydantic and delegate to services.
- **Analysis is orchestrated, not scattered** — `analysis_service.analyze_ticket` is the single entry point for any case.
- **Rules are deterministic** — classification, escalation, and conflict detection never depend on Gemini.
- **AI is grounded** — Gemini only sees customer/operational facts plus retrieved knowledge, and its output is parsed/validated before it can reach the UI.
- **Database is the source of truth** — every mutation persists to SQLite with history and audit.
- **Graceful degradation** — if Gemini or FAISS is unavailable, the system serves deterministic fallbacks or escalates instead of failing.


## India-Focused Synthetic Dataset

- **55 synthetic customers** with Indian names (Sai Kiran Reddy, Ananya Sharma, Rahul Verma, etc.)
- **4 telecom providers**: Reliance Jio, Bharti Airtel, Vodafone Idea (Vi), BSNL
- **30 network sites** across Hyderabad, Bengaluru, Chennai, Mumbai, Pune, Delhi, Vijayawada, Visakhapatnam, Kolkata, Kochi, Ahmedabad, Jaipur, Lucknow, Mysuru, Warangal, Kurnool
- **11 Indian states**: Andhra Pradesh, Telangana, Karnataka, Tamil Nadu, Maharashtra, Delhi, West Bengal, Kerala, Gujarat, Rajasthan, Uttar Pradesh, Madhya Pradesh
- **INR pricing**: ₹279 - ₹4,999/month
- **Indian mobile numbers**: +91 format
- **12 regional incidents** across Indian cities
- **115 support tickets** (110 original + 5 demo cases)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## Running the Application

```bash
python app.py
```

This starts the complete application on `http://localhost:8000`.

The database is automatically initialized and seeded with India-focused synthetic data on first run.

## Running Tests

```bash
python -m pytest tests/ -v
```

- **43 pytest tests:** Classification engine, escalation matrix, conflict detection, state machine, clarification, missing info, agent resolve/close overrides + E2E workflows
- Classification tests do NOT depend on Gemini

## Environment Variables

Environment variables are read via `python-dotenv` from a local `.env` file (which is **gitignored — never committed**). You can also set them in your shell.

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Server port (default: 8000) | No |
| `HOST` | Server host (default: 0.0.0.0) | No |
| `GEMINI_API_KEY` | Google Gemini API key | No (required for AI features) |
| `GEMINI_MODEL` | Gemini text model (default: `gemini-3.5-flash`) | No |
| `GEMINI_EMBEDDING_MODEL` | Gemini embedding model (default: `gemini-embedding-001`) | No |
| `SAFE_RETRIEVAL_THRESHOLD` | Minimum retrieval score (default: 0.35) | No |
| `REPEAT_COMPLAINT_THRESHOLD` | Tickets before escalation (default: 2) | No |
| `CLARIFICATION_MAX_TURNS` | Max clarification rounds (default: 3) | No |

Never hard-code or commit API keys.

## Key Design Principles

- **No automatic resolution** — SmartResolve recommends, humans decide
- **Deterministic over AI** — operational facts always take priority over unsupported AI claims
- **LLM never overrides safety** — deterministic escalation rules cannot be bypassed by AI
- **Transparent confidence** — confidence reasons are explicit and auditable
- **Graceful degradation** — works without Gemini, without FAISS, without complete data
- **Complete handover** — specialists understand the full problem without asking customer to repeat
- **Database is source of truth** — every mutation persists to SQLite with history and audit
- **Synthetic data only** — all customer records are fictional; real provider names used as labels only

## Demo Flow

1. Open `http://localhost:8000`
2. Go to **New Conversation**, select a customer, describe an issue
3. SmartResolve classifies and responds (Mode A/B/C)
4. Go to **Agent Console**, see the case in the queue with full transcript
5. Run analysis, review the recommendation/clarification/escalation
6. Take action: Approve → Resolve, or Need Info, or Dismiss, or Escalate
7. Verify the queue, overview, audit trail, and history all update immediately

## Local URL

http://localhost:8000
