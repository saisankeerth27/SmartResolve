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

## Current Foundation (v0.1)

This initial commit provides:

- FastAPI application entry point (`app.py`)
- Health check endpoint (`GET /api/health`)
- Frontend serving mechanism (serves React build from `frontend/dist/`)
- Modular backend structure (`src/api`, `src/core`, `src/database`, `src/services`, `src/ai`, `src/retrieval`, `src/rules`)
- SQLite database initialization
- Configuration module with environment variable support
- React/TypeScript frontend with enterprise telecom operations UI
- Responsive sidebar navigation with dashboard placeholder

## Installation

### Backend

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
npm run build
```

## Running the Application

```bash
python app.py
```

This starts the complete application on `http://localhost:8000`.

A single terminal is all that is needed.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Server port (default: 8000) | No |
| `GEMINI_API_KEY` | Google Gemini API key | No (required for AI features) |

Never hard-code or commit API keys.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/docs` | OpenAPI documentation |
| GET | `/*` | Serves frontend (or fallback message) |

## Project Structure

```
SmartResolve/
├── app.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── README.md
├── .gitignore
├── .python-version
├── src/
│   ├── api/               # FastAPI routes and schemas
│   ├── core/              # Configuration and logging
│   ├── services/          # Business logic services
│   ├── database/          # SQLite database modules
│   ├── ai/                # Gemini integration
│   ├── retrieval/         # RAG and FAISS modules
│   └── rules/             # Deterministic business rules
├── data/                  # SQLite database files
├── knowledge/             # Telecom policy documents
├── index/                 # FAISS indices
└── frontend/
    └── dist/              # Built React frontend
```

## Local URL

http://localhost:8000
