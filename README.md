# AgentForge

AgentForge is a monorepo for a portfolio-grade AI internship workflow platform.

This first step only establishes the project foundation:

- `apps/web`: Next.js frontend skeleton
- `apps/api`: FastAPI backend skeleton
- `packages/shared`: shared types and constants
- `packages/prompts`: reusable agent prompt assets
- `infra`: local infrastructure configuration
- `docs`: architecture, database, and agent design notes

## Prerequisites

- Node.js 20+
- Python 3.12 recommended
- Docker Desktop

## Local Infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL, Redis, and Qdrant.

## Local LLM Adapter

AgentForge now has an LLM provider adapter layer. Ollama is the first provider,
but no existing pipeline depends on the LLM yet.

```bash
ollama pull qwen3:8b
```

Configure the provider in `.env`:

```text
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
```

Prompt templates are versioned in `packages/prompts`. The first LLM reasoner
prompt is `internship_reasoning_v1.md`, loaded by prompt name
`internship_reasoning` and version `v1`.

LLM model settings are routed through an in-code model registry:

```text
internship_reasoning -> ollama / qwen3:8b / temperature 0.2 / JSON enabled
cover_letter -> disabled placeholder
interview_prep -> disabled placeholder
output_validation -> ollama / qwen3:8b / temperature 0.0 / JSON enabled
```

LLM providers are routed through an in-code provider registry. The first
registered provider is:

```text
ollama -> OllamaProvider -> http://localhost:11434 -> enabled
```

## Backend

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run database migrations after PostgreSQL is running:

```bash
cd apps/api
alembic upgrade head
```

Create demo backend data:

```bash
cd apps/api
python scripts/seed.py
```

Run backend tests:

```bash
cd apps/api
pytest
pytest -q
pytest --cov
pytest --cov=app --cov-report=term-missing
```

Useful backend endpoints:

```text
GET /health
POST /users
GET /users/{id}
POST /workspaces
GET /workspaces
GET /workspaces/{id}
POST /documents/upload
GET /documents
GET /documents/{id}
POST /internships
GET /internships
GET /internships/{id}
PATCH /internships/{id}?request_user_id={user_id}
DELETE /internships/{id}?request_user_id={user_id}
POST /applications
GET /applications
GET /applications/{id}
PATCH /applications/{id}?request_user_id={user_id}
GET /agents/registry
POST /agents/planner/plan
POST /agents/evidence-analyzer/analyze
POST /agents/llm-reasoner/reason
POST /agents/output-validator/validate
POST /agents/internship-match-graph/run
```

Uploaded documents are stored locally in `storage/documents/`. The API accepts
PDF, DOCX, and TXT files up to 10 MB.

Planner contract example:

```bash
curl -X POST http://localhost:8000/agents/planner/plan \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Compare my CV with this backend internship and tell me what to improve.",
    "workspace_id": "workspace_uuid",
    "user_id": "user_uuid",
    "document_id": "cv_document_uuid",
    "internship_post_id": "internship_uuid"
  }'
```

Evidence analyzer contract example:

```bash
curl -X POST http://localhost:8000/agents/evidence-analyzer/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "workspace_uuid",
    "user_id": "user_uuid",
    "cv_chunks": [],
    "min_score": 0.45,
    "max_chunks": 3
  }'
```

LLM reasoner contract example:

```bash
curl -X POST http://localhost:8000/agents/llm-reasoner/reason \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "workspace_uuid",
    "user_id": "user_uuid",
    "context_text": "Context Builder output text",
    "deterministic_report": {
      "match_score": 81.19,
      "summary": "Deterministic match summary",
      "matched_skills": [],
      "missing_skills": [],
      "recommendations": [],
      "source_chunk_ids": []
    }
  }'
```

Output validator contract example:

```bash
curl -X POST http://localhost:8000/agents/output-validator/validate \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "workspace_uuid",
    "user_id": "user_uuid",
    "deterministic_report": {
      "match_score": 81,
      "summary": "Deterministic summary",
      "matched_skills": [],
      "missing_skills": [],
      "recommendations": [],
      "source_chunk_ids": []
    },
    "llm_reasoning": {
      "prompt_name": "internship_reasoning",
      "prompt_version": "v1",
      "reasoning_summary": "Reasoning summary",
      "strengths": [],
      "weaknesses": [],
      "improvement_plan": [],
      "confidence": 0.8,
      "risk_flags": []
    },
    "llm_match_score": 98
  }'
```

Agent registry example:

```bash
curl http://localhost:8000/agents/registry
```

The backend also defines a shared `InternshipPipelineState` model for the future
LangGraph migration. It is not connected to the current pipeline yet.

An experimental LangGraph pipeline is available separately:

```bash
curl -X POST http://localhost:8000/agents/internship-match-graph/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Compare my CV with this backend internship.",
    "workspace_id": "workspace_uuid",
    "user_id": "user_uuid",
    "document_id": "cv_document_uuid",
    "internship_post_id": "internship_uuid"
  }'
```

The existing manual pipeline remains available at
`POST /agents/internship-match/run`.

## Frontend

```bash
npm install
npm.cmd --workspace apps/web run dev
```

## CI

CI runs on every push and pull request through GitHub Actions:

| Workflow | Runtime | Checks |
| --- | --- | --- |
| `.github/workflows/backend.yml` | Python 3.12 | install requirements, `compileall`, `pytest -q`, `pytest --cov=app` |
| `.github/workflows/frontend.yml` | Node.js 20 | `npm ci`, frontend typecheck, frontend lint |

## Build Order

1. Create monorepo
2. Setup Docker Compose
3. Setup PostgreSQL
4. Setup FastAPI
5. Setup Next.js
6. Connect frontend to backend
7. Add database models
8. Add document upload
9. Add internship post CRUD
10. Add simple CV/job matching logic
11. Add Qdrant RAG
12. Add LangGraph agents
