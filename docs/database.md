# Database Design

AgentForge uses PostgreSQL for relational application data and Qdrant for vector search.

## Tables

- `users`
  Stores user accounts, profile names, password hashes for later auth, and account activity state.

- `workspaces`
  Stores student, team, or organization workspaces. Each workspace has an owner.

- `workspace_members`
  Joins users to workspaces with a role: `owner`, `admin`, or `member`.

- `documents`
  Stores uploaded files such as CVs, including owner, workspace, storage path, content type, size, and processing status.

- `document_chunks`
  Stores extracted document text chunks before and after vector indexing. Each chunk can reference its Qdrant point ID.

- `internship_posts`
  Stores internship or job post details, including title, company, location, description, requirements, and source URL.

- `applications`
  Tracks a user's application workflow for an internship post. Status values include `draft`, `matched`, `applied`, `interviewing`, `offered`, `rejected`, and `withdrawn`.

- `agent_runs`
  Stores one full AI workflow execution, such as an internship match run, with JSON input/output payloads and run status.

- `agent_steps`
  Stores ordered steps inside an agent run, such as Planner, RAG, Tool, Safety, and Evaluator.

- `agent_logs`
  Stores diagnostic logs, model names, latency, structured details, warnings, and errors for agent runs and steps.

## Conventions

- Primary keys are UUIDs.
- Every table includes `created_at` and `updated_at`.
- Foreign keys connect users, workspaces, documents, internships, applications, agent runs, steps, and logs.
- Enums are used for workspace roles, document status, application status, agent status, and log level.
- JSONB is used for agent input, output, and diagnostic details.

## Notes

- PostgreSQL is the source of truth for structured data.
- Qdrant stores vector embeddings and metadata needed for retrieval.
- `document_chunks` stores extracted chunks before embedding and indexing.
- `agent_runs`, `agent_steps`, and `agent_logs` preserve observability for each AI task.
