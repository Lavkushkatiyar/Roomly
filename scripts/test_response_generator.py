import asyncio

from app.core.config import settings
from app.providers.reasoning.ollama import OllamaProvider
from app.schemas.task_extraction import (
    TaskExtractionResult,
)


async def main() -> None:
    provider = OllamaProvider(
        model=settings.REASONING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )

    extraction = TaskExtractionResult(tasks=[])

    response = await provider.generate_response(
        extraction=extraction,
        language="en-IN",
    )

    print("\nGenerated response:")
    print(response.text)
    print("\nLanguage:", response.language)


if __name__ == "__main__":
    asyncio.run(main())
