# Agent Design

AgentForge uses narrow, inspectable agent contracts for CV-to-internship
matching. The current production-style workflow is deterministic first:

```text
Planner
  -> Retriever
  -> Evidence Analyzer
  -> Context Builder
  -> Match Report Generator
```

The LLM layer is optional and remains separate from the main scoring path.

## LLM Adapter Layer

AgentForge introduces LLMs through a provider adapter instead of calling a model
directly from business logic. The first provider is Ollama, configured for a
local `qwen3:8b` model by default.

The adapter contract is:

- `LLMMessage`: system, user, or assistant message.
- `LLMGenerateRequest`: messages, model override, temperature, token limit, and JSON mode.
- `LLMGenerateResponse`: provider, model, generated content, and optional raw provider payload.

This keeps the deterministic pipeline intact. Future components can call the
LLM adapter as one replaceable step:

```text
Planner
  -> Retriever
  -> Evidence Analyzer
  -> Context Builder
  -> LLM Reasoner
  -> JSON Validator
  -> Report Formatter
```

The rule-based skill graph and retrieval quality checks remain verification
layers even after LLM reasoning is added.

## Evidence Analyzer

The Evidence Analyzer sits between Retriever and Context Builder. It is a
standalone agent contract for now:

```text
POST /agents/evidence-analyzer/analyze
```

It accepts retrieved CV chunks, sorts them by score, removes duplicates, keeps
only evidence above the configured threshold, and caps how many chunks move
forward. The default policy keeps up to three chunks with score `>= 0.45`.

The output includes:

- kept chunks
- discarded chunks
- retrieval quality
- warnings

This keeps weak or repetitive evidence out of future prompts while preserving a
clear audit trail for why each chunk was kept or discarded.

## LLM Reasoner Foundation

The LLM reasoner is currently an optional standalone agent endpoint:

```text
POST /agents/llm-reasoner/reason
```

It accepts Context Builder text plus the deterministic match report. It builds a
JSON-only prompt, calls the LLM adapter, and validates the response with
Pydantic before returning it.

Expected validated output:

- `prompt_name`
- `prompt_version`
- `reasoning_summary`
- `strengths`
- `weaknesses`
- `improvement_plan`
- `confidence`
- `risk_flags`

This endpoint is not connected to the internship match or ranking pipelines yet.

## Prompt Registry

Prompt templates live outside application code in `packages/prompts`.

The first registered template is:

```text
packages/prompts/internship_reasoning_v1.md
```

Each prompt includes metadata:

```text
prompt_name: internship_reasoning
prompt_version: v1
```

The backend prompt registry loads templates by name and version, renders explicit
`{{variable}}` placeholders, and returns prompt metadata with the rendered
content. LLM reasoner outputs include this prompt metadata so future agent run
logs can be compared across prompt versions.

## Output Validator

The Output Validator checks business correctness after LLM reasoning. It is a
standalone endpoint:

```text
POST /agents/output-validator/validate
```

The validator compares the deterministic match report with the LLM reasoning
output and flags risk signals such as:

- large disagreement between deterministic score and LLM score
- high LLM confidence when retrieval quality is weak
- retrieval warnings not reflected in LLM risk flags
- deterministic missing skills not discussed as weaknesses

This lets AgentForge accept structured LLM reasoning without blindly trusting it.

## Model Registry

AgentForge uses an in-code model registry before introducing database-backed
model configuration.

Each model task config includes:

- `task_name`
- `provider`
- `model`
- `temperature`
- `max_tokens`
- `supports_json`
- `enabled`

Initial registered tasks:

- `internship_reasoning`
- `cover_letter`
- `interview_prep`
- `output_validation`

The LLM service can now apply model settings by `task_name`, which keeps agent
logic separate from model/provider selection.

## Provider Registry

Provider creation is also routed through an in-code provider registry.

Each provider config includes:

- `provider_name`
- `provider_class`
- `base_url`
- `enabled`

Initial registered provider:

- `ollama`

This keeps provider selection replaceable. Future providers such as OpenAI,
Azure, vLLM, or LM Studio can be added behind the same LLM service contract
without changing agent logic.

## Agent Registry

Agent metadata is exposed through:

```text
GET /agents/registry
```

Each registry item includes:

- `agent_name`
- `run_type`
- `description`
- `enabled`

Registered agents:

- `planner`
- `retriever`
- `evidence_analyzer`
- `context_builder`
- `match_report_generator`
- `llm_reasoner`
- `output_validator`

The registry makes agents discoverable before orchestration moves to LangGraph
or another runtime. It is metadata-only for now and does not change pipeline
behavior.

## Shared Pipeline State

`app/agents/pipeline_state.py` defines `InternshipPipelineState`, a shared state
container used by the experimental LangGraph pipeline.

The state can hold:

- user/workspace/document/internship identifiers
- planner output
- retriever output
- evidence analyzer output
- context builder output
- deterministic report
- optional LLM reasoning
- optional output validation
- warnings
- errors
- current stage
- completed stages

The manual pipeline does not use this state directly. LangGraph uses it to
orchestrate the existing agents without changing each agent's business logic.

## Experimental LangGraph Pipeline

AgentForge includes a parallel experimental graph endpoint:

```text
POST /agents/internship-match-graph/run
```

It does not replace the existing manual pipeline:

```text
POST /agents/internship-match/run
```

The graph uses `InternshipPipelineState` and reuses existing business logic:

```text
START
  -> planner_node
  -> retriever_node
  -> evidence_analyzer_node
  -> context_builder_node
  -> match_report_node
  -> END
```

Conditional stops:

- stop after planner when clarification is needed
- stop after evidence analyzer when no reliable evidence is retained

The graph currently excludes LLM reasoning and output validation. It exists to
prove orchestration can move to LangGraph without rewriting the agent logic.

## Agent Execution Visualizer

Agent execution is visible in the frontend at:

```text
/agent-runs
```

The page reads stored agent runs through:

```text
GET /agents/runs
GET /agents/runs/{id}
```

It shows a selectable node graph, timeline fallback, parent payload, and selected
stage payload. This keeps observability separate from orchestration behavior.
