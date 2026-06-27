from pydantic import BaseModel


class AgentConfig(BaseModel):
    agent_name: str
    run_type: str
    description: str
    enabled: bool = True


AGENT_REGISTRY: dict[str, AgentConfig] = {
    "planner": AgentConfig(
        agent_name="planner",
        run_type="planner",
        description="Classifies user intent and creates a structured task plan.",
        enabled=True,
    ),
    "retriever": AgentConfig(
        agent_name="retriever",
        run_type="retriever",
        description="Retrieves CV chunks and internship post context.",
        enabled=True,
    ),
    "evidence_analyzer": AgentConfig(
        agent_name="evidence_analyzer",
        run_type="evidence_analyzer",
        description="Filters, deduplicates, and scores retrieved evidence.",
        enabled=True,
    ),
    "context_builder": AgentConfig(
        agent_name="context_builder",
        run_type="context_builder",
        description="Formats trusted evidence and internship data into model-ready context.",
        enabled=True,
    ),
    "match_report_generator": AgentConfig(
        agent_name="match_report_generator",
        run_type="match_report_generator",
        description="Creates the deterministic skill graph match report.",
        enabled=True,
    ),
    "llm_reasoner": AgentConfig(
        agent_name="llm_reasoner",
        run_type="llm_reasoner",
        description="Uses the LLM adapter to explain deterministic results as validated JSON.",
        enabled=True,
    ),
    "output_validator": AgentConfig(
        agent_name="output_validator",
        run_type="output_validator",
        description="Checks LLM reasoning against deterministic results and retrieval quality.",
        enabled=True,
    ),
}


def list_agent_configs(include_disabled: bool = False) -> list[AgentConfig]:
    configs = list(AGENT_REGISTRY.values())
    if include_disabled:
        return configs
    return [config for config in configs if config.enabled]
