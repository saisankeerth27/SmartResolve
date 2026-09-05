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
| Knowledge Base | Markdown documents, deterministic chunking, lexical search |
| AI/LLM | Gemini 3.5 Flash (text), Gemini Embedding 001 (embeddings) |
| Vector Search | FAISS (local, in-memory) |
| Rules Engine | Python deterministic rule evaluation |

## Current Implementation (Stage 7 - Resolution Decision Engine)

This release adds the Resolution Decision Engine:

- **Deterministic Rule Engine** - evaluates operational conditions (degraded sites, active incidents, billing cases, repeated tickets, enterprise customers, AI conflicts) with explicit rule precedence
- **Resolution Service** - combines deterministic rules, operational evidence, retrieved knowledge, and grounded AI reasoning into a structured recommendation
- **AI/Rule Separation** - clearly distinguishes deterministic facts, rule results, AI reasoning, and human decisions
- **Evidence Model** - every recommendation references operational, knowledge, or AI evidence with source tracking
- **Confidence Model** - transparent confidence calculation combining evidence completeness, retrieval quality, AI confidence, rule agreement, and ambiguity
- **Human-in-the-Loop** - requires human review for insufficient evidence, conflicting data, critical cases, enterprise customers, active incidents, and low AI confidence
- **Conflict Handling** - when AI assessment contradicts operational data, the system flags the conflict and escalates rather than claiming an unsupported conclusion
- **Resolution UI** - expandable evidence display, deterministic findings, knowledge sources, AI assessment, alternative actions, and human decision controls (Approve/Need Info/Escalate/Dismiss)
- **Review Audit Trail** - records recommendation, confidence, reviewer decisions, and timestamps without modifying original customer/ticket data
- **Resolution API** - POST `/api/cases/{id}/resolve` and POST `/api/cases/{id}/review`

### Resolution Categories

| Category | Description |
|----------|-------------|
| `network_investigation` | Review serving site and network events |
| `incident_review` | Review active regional incident |
| `customer_troubleshooting` | Standard device and connectivity troubleshooting |
| `billing_review` | Review billing transactions and plan terms |
| `device_diagnostics` | Verify device compatibility and SIM status |
| `service_configuration_review` | Review provisioning and account settings |
| `monitoring` | Monitor conditions, escalate if worsened |
| `human_escalation` | Escalate to specialist team |
| `insufficient_evidence` | Collect additional information |

### Rule Precedence

1. Missing critical evidence (customer, subscription, network)
2. Safety/human-review requirements (critical priority, enterprise customer)
3. Active incident relationship
4. Strong deterministic operational facts (degraded site, active events)
5. Case category (billing, voice, device, roaming)
6. Retrieved knowledge
7. AI assessment
8. Secondary recommendations

### India-Focused Synthetic Dataset

- **55 synthetic customers** with Indian names (Sai Kiran Reddy, Ananya Sharma, Rahul Verma, etc.)
- **4 telecom providers**: Reliance Jio, Bharti Airtel, Vodafone Idea (Vi), BSNL
- **30 network sites** across Hyderabad, Bengaluru, Chennai, Mumbai, Pune, Delhi, Vijayawada, Visakhapatnam, Kolkata, Kochi, Ahmedabad, Jaipur, Lucknow, Mysuru, Warangal, Kurnool
- **11 Indian states**: Andhra Pradesh, Telangana, Karnataka, Tamil Nadu, Maharashtra, Delhi, West Bengal, Kerala, Gujarat, Rajasthan, Uttar Pradesh, Madhya Pradesh
- **INR pricing**: ₹279 - ₹4,999/month
- **Indian mobile numbers**: +91 format
- **12 regional incidents** across Indian cities
- **110 support tickets** with India-specific scenarios

### Architecture

```
Operational Data (SQLite)
       |
       v
Investigation Context
       |
       +--------------------+
       |                    |
       v                    v
Deterministic Rules      Local RAG (FAISS)
       |                    |
       |                    v
       |              Gemini Embeddings
       |                    |
       |                    v
       |                 Gemini 3.5 Flash
       |                    |
       +---------+----------+
                 |
                 v
       Resolution Decision Engine
                 |
                 v
        Structured Recommendation
                 |
                 v
             Human Review
```

## Previous Stages

### Stage 6 - Gemini RAG + AI Reasoning

- Gemini 3.5 Flash for text generation, Gemini Embedding 001 for embeddings
- Local FAISS vector store with 195 chunks, dimension 3072
- Grounded retrieval with category filtering and relevance threshold
- Structured AI reasoning output with citations, confidence, and limitations
- Graceful degradation when Gemini is unavailable

### Stage 5 - Grounded Knowledge Base

- 30 Markdown documents across 8 categories
- Deterministic chunking (300-700 words per chunk)
- Lexical search with relevance scoring
- Citation-ready chunks with document/section/position metadata

### Stage 4 - Case Investigation Workflow

- Case list with search, filters, pagination
- Investigation workspace with customer, service, network, incidents, history
- Deterministic readiness calculation (READY / PARTIAL / INSUFFICIENT DATA)

### Stage 3 - Operations Dashboard

- KPI cards, network health, ticket workload, active incidents
- Regional impact, priority cases, recent activity feed

### Stage 2 - Telecom Data Layer

- 9-table SQLite schema with India-focused sample data
- 55 customers, 11 plans, 63 subscriptions, 30 network sites
- 42 network events, 12 incidents, 110 tickets

### Stage 1 - Foundation

- FastAPI backend, React frontend, Tailwind CSS, single entry point on port 8000

## Database Schema

| Entity | Description |
|--------|-------------|
| `telecom_providers` | Operator/provider reference data (Jio, Airtel, Vi, BSNL) |
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
| GET | `/api/knowledge` | List knowledge documents |
| GET | `/api/knowledge/categories` | Knowledge categories |
| GET | `/api/knowledge/search?q=` | Search knowledge base |
| GET | `/api/knowledge/{id}` | Knowledge document detail |
| GET | `/api/knowledge/{id}/chunks` | Document chunks |

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

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Server port (default: 8000) | No |
| `HOST` | Server host (default: 0.0.0.0) | No |
| `GEMINI_API_KEY` | Google Gemini API key | No (required for AI features) |

Never hard-code or commit API keys.

## Key Design Principles

- **No automatic resolution** - SmartResolve recommends, humans decide
- **Deterministic over AI** - operational facts always take priority over unsupported AI claims
- **Causation vs correlation** - never claim an incident caused a problem unless evidence establishes it
- **Transparent confidence** - confidence reasons are explicit and auditable
- **Graceful degradation** - works without Gemini, without FAISS, without complete data
- **Synthetic data only** - all customer records are fictional; real provider names used as labels only

## Local URL

http://localhost:8000
