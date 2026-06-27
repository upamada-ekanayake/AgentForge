# AgentForge Demo Script And Reviewer Guide

AgentForge is a full-stack AI internship workflow platform. The demo should show
that it is more than a RAG experiment: it has product screens, database-backed
workflows, document intelligence, retrieval safety, deterministic scoring, and a
parallel LangGraph orchestration path.

## Local Setup

Start local infrastructure:

```powershell
docker compose up -d
```

Start the backend:

```powershell
cd apps/api
.venv\Scripts\Activate.ps1
alembic upgrade head
python scripts\seed.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend in a second terminal:

```powershell
npm install
npm.cmd --workspace apps/web run dev
```

Open:

```text
http://localhost:3000/dashboard
```

Useful backend checks:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/workspaces
Invoke-RestMethod http://localhost:8000/internships
```

The backend API docs are available at:

```text
http://localhost:8000/docs
```

## Demo Data Preparation

Use the seeded workspace and internship posts, or create your own through the
API. For the clearest demo, prepare one small TXT CV that mentions a few relevant
skills, for example:

```text
Python, FastAPI, SQL, PostgreSQL, Git, API development, communication,
product thinking, AI tools, and documentation.
```

Upload it from the Documents page, then index it so Qdrant can retrieve it.
The document flow is:

```text
Upload
  -> local storage
  -> text extraction
  -> recursive chunking
  -> PostgreSQL document_chunks
  -> embedding generation
  -> Qdrant indexing
```

If retrieval quality is weak, use a query that names the target skills clearly,
such as:

```text
Compare backend FastAPI PostgreSQL API development skills with my CV and tell me what to improve.
```

This avoids making the demo depend on ambiguous wording.

## Main Demo Flow

### 1. Show The Dashboard

Explain:

```text
This is a monorepo app with a Next.js frontend, FastAPI backend, PostgreSQL for
structured data, and Qdrant for semantic document search.
```

Show that real data is flowing through the stack:

```text
Frontend -> API client -> FastAPI -> PostgreSQL
```

### 2. Upload And Index A CV

Go to the Documents page.

Show:

- drag-and-drop upload
- document status
- stored filename
- upload date

Explain:

```text
The backend extracts text from PDF, DOCX, or TXT files, chunks it with a
recursive text splitter, stores chunks in PostgreSQL, and indexes embeddings in
Qdrant.
```

Do not overclaim scanned PDF support. Current parsing supports regular PDF,
DOCX, and TXT text extraction.

### 3. Run Manual Internship Match

Go to the Internship Match page.

Select:

- workspace
- ready CV document
- internship post
- Manual Pipeline

Use a query such as:

```text
Compare backend FastAPI PostgreSQL API development skills with my CV and tell me what to improve.
```

Click Run.

Show:

- planner result
- retrieval summary
- retrieval quality
- evidence kept/discarded
- context summary
- match score
- matched skills
- missing skills
- recommendations

Explain:

```text
The manual pipeline is the trusted path. It runs normal Python service calls in
order: Planner, Retriever, Evidence Analyzer, Context Builder, and Match Report
Generator.
```

### 4. Run LangGraph Internship Match

Switch Execution Mode to LangGraph Pipeline and run the same query.

Show:

- LangGraph Pipeline badge
- completed stages
- same or comparable match report
- warnings/errors if any

Explain:

```text
LangGraph is currently experimental. It uses the same business logic, but runs
the workflow through a shared graph state. This proves the orchestration layer
can change without rewriting each agent.
```

Point out the key difference:

```text
Manual pipeline returns a flattened response for the UI.
LangGraph returns a state-based response with completed stages, warnings, errors,
and the deterministic report.
```

### 5. Compare Results

Compare:

- match score
- retrieval quality
- evidence count
- matched skills
- recommendations

Explain:

```text
The important part is not that LangGraph gives a different answer. The important
part is that both orchestration engines can run the same workflow and produce
consistent results.
```

Also show the safety behavior when useful:

```text
If retrieval is weak, the Evidence Analyzer can stop the pipeline before a
confident report is generated.
```

### 6. Run Internship Ranking

Go to the Internship Rank page.

Select:

- workspace
- CV document

Click Rank internships.

Show:

- ranked internship cards
- match score
- retrieval quality
- missing skills
- recommendations

Explain:

```text
The ranking workflow applies the same deterministic match logic across active
internship posts in the workspace and sorts them by match score.
```

## Two-Minute Demo Version

Use this when the interviewer asks for a quick overview.

```text
AgentForge is an AI internship workflow platform. It lets a user upload a CV,
extracts and chunks the document, indexes it into Qdrant with embeddings, and
then compares the CV against internship posts.

The core workflow is deterministic first: Planner decides the task, Retriever
gets CV evidence, Evidence Analyzer filters weak chunks, Context Builder prepares
clean context, and Match Report Generator returns a score, matched skills,
missing skills, and recommendations.

The interesting architecture choice is that I built two orchestration paths:
a manual production-style pipeline and an experimental LangGraph pipeline. The
frontend can switch between them and compare results.

I also kept the LLM layer optional. There is an LLM adapter, prompt registry,
model registry, provider registry, and output validator, but the main scoring
does not depend on an LLM. That makes the system easier to test and safer to
demo.
```

If showing the UI, spend the time like this:

- 20 seconds: dashboard and stack overview
- 30 seconds: document upload/indexing explanation
- 45 seconds: manual internship match result
- 20 seconds: switch to LangGraph and show completed stages
- 5 seconds: mention ranking and next steps

## Five-Minute Demo Version

Use this when the interviewer wants more technical depth.

```text
AgentForge started as a production-style full-stack foundation: Next.js frontend,
FastAPI backend, PostgreSQL, Alembic migrations, and Docker Compose services.
I built the regular product surfaces first instead of starting with agents.
```

Then show the document flow:

```text
The CV upload system stores the file locally, extracts text from PDF/DOCX/TXT,
splits text with RecursiveCharacterTextSplitter, stores chunks in PostgreSQL,
embeds them with sentence-transformers/all-MiniLM-L6-v2, and indexes vectors in
Qdrant.
```

Then show the manual pipeline:

```text
The manual pipeline is intentionally deterministic. The planner is rule-based,
retrieval is semantic search, evidence analysis checks retrieval quality, and
the report generator uses an explainable skill graph instead of asking an LLM
to invent a score.
```

Then show LangGraph:

```text
The LangGraph endpoint is experimental and parallel to the manual endpoint. It
uses shared pipeline state and the same components as graph nodes. I kept the
manual pipeline because it is easier to debug and safer while the graph version
is being validated.
```

Then show optional LLM architecture:

```text
The LLM layer exists but is not connected to the main workflow yet. It has a
prompt registry, model registry, provider registry, Ollama adapter, LLM reasoner,
and output validator. The validator compares LLM reasoning against the
deterministic report so the system does not blindly trust generated text.
```

Close with limitations:

```text
The main gaps are authentication, background jobs, deeper automated tests,
hybrid retrieval, and production deployment. I paused adding more agents because
the next valuable step is hardening the system.
```

## Interview Talking Points

### Why Deterministic First

The match score is produced by a deterministic skill graph, not by an LLM. This
makes results repeatable, easier to test, and easier to explain.

Good phrasing:

```text
I wanted a reliable baseline before adding generative reasoning. The LLM can
explain or refine the result later, but it should not be the only source of
truth for scoring.
```

### Why The Evidence Analyzer Matters

The Evidence Analyzer separates retrieved chunks from trusted evidence. It
filters low-score chunks, removes duplicates, caps the number of chunks, and
reports warnings.

Good phrasing:

```text
Retrieval can fail silently in RAG systems. I added an evidence layer so weak
retrieval does not automatically become a confident match report.
```

### Why LangGraph Is Experimental

The manual pipeline is still the trusted path. LangGraph is used to validate
graph orchestration without replacing working code.

Good phrasing:

```text
I introduced LangGraph as a parallel path so I could compare outputs and migrate
carefully instead of rewriting the pipeline all at once.
```

### Why The LLM Is Optional

The LLM layer is behind adapter, provider, model, and prompt registries. It is
not required for the deterministic workflow.

Good phrasing:

```text
The system should still work if Ollama is not running. That is why the LLM
reasoner is optional and validated separately.
```

### Why Registries Exist

Registries keep configuration and discovery separate from business logic:

- Agent Registry: what agents exist
- Prompt Registry: which prompt/version is used
- Model Registry: which model settings belong to which task
- Provider Registry: which LLM provider implementation is enabled

Good phrasing:

```text
The registries are lightweight now, but they create clear extension points for
future providers, models, prompts, and orchestration.
```

## What I Personally Learned From Building This

I learned that AI features need normal software foundations first. Uploads,
database models, API contracts, frontend state, migrations, and observability
matter before agents become useful.

I also learned that RAG quality depends heavily on the steps before generation:
parsing, chunking, embeddings, retrieval filters, and context preparation. A weak
retrieval result should not be treated as reliable evidence just because it came
from a vector database.

The biggest architecture lesson was separation of concerns. Planner, Retriever,
Evidence Analyzer, Context Builder, Match Report Generator, LLM Reasoner, and
Output Validator each have a narrow job. That makes the system easier to test,
debug, and explain.

Finally, I learned that adding an LLM too early can hide problems. The
deterministic pipeline made the system useful before generation, and it gives the
future LLM layer something stable to validate against.

## Known Limitations

- Authentication is not implemented yet; demo flows use seeded users and
  workspaces.
- Document processing and indexing are synchronous.
- Redis is available but background workers are not connected yet.
- Local document storage is for development, not production.
- OCR and scanned PDF support are not implemented.
- Retrieval is embedding-only; hybrid search and reranking are future work.
- The skill graph is intentionally small and should be expanded with weights.
- The LangGraph pipeline is validated but still experimental.
- The LLM reasoner is standalone and not connected to the main pipeline.
- Output validation is standalone and should later run after optional LLM
  reasoning.
- There is not yet enough automated test coverage for production confidence.

## Next Improvements

Recommended next steps:

1. Add automated backend and frontend tests for the current workflows.
2. Add GitHub Actions for backend compile/tests and frontend lint/typecheck.
3. Build an Agent Execution Visualizer from agent run and pipeline state data.
4. Add JWT authentication and workspace ownership enforcement.
5. Move document parsing, embedding, and Qdrant indexing to background jobs.
6. Improve retrieval with hybrid search and reranking.
7. Connect the optional LLM Reasoner behind a user-controlled mode.
8. Run Output Validator after LLM reasoning.
9. Add deployment configuration for frontend, backend, PostgreSQL, and Qdrant.

## Reviewer Checklist

A reviewer should be able to verify:

- the project runs locally with Docker, FastAPI, and Next.js
- uploaded documents become searchable through Qdrant
- manual internship match produces a structured report
- LangGraph internship match completes the same core workflow
- weak retrieval can stop the pipeline before report generation
- internship ranking works across workspace internships
- LLM infrastructure exists but is not overclaimed as part of the main pipeline
- current limitations are clearly documented
