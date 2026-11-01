from app.core.config import settings
from app.providers.reasoning.base import ReasoningProvider
from app.providers.reasoning.ollama import OllamaProvider


def get_reasoning_provider() -> ReasoningProvider:
    if settings.REASONING_PROVIDER == "ollama":
        return OllamaProvider(
            model=settings.REASONING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )

    raise ValueError(f"Unsupported reasoning provider: {settings.REASONING_PROVIDER}")
