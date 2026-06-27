from app.core.config import settings
from app.services.llm_provider import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMProvider,
)
from app.services.model_registry import ModelTaskConfig, get_model_task_config
from app.services.provider_registry import create_provider


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    provider = (provider_name or settings.llm_provider).lower()
    return create_provider(provider)


async def generate_with_llm(
    request: LLMGenerateRequest,
    task_name: str | None = None,
) -> LLMGenerateResponse:
    model_config = get_model_task_config(task_name) if task_name else None
    configured_request = _apply_model_config(request, model_config)
    provider = get_llm_provider(model_config.provider if model_config else None)
    return await provider.generate(configured_request)


def _apply_model_config(
    request: LLMGenerateRequest,
    model_config: ModelTaskConfig | None,
) -> LLMGenerateRequest:
    if model_config is None:
        return request

    return request.model_copy(
        update={
            "model": request.model or model_config.model,
            "temperature": model_config.temperature,
            "max_tokens": request.max_tokens or model_config.max_tokens,
            "require_json": request.require_json and model_config.supports_json,
        },
    )
