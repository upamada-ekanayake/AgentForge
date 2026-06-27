from collections.abc import Callable

from pydantic import BaseModel

from app.core.config import settings
from app.services.llm_provider import LLMProvider, LLMProviderError
from app.services.ollama_service import OllamaProvider


ProviderFactory = Callable[[str], LLMProvider]


class ProviderConfig(BaseModel):
    provider_name: str
    provider_class: str
    base_url: str
    enabled: bool = True


PROVIDER_REGISTRY: dict[str, ProviderConfig] = {
    "ollama": ProviderConfig(
        provider_name="ollama",
        provider_class="OllamaProvider",
        base_url=settings.ollama_base_url,
        enabled=True,
    ),
}


PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "ollama": lambda base_url: OllamaProvider(base_url=base_url),
}


def get_provider_config(provider_name: str) -> ProviderConfig:
    normalized_name = provider_name.lower()
    config = PROVIDER_REGISTRY.get(normalized_name)
    if config is None:
        raise LLMProviderError(f"Unknown LLM provider: {provider_name}")
    if not config.enabled:
        raise LLMProviderError(f"LLM provider is disabled: {provider_name}")
    return config


def create_provider(provider_name: str) -> LLMProvider:
    config = get_provider_config(provider_name)
    factory = PROVIDER_FACTORIES.get(config.provider_name)
    if factory is None:
        raise LLMProviderError(
            f"LLM provider has no factory: {config.provider_name}",
        )
    return factory(config.base_url)


def list_provider_configs(include_disabled: bool = True) -> list[ProviderConfig]:
    configs = list(PROVIDER_REGISTRY.values())
    if include_disabled:
        return configs
    return [config for config in configs if config.enabled]
