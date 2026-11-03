import asyncio

from app.core.config import settings
from app.db.models.enums import RequestCategory, RequestPriority
from app.providers.reasoning.ollama import OllamaProvider
from app.schemas.task_extraction import (
    ProposedServiceRequest,
    TaskExtractionResult,
)


async def main() -> None:
    provider = OllamaProvider(
        model=settings.REASONING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )

    extraction = TaskExtractionResult(
        tasks=[
            ProposedServiceRequest(
                category=RequestCategory.HOUSEKEEPING,
                staff_summary="Provide four water bottles",
                priority=RequestPriority.MEDIUM,
            ),
            ProposedServiceRequest(
                category=RequestCategory.HOUSEKEEPING,
                staff_summary="Provide two towels",
                priority=RequestPriority.MEDIUM,
            ),
        ]
    )

    response = await provider.generate_response(
        extraction=extraction,
        language="en-IN",
    )

    print("\nGenerated response:")
    print(response.text)
    print("\nLanguage:", response.language)


if __name__ == "__main__":
    asyncio.run(main())
