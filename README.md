TRACK_ID=PS6

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
| Knowledge Base | Markdown documents, deterministic chunking, lexical search |
| AI/LLM | Gemini (planned) |

## Current Implementation (Stage 5 - Grounded Knowledge Base)

This release adds the complete grounded knowledge base foundation:

- **30 Knowledge Documents** across 8 categories: Network, Connectivity, Billing, Roaming, Device, Support, Escalation, Enterprise
- **Deterministic Chunking** - documents are split into 300-700 word chunks with section context preserved
- **Lexical Search** - searches across titles, categories, tags, section headings, and content
- **Knowledge API** - list, get, search, categories, sections, and chunks endpoints
- **Knowledge UI** - browse documents by category, search across the knowledge base, read documents with table of contents navigation
- **Citation-Ready Chunks** - every chunk is traceable to its source document, section, and chunk index
- **Category Routing** - maps ticket categories to relevant knowledge base categories
- **No External Dependencies** - no Gemini, no embeddings, no FAISS, no vector search

### Knowledge Categories

| Category | Documents | Topics |
|----------|-----------|--------|
| Network | 5 | Incident response, health monitoring, cell site operations, technology overview, spectrum management |
| Connectivity | 5 | Mobile data troubleshooting, Wi-Fi calling, APN configuration, service activation, coverage issues |
| Billing | 4 | Billing cycles, data throttling, invoice disputes, payment methods |
| Support | 5 | Customer service standards, ticket management, account security, technical troubleshooting, retention |
| Escalation | 3 | Escalation procedures, SLA management, complaint handling |
| Enterprise | 3 | Enterprise SLAs, support operations, account management |
| Device | 3 | Device compatibility, SIM management, device financing |
| Roaming | 2 | Roaming policies, international troubleshooting |

### Deterministic Rules

- Documents are chunked by section headings (## level)
- Chunks target 300-700 words for optimal retrieval
- Search scores: title matches (10x), category matches (5x), heading matches (8x), content matches (1x)
- Category routing maps ticket types to relevant knowledge categories
- All chunks include citation metadata: document_id, section_heading, chunk_index

### Search and Retrieval

- Lexical search across all document content, headings, titles, tags, and categories
- Results ranked by relevance score with preview snippets
- Category filtering available for scoped searches
- No embeddings, no vectors, no external AI services required

## Previous Stages

### Stage 4 - Case Investigation Workflow

- Case List with search, filters, pagination, desktop table and mobile card layouts
- Case Detail investigation workspace with customer profile, service, network, incidents, history
- Investigation Service with deterministic readiness calculation and known/missing facts
- Partial Data Handling and Readiness Indicator (READY / PARTIAL / INSUFFICIENT DATA)

### Stage 3 - Operations Dashboard

- KPI cards, network health, ticket workload, active incidents, regional impact
- Priority cases with scoring, recent activity feed

### Stage 2 - Telecom Data Layer

- 9-table SQLite schema with 55 customers, 8 plans, 63 subscriptions, 18 network sites
- 42 network events, 12 incidents, 110 tickets, 631 ticket events, 631 interactions

### Stage 1 - Foundation

- FastAPI backend, React frontend, Tailwind CSS, single entry point

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
| GET | `/api/knowledge` | List knowledge documents |
| GET | `/api/knowledge/categories` | List knowledge categories |
| GET | `/api/knowledge/search?q=` | Search knowledge base |
| GET | `/api/knowledge/{id}` | Knowledge document detail |
| GET | `/api/knowledge/{id}/chunks` | Document chunks for citation |

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
│   │   ├── case_investigation_service.py
│   │   └── knowledge_service.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── knowledge_loader.py
│   │   └── chunker.py
│   ├── ai/                 # (planned)
│   └── rules/              # (planned)
├── data/
│   └── smartresolve.db
├── knowledge/
│   ├── manifest.json
│   ├── network/            # 5 documents
│   ├── connectivity/       # 5 documents
│   ├── billing/            # 4 documents
│   ├── roaming/            # 2 documents
│   ├── device/             # 3 documents
│   ├── support/            # 5 documents
│   ├── escalation/         # 3 documents
│   └── enterprise/         # 3 documents
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── common/     # States, Badges
    │   │   └── dashboard/  # KpiCards, NetworkHealth, etc.
    │   ├── pages/
    │   │   ├── Overview.tsx
    │   │   ├── Cases.tsx
    │   │   ├── CaseDetail.tsx
    │   │   ├── Knowledge.tsx
    │   │   └── KnowledgeDetail.tsx
    │   ├── services/api.ts
    │   └── types/
    │       ├── index.ts
    │       ├── case.ts
    │       └── knowledge.ts
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
- No resolution engine or escalation logic
- Evidence and citations page is a placeholder
- Knowledge base uses lexical search only (no semantic search)

## Future Stages

- Stage 6: Deterministic business rules
- Stage 7: Gemini reasoning engine
- Stage 8: RAG retrieval with FAISS
- Stage 9: Evidence scoring and citations
- Stage 10: Final polish and testing

## Local URL

http://localhost:8000
