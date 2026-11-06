import asyncio

from app.core.config import settings
from app.providers.reasoning.ollama import OllamaProvider
from app.providers.reasoning.open_router import OpenRouterProvider


async def main() -> None:
    provider = OllamaProvider()

    result = await provider.extract_tasks(
        "I need two towels, and the AC in my room isn't cooling."
    )
    open_router = OpenRouterProvider(
        api_key=settings.OPENROUTER_API_KEY,
        model=settings.model,
        base_url=settings.OPENROUTER_BASE_URL,
        timeout=300,
    )
    result2 = await open_router.extract_tasks(
        transcript=" I need two towels, and the AC in my room isn't cooling."
    )
    print("Ollama", result.model_dump())
    print("Open_router", result2.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
