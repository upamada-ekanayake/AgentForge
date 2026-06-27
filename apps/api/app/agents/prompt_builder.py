from app.modules.agents.schemas import LLMReasonerInput
from app.services.llm_provider import LLMGenerateRequest, LLMMessage
from app.services.prompt_registry import RenderedPrompt, render_prompt_template


INTERNSHIP_REASONING_PROMPT_NAME = "internship_reasoning"
INTERNSHIP_REASONING_PROMPT_VERSION = "v1"


def build_match_reasoning_prompt(
    reasoner_input: LLMReasonerInput,
) -> tuple[LLMGenerateRequest, RenderedPrompt]:
    rendered_prompt = render_prompt_template(
        prompt_name=INTERNSHIP_REASONING_PROMPT_NAME,
        prompt_version=INTERNSHIP_REASONING_PROMPT_VERSION,
        variables={
            "context_text": reasoner_input.context_text,
            "deterministic_report": reasoner_input.deterministic_report.model_dump_json(
                indent=2,
            ),
        },
    )

    request = LLMGenerateRequest(
        messages=[
            LLMMessage(role="user", content=rendered_prompt.content),
        ],
        temperature=0.2,
        max_tokens=900,
        require_json=True,
    )
    return request, rendered_prompt
