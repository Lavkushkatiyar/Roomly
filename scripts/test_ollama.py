import asyncio

from app.providers.reasoning.ollama import OllamaProvider


async def main() -> None:
    provider = OllamaProvider()

    result = await provider.extract_tasks(
        "I need two towels, and the AC in my room isn't cooling."
    )

    print(result.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
