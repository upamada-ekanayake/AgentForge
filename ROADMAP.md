# AgentForge Roadmap

AgentForge is being developed as a portfolio-grade AI engineering project: a
full-stack internship workflow platform with document intelligence, retrieval,
deterministic agents, optional LLM reasoning, and experimental LangGraph
orchestration.

The current focus is:

```text
Testing + CI/CD
```

The project already has enough AI architecture for the MVP. The next priority is
to make the existing system reliable, testable, observable, and easier for
reviewers to trust.

## Phase Overview

| Phase | Area | Status |
| --- | --- | --- |
| Phase 1 | Core Platform | Completed |
| Phase 2 | RAG Pipeline | Completed |
| Phase 3 | Deterministic Agents | Completed |
| Phase 4 | LangGraph Orchestration | Completed |
| Phase 5 | Testing | In Progress |
| Phase 6 | CI/CD | Planned |
| Phase 7 | Agent Execution Visualizer | Planned |
| Phase 8 | Authentication | Planned |
| Phase 9 | Background Processing | Planned |
| Phase 10 | Deployment | Planned |

## Phase 1 - Core Platform

Status: Completed

Completed work:

- Monorepo structure with `apps/web`, `apps/api`, `packages`, `infra`, and
  `docs`.
- FastAPI backend.
- Next.js frontend.
- PostgreSQL through Docker Compose.
- Redis and Qdrant in local infrastructure.
- SQLAlchemy models and Alembic migrations.
- Seed data for demo workspace, user, and internships.
- Basic CRUD foundation for users, workspaces, internships, and applications.
- Dashboard and API-connected frontend foundation.

Goal:

```text
Make AgentForge a real full-stack application before adding AI behavior.
```

## Phase 2 - RAG Pipeline

Status: Completed

Completed work:

- Document upload for PDF, DOCX, and TXT files.
- Local document storage.
- Text extraction.
- Recursive text chunking.
- `document_chunks` persistence.
- Embedding generation with `sentence-transformers/all-MiniLM-L6-v2`.
- Qdrant indexing.
- Retrieval-only document search endpoint.

Goal:

```text
Turn uploaded CVs into searchable evidence for downstream agent workflows.
```

## Phase 3 - Deterministic Agents

Status: Completed

Completed work:

- Planner Agent.
- Retriever Agent.
- Evidence Analyzer.
- Context Builder.
- Match Report Generator.
- Retrieval quality analysis.
- Workspace-wide internship ranking.
- Agent run logging through `agent_runs`.

Goal:

```text
Build useful AI-style workflow results without depending on an LLM.
```

## Phase 4 - LangGraph Orchestration

Status: Completed

Completed work:

- Shared `InternshipPipelineState`.
- Experimental LangGraph internship match endpoint.
- Manual pipeline remains unchanged.
- Frontend execution mode selector for Manual Pipeline vs LangGraph Pipeline.
- Successful mocked and live endpoint validation.

Goal:

```text
Prove the orchestration layer can move to LangGraph while preserving the same
business logic and result quality.
```

## Phase 5 - Testing

Status: In Progress

Current goal:

```text
Add focused automated tests around deterministic, high-value logic first.
```

Initial test targets:

1. Planner Agent.
2. Evidence Analyzer.
3. Text Chunker.
4. Skill Graph.
5. Match Report Generator.
6. Retrieval Quality.
7. Output Validator.
8. Prompt Registry.
9. Model Registry.
10. Provider Registry.

Near-term success criteria:

- Tests can run locally with one command.
- Pure unit tests do not require Docker.
- External services are mocked where appropriate.
- Failures are easy to diagnose.
- Tests cover both normal and safety-stop paths.

## Phase 6 - CI/CD

Status: Planned

Goal:

```text
Make every push and pull request run quality checks automatically.
```

Planned checks:

- Backend formatting check.
- Backend linting.
- Backend type checks.
- Backend tests.
- Frontend linting.
- Frontend typecheck.
- Future Playwright end-to-end tests.
- Future Docker build validation.

Target tools:

- Ruff.
- Black.
- mypy.
- pytest.
- ESLint.
- TypeScript.
- Playwright.
- GitHub Actions.

## Phase 7 - Agent Execution Visualizer

Status: Planned

Goal:

```text
Make agent observability visible in the product UI.
```

Planned viewer:

```text
User Query
  -> Planner
  -> Retriever
  -> Evidence Analyzer
  -> Context Builder
  -> Match Report
  -> Optional LLM Reasoner
  -> Output Validator
```

Each stage should eventually show:

- status
- duration
- input payload
- output payload
- warnings
- errors
- retrieval scores
- retained and discarded evidence
- prompt name and version for LLM stages
- model/provider metadata for LLM stages

This is expected to become the main portfolio demo feature after tests and CI.

## Phase 8 - Authentication

Status: Planned

Goal:

```text
Replace demo-user assumptions with real user identity and workspace access.
```

Planned work:

- Register.
- Login.
- Logout.
- Password hashing.
- JWT access tokens.
- Refresh token strategy.
- Workspace ownership checks.
- Workspace membership roles.
- Frontend auth state.
- Protected routes.

## Phase 9 - Background Processing

Status: Planned

Goal:

```text
Move expensive document processing out of request-response paths.
```

Current flow:

```text
Upload
  -> Extract
  -> Chunk
  -> Embed
  -> Qdrant
```

Target flow:

```text
Upload
  -> Store metadata
  -> Queue job
  -> Worker extracts text
  -> Worker chunks text
  -> Worker embeds chunks
  -> Worker indexes Qdrant
  -> Document status updates
```

Possible tools:

- Celery.
- Dramatiq.
- RQ.
- ARQ.

## Phase 10 - Deployment

Status: Planned

Goal:

```text
Make AgentForge reviewable outside a local machine.
```

Planned deployment targets:

- Frontend on Vercel.
- Backend on Render, Railway, Fly.io, or a VPS.
- Managed PostgreSQL.
- Qdrant Cloud or self-hosted Qdrant.
- Environment-specific configuration.
- Health checks.
- Structured logs.
- Basic monitoring.

## Engineering Principles

AgentForge favors deterministic, observable, and testable AI workflows before
autonomous behavior.

Core principles:

- Build product foundations before agent complexity.
- Keep agents narrow and composable.
- Separate retrieval, evidence analysis, context building, scoring, and LLM
  reasoning.
- Make weak retrieval visible instead of hiding it behind confident outputs.
- Keep deterministic scoring independent from LLM explanation.
- Treat LangGraph as orchestration, not business logic.
- Keep LLM providers, models, and prompts replaceable through registries.
- Prefer small, reviewable changes over large rewrites.
- Add tests before expanding more AI behavior.

Why this matters:

```text
AI systems are easier to trust when each step can be inspected, tested, and
replaced independently.
```

## What I Will Not Build Right Now

These ideas are intentionally deferred:

- Memory Agent.
- Reflection Agent.
- Debate Agent.
- Multi-Agent Voting.
- Self-Improving Planner.

Reason:

```text
They add agent complexity without improving the current portfolio story as much
as testing, CI/CD, observability, authentication, background jobs, and deployment.
```

## Success Criteria

AgentForge should not be considered production-ready until the following are
complete:

- Core deterministic logic has automated unit tests.
- Main API workflows have integration tests.
- Frontend workflows have at least a small end-to-end test suite.
- CI runs backend and frontend quality checks on every push.
- Authentication and workspace access are implemented.
- Document processing runs in background jobs.
- Agent execution is observable through logs or a visualizer.
- Retrieval quality, warnings, and errors are visible to users or operators.
- Environment configuration is separated for development and production.
- The app is deployed with managed database/vector storage or documented
  self-hosting.
- Known limitations are clearly documented.

## Recruiter Review Notes

This roadmap is meant to show that AgentForge is not just a feature list. It is
being developed like an engineering platform:

- completed phases show the working product and AI foundation
- current phases show quality hardening
- planned phases show production-readiness gaps
- non-goals show restraint and prioritization

The short version:

```text
AgentForge already demonstrates a serious AI workflow. The next work is about
proving reliability and making the system easier to inspect, test, and deploy.
```
