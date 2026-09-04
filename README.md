TRACK_ID=PS04

# SmartResolve

**Telecom Operations Resolution Assistant**

SmartResolve is a grounded AI-assisted telecom operations system that combines customer information, operational records, support tickets, telecom policies, local RAG retrieval, Gemini reasoning, deterministic business rules, evidence/citations, and human escalation into a unified resolution workspace.

The system resolves what the available evidence supports, asks for missing information when required, and escalates when the available evidence or knowledge is insufficient.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Router |
| Database | SQLite |
| AI/LLM | Gemini (planned) |
| RAG | FAISS, NumPy (planned) |

## Current Implementation (Stage 4 - Case Investigation Workflow)

This release adds the complete case investigation workflow:

- **Case List** with search (ticket number, customer name/number, subject), status/priority/category filters, pagination, desktop table and mobile card layouts
- **Case Detail** investigation workspace with customer profile, service/subscription, network context, active incidents, previous tickets, ticket timeline, customer interactions
- **Investigation Service** with deterministic readiness calculation, known facts extraction, and missing information identification
- **Deterministic Investigation Rules** that correlate ticket category with network status, identify regional incidents, and flag repeated customer issues
- **Partial Data Handling** - system works gracefully with incomplete data (missing subscription, no network site, no incidents)
- **Readiness Indicator** - READY / PARTIAL / INSUFFICIENT DATA based on available context
- **React Router** navigation between case list and case detail views

### Investigation Readiness Logic

- **READY**: Customer exists, ticket exists, subscription linked, network site available
- **PARTIAL**: Core ticket/customer exists but subscription or network context missing
- **INSUFFICIENT DATA**: Critical context missing (e.g., customer record not found)

### Deterministic Rules

- Network site status "degraded" flagged as relevant to customer issue
- Active incidents in customer's region identified as potentially related
- Previous tickets in same category counted and surfaced
- Data overage detected when usage exceeds plan limit
- Site capacity above 85% flagged as high utilization

### Known vs Missing Information

The system extracts what it knows from the database and identifies gaps:
- Known: customer, subscription, plan, network site, incidents, ticket history, interactions
- Missing: device model, exact location, signal strength, symptom details

This prepares context for future AI reasoning without hallucinating data.

### Case Investigation Scenarios

The seed data supports testing these scenarios:
- Network issue with active regional incident
- Network issue without active incident
- Billing issue with healthy network
- Customer with repeated tickets in same category
- High data usage exceeding plan limits
- Enterprise vs consumer customer handling

## Database Schema

| Entity | Description |
|--------|-------------|
| `customers` | Customer accounts with segments and status |
| `plans` | Telecom plan definitions |
| `subscriptions` | Customer-plan-service associations |
| `network_sites` | Cell towers, fiber COs, and network infrastructure |
| `network_events` | Operational events at network sites |
| `incidents` | Regional outages and service incidents |
| `tickets` | Support tickets and cases |
| `ticket_events` | Ticket history and audit trail |
| `customer_interactions` | Customer contact records |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/dashboard` | Dashboard statistics |
| GET | `/api/dashboard/overview` | Full operations dashboard data |
| GET | `/api/customers` | List customers with search/filter |
| GET | `/api/customers/{id}` | Customer detail |
| GET | `/api/customers/{id}/subscriptions` | Customer subscriptions |
| GET | `/api/customers/{id}/tickets` | Customer tickets |
| GET | `/api/customers/{id}/interactions` | Customer interactions |
| GET | `/api/plans` | List all plans |
| GET | `/api/network/sites` | List network sites |
| GET | `/api/network/sites/{id}` | Network site detail |
| GET | `/api/network/sites/{id}/events` | Site events |
| GET | `/api/incidents` | List incidents |
| GET | `/api/incidents/active` | Active incidents only |
| GET | `/api/incidents/{id}` | Incident detail |
| GET | `/api/tickets` | List tickets with filters |
| GET | `/api/tickets/{id}` | Ticket detail with history |
| GET | `/api/tickets/{id}/history` | Ticket event history |
| GET | `/api/cases/{id}/investigation` | Case investigation context |

All collection endpoints support `page` and `page_size` query parameters.

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

A single terminal is all that is needed. The database is automatically initialized and seeded on first run.

## Project Structure

```
SmartResolve/
├── app.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── README.md
├── src/
│   ├── api/
│   │   ├── routes.py       # API endpoints
│   │   └── schemas.py      # Pydantic models
│   ├── core/
│   │   ├── config.py       # Configuration
│   │   └── logging_config.py
│   ├── database/
│   │   ├── db.py           # Connection management
│   │   ├── init_db.py      # Schema initialization
│   │   ├── seed.py         # Seed data generator
│   │   └── repositories/
│   │       ├── customer_repository.py
│   │       ├── ticket_repository.py
│   │       ├── network_repository.py
│   │       ├── incident_repository.py
│   │       └── plan_repository.py
│   ├── services/
│   │   ├── dashboard_service.py
│   │   └── case_investigation_service.py
│   ├── ai/                 # (planned)
│   ├── retrieval/          # (planned)
│   └── rules/              # (planned)
├── data/
│   └── smartresolve.db
├── knowledge/              # (planned)
├── index/                  # (planned)
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── common/     # States, Badges
    │   │   └── dashboard/  # KpiCards, NetworkHealth, etc.
    │   ├── pages/
    │   │   ├── Overview.tsx
    │   │   ├── Cases.tsx
    │   │   └── CaseDetail.tsx
    │   ├── services/api.ts
    │   └── types/
    │       ├── index.ts
    │       └── case.ts
    └── dist/
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Server port (default: 8000) | No |
| `GEMINI_API_KEY` | Google Gemini API key | No (required for AI features) |

Never hard-code or commit API keys.

## Current Limitations

- No Gemini AI integration yet
- No RAG or FAISS retrieval yet
- No resolution engine or escalation logic
- No knowledge base documents
- Evidence and citations page is a placeholder

## Future Stages

- Stage 5: RAG retrieval with FAISS
- Stage 6: Deterministic business rules
- Stage 7: Resolution engine
- Stage 8: Escalation logic
- Stage 9: Evidence scoring
- Stage 10: Final polish and testing

## Local URL

http://localhost:8000
