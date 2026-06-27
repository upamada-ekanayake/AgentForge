from pydantic import BaseModel, Field

from app.core.config import settings


class ModelRegistryError(RuntimeError):
    """Raised when a requested model task config is unavailable."""


class ModelTaskConfig(BaseModel):
    task_name: str
    provider: str
    model: str
    temperature: float = Field(ge=0, le=2)
    max_tokens: int = Field(ge=1)
    supports_json: bool
    enabled: bool = True


MODEL_REGISTRY: dict[str, ModelTaskConfig] = {
    "internship_reasoning": ModelTaskConfig(
        task_name="internship_reasoning",
        provider="ollama",
        model=settings.ollama_model,
        temperature=0.2,
        max_tokens=900,
        supports_json=True,
        enabled=True,
    ),
    "cover_letter": ModelTaskConfig(
        task_name="cover_letter",
        provider="ollama",
        model=settings.ollama_model,
        temperature=0.4,
        max_tokens=1200,
        supports_json=True,
        enabled=False,
    ),
    "interview_prep": ModelTaskConfig(
        task_name="interview_prep",
        provider="ollama",
        model=settings.ollama_model,
        temperature=0.3,
        max_tokens=1200,
        supports_json=True,
        enabled=False,
    ),
    "output_validation": ModelTaskConfig(
        task_name="output_validation",
        provider="ollama",
        model=settings.ollama_model,
        temperature=0.0,
        max_tokens=700,
        supports_json=True,
        enabled=True,
    ),
}


def get_model_task_config(task_name: str) -> ModelTaskConfig:
    config = MODEL_REGISTRY.get(task_name)
    if config is None:
        raise ModelRegistryError(f"Model task is not registered: {task_name}")
    if not config.enabled:
        raise ModelRegistryError(f"Model task is disabled: {task_name}")
    return config


def list_model_task_configs(include_disabled: bool = True) -> list[ModelTaskConfig]:
    configs = list(MODEL_REGISTRY.values())
    if include_disabled:
        return configs
    return [config for config in configs if config.enabled]
