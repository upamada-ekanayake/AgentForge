# AgentForge

[![Backend CI](https://github.com/upamada-ekanayake/AgentForge/actions/workflows/backend.yml/badge.svg)](https://github.com/upamada-ekanayake/AgentForge/actions/workflows/backend.yml)
[![Frontend CI](https://github.com/upamada-ekanayake/AgentForge/actions/workflows/frontend.yml/badge.svg)](https://github.com/upamada-ekanayake/AgentForge/actions/workflows/frontend.yml)

AgentForge is a portfolio-grade AI internship workflow platform. It combines a
Next.js frontend, FastAPI backend, PostgreSQL, Qdrant vector search, document
processing, deterministic agent workflows, optional LLM infrastructure, and an
agent execution visualizer.

Reviewer links:

- [Architecture](docs/architecture.md)
- [Agent Design](docs/agent-design.md)
- [Database Design](docs/database.md)
- [Demo Script](docs/demo-script.md)
- [Roadmap](ROADMAP.md)

Repository layout:

- `apps/web`: Next.js frontend
- `apps/api`: FastAPI backend
- `packages/shared`: shared types and constants
- `packages/prompts`: reusable and versioned prompt assets
- `infra`: local infrastructure configuration
- `docs`: architecture, database, demo, and agent design notes

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
GET /agents/runs
GET /agents/runs/{id}
POST /agents/planner/plan
POST /agents/evidence-analyzer/analyze
POST /agents/llm-reasoner/reason
POST /agents/output-validator/validate
POST /agents/internship-match/run
POST /agents/internship-match-graph/run
POST /agents/internship-rank/run
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

The backend also defines a shared `InternshipPipelineState` model used by the
experimental LangGraph pipeline.

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

Main frontend routes:

```text
/dashboard
/documents
/internship-match
/internship-rank
/agent-runs
```

The Agent Execution Visualizer at `/agent-runs` shows recent agent runs, a
pipeline node graph, a timeline fallback, and input/output payload inspection.

## CI

CI runs on every push and pull request through GitHub Actions:

| Workflow | Runtime | Checks |
| --- | --- | --- |
| `.github/workflows/backend.yml` | Python 3.12 | install requirements, `compileall`, `pytest -q`, `pytest --cov=app` |
| `.github/workflows/frontend.yml` | Node.js 20 | `npm ci`, frontend typecheck, frontend lint |

## Current Status

Completed:

- Core full-stack platform
- PostgreSQL schema and migrations
- Document upload, parsing, chunking, embeddings, and Qdrant indexing
- Manual deterministic internship match pipeline
- Experimental LangGraph pipeline
- Workspace-wide internship ranking
- Optional LLM adapter, prompt/model/provider registries, and output validator
- Agent registry and agent execution visualizer
- Backend and frontend CI
- Unit test foundation

Current hardening focus:

- deterministic registry tests
- opt-in integration tests
- deployment preparation
