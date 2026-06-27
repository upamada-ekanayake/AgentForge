from typing import Any

import httpx

from app.core.config import settings
from app.services.llm_provider import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMProviderError,
)


class OllamaProvider:
    provider_name = "ollama"

    def __init__(
        self,
        base_url: str = settings.ollama_base_url,
        default_model: str = settings.ollama_model,
        timeout_seconds: float = settings.ollama_timeout_seconds,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds

    async def generate(
        self,
        request: LLMGenerateRequest,
    ) -> LLMGenerateResponse:
        model = request.model or self.default_model
        payload = self._build_payload(request, model)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"Ollama returned HTTP {exc.response.status_code}.",
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError("Could not connect to Ollama.") from exc

        response_payload = response.json()
        content = self._extract_content(response_payload)
        return LLMGenerateResponse(
            provider=self.provider_name,
            model=model,
            content=content,
            raw_response=response_payload,
        )

    def _build_payload(
        self,
        request: LLMGenerateRequest,
        model: str,
    ) -> dict[str, Any]:
        options: dict[str, Any] = {"temperature": request.temperature}
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                message.model_dump(mode="json") for message in request.messages
            ],
            "stream": False,
            "options": options,
        }
        if request.require_json:
            payload["format"] = "json"

        return payload

    def _extract_content(self, response_payload: dict[str, Any]) -> str:
        message = response_payload.get("message")
        if not isinstance(message, dict):
            raise LLMProviderError("Ollama response did not include a message.")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("Ollama response did not include content.")

        return content
