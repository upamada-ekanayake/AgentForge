from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


LLMRole = Literal["system", "user", "assistant"]


class LLMMessage(BaseModel):
    role: LLMRole
    content: str = Field(min_length=1)


class LLMGenerateRequest(BaseModel):
    messages: list[LLMMessage] = Field(min_length=1)
    model: str | None = None
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)
    require_json: bool = False


class LLMGenerateResponse(BaseModel):
    provider: str
    model: str
    content: str
    raw_response: dict[str, Any] | None = None


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot complete a generation request."""


class LLMProvider(Protocol):
    provider_name: str

    async def generate(
        self,
        request: LLMGenerateRequest,
    ) -> LLMGenerateResponse:
        """Generate text from structured chat messages."""
