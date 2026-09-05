TRACK_ID=PS6

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
| **Center** | Case workspace with Analyze button, mode-specific display, classification details, audit trail |
| **Right** | Customer/account context with service, network, incidents, investigation status |

### Mode Displays

- **Mode A (Routine):** Green grounded recommendation with draft, evidence, citations, limitations, and Approve/Dismiss/Escalate actions
- **Mode B (Missing Info):** Amber information-needed panel with targeted question and Send Question action
- **Mode C (Escalation):** Red human-review-required panel with escalation reasons, confirmed facts, missing info, previous tickets, recommendations, and Open Human Review/Add Note actions

### Queue Filters

- All, Routine, Needs Information, Human Review, Pending Approval, Resolved, Analyzing

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

## Database Schema (16 Tables)

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

## Architecture

```
Customer Message
       |
       v
Account + Operational Context
       |
       v
Deterministic Rules (classify.py)
       |
       +------------------+------------------+
       |                  |                  |
       v                  v                  v
   MODE A             MODE B             MODE C
   Routine            Missing Info        Escalation
       |                  |                  |
       v                  v                  v
  Gemini Draft      One Question        Handover
       |                  |                  |
       v                  v                  v
  Citations         Continue Case       Human Queue
       |
       v
  Pending Approval
       |
       v
  Human Decision
```

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
python -m tests.test_decision_engine
```

Tests the deterministic Mode A/B/C classification without requiring Gemini.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Server port (default: 8000) | No |
| `HOST` | Server host (default: 0.0.0.0) | No |
| `GEMINI_API_KEY` | Google Gemini API key | No (required for AI features) |
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
- **Synthetic data only** — all customer records are fictional; real provider names used as labels only

## Local URL

http://localhost:8000
