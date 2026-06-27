import json

from pydantic import ValidationError

from app.agents.prompt_builder import build_match_reasoning_prompt
from app.modules.agents.schemas import LLMReasonerInput, LLMReasonerOutput
from app.services.llm_provider import LLMProviderError
from app.services.llm_service import generate_with_llm


class LLMReasonerValidationError(ValueError):
    """Raised when an LLM response cannot be validated as reasoner JSON."""


async def run_llm_reasoning(
    reasoner_input: LLMReasonerInput,
) -> LLMReasonerOutput:
    prompt, rendered_prompt = build_match_reasoning_prompt(reasoner_input)
    llm_response = await generate_with_llm(
        prompt,
        task_name=rendered_prompt.prompt_name,
    )
    return validate_llm_reasoning_json(
        content=llm_response.content,
        prompt_name=rendered_prompt.prompt_name,
        prompt_version=rendered_prompt.prompt_version,
    )


def validate_llm_reasoning_json(
    content: str,
    prompt_name: str,
    prompt_version: str,
) -> LLMReasonerOutput:
    try:
        parsed = json.loads(_strip_json_fence(content))
        parsed["prompt_name"] = prompt_name
        parsed["prompt_version"] = prompt_version
        return LLMReasonerOutput.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise LLMReasonerValidationError(
            "LLM reasoner returned invalid JSON.",
        ) from exc


def _strip_json_fence(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```json"):
        stripped = stripped.removeprefix("```json").strip()
    elif stripped.startswith("```"):
        stripped = stripped.removeprefix("```").strip()

    if stripped.endswith("```"):
        stripped = stripped.removesuffix("```").strip()

    return stripped


__all__ = [
    "LLMProviderError",
    "LLMReasonerValidationError",
    "run_llm_reasoning",
    "validate_llm_reasoning_json",
]
