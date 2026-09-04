TRACK_ID=PS6

# SmartResolve

**Telecom Operations Resolution Assistant**

SmartResolve is a grounded AI-assisted telecom operations system that combines customer information, operational records, support tickets, telecom policies, local RAG retrieval, Gemini reasoning, deterministic business rules, evidence/citations, and human escalation into a unified resolution workspace.

The system resolves what the available evidence supports, asks for missing information when required, and escalates when the available evidence or knowledge is insufficient.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Database | SQLite |
| AI/LLM | Gemini (planned) |
| RAG | FAISS, NumPy (planned) |

## Current Implementation (Stage 2 - Data Layer)

This release adds the core telecom operations data model:

- **SQLite database** with 9 relational tables and proper foreign keys
- **Realistic seed data** with 55 customers, 8 plans, 63 subscriptions, 18 network sites, 42 network events, 12 incidents, 110 tickets, and 110 customer interactions
- **Repository layer** with clean data access methods
- **REST API endpoints** with filtering and pagination
- **Frontend integration** with live data from the backend API

### Database Schema

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

### Intentional Scenarios

The seed data includes realistic scenarios for testing:
- Customers with poor 5G performance linked to congested sites
- Regional outages affecting multiple customers
- Repeated tickets for the same service
- Issues unrelated to any network event
- Billing complaints with healthy network status
- Enterprise customers requiring different handling
- Failed previous troubleshooting attempts
- Resolved incidents followed by new complaints

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/dashboard` | Dashboard statistics |
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

All collection endpoints support `page` and `page_size` query parameters.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
```

This starts the complete application on `http://localhost:8000`.

A single terminal is all that is needed. The database is automatically initialized and seeded on first run.

## Seed Data Generation

The seed data is generated deterministically using `src/database/seed.py` with a fixed random seed (42). To regenerate:

```python
from src.database.db import get_connection
from src.database.seed import seed_database
conn = get_connection()
seed_database(conn, force=True)
conn.close()
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Server port (default: 8000) | No |
| `GEMINI_API_KEY` | Google Gemini API key | No (required for AI features) |

Never hard-code or commit API keys.

## Project Structure

```
SmartResolve/
├── app.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── README.md
├── .gitignore
├── .python-version
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
│   ├── services/           # (planned)
│   ├── ai/                 # (planned)
│   ├── retrieval/          # (planned)
│   └── rules/              # (planned)
├── data/
│   └── smartresolve.db     # SQLite database with seed data
├── knowledge/              # (planned)
├── index/                  # (planned)
└── frontend/
    └── dist/               # Built React frontend
```

## Current Limitations

- No Gemini AI integration yet
- No RAG or FAISS retrieval yet
- No resolution engine or escalation logic
- No knowledge base documents
- Frontend shows basic data tables only

## Future Stages

- Stage 3: Gemini integration and knowledge base
- Stage 4: RAG retrieval with FAISS
- Stage 5: Deterministic business rules
- Stage 6: Resolution engine
- Stage 7: Escalation logic
- Stage 8: Evidence scoring
- Stage 9: Advanced dashboard
- Stage 10: Final polish and testing

## Local URL

http://localhost:8000
