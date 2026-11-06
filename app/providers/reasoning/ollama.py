import httpx

from app.providers.reasoning.prompts import (
    RESPONSE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    TURN_SYSTEM_PROMPT,
)
from app.schemas.assistant import AssistantResponse
from app.schemas.conversation_turn import ConversationTurnResult
from app.schemas.task_extraction import TaskExtractionResult


class OllamaProvider:
    def __init__(
        self,
        model: str = "qwen3:8b",
        base_url: str = "http://localhost:11434",
        timeout: float = 180.0,
    ) -> None:
        self.model = model
        self.url = f"{base_url.rstrip('/')}/api/chat"
        self.timeout = timeout

    async def extract_tasks(
        self,
        transcript: str,
        context: list[dict[str, str]] | None = None,
    ) -> TaskExtractionResult:
        schema = TaskExtractionResult.model_json_schema()

        conversation_history = "\n".join(
            f"{message['role']}: {message['content']}" for message in (context or [])
        )

        user_content = (
            f"Previous conversation:\n"
            f"{conversation_history or 'No previous conversation.'}\n\n"
            f"Current guest utterance:\n{transcript}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            "stream": False,
            "think": False,
            "format": schema,
            "options": {
                "temperature": 0,
                "num_ctx": 8192,
            },
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            response = await client.post(
                self.url,
                json=payload,
            )
            response.raise_for_status()

        result = response.json()
        content = result["message"]["content"]

        return TaskExtractionResult.model_validate_json(content)

    async def generate_response(
        self,
        extraction: TaskExtractionResult,
        language: str,
    ) -> AssistantResponse:
        schema = AssistantResponse.model_json_schema()

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": RESPONSE_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"Requested language: {language}\n"
                        f"Validated tasks:\n"
                        f"{extraction.model_dump_json()}"
                    ),
                },
            ],
            "stream": False,
            "think": False,
            "format": schema,
            "options": {
                "temperature": 0,
                "num_ctx": 8192,
            },
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            print(payload)
            response = await client.post(
                self.url,
                json=payload,
            )
            response.raise_for_status()

        result = response.json()
        content = result["message"]["content"]

        generated = AssistantResponse.model_validate_json(content)

        return AssistantResponse(
            text=generated.text,
            language=language,
        )

    async def process_turn(
        self,
        transcript: str,
        language: str,
        context: list[dict[str, str]] | None = None,
    ) -> ConversationTurnResult:
        normalized_transcript = transcript.strip()

        if not normalized_transcript:
            raise ValueError("Transcript cannot be empty.")

        conversation_history = "\n".join(
            f"{message['role']}: {message['content']}" for message in (context or [])
        )

        user_content = (
            f"Guest language: {language}\n\n"
            f"Previous conversation:\n"
            f"{conversation_history or 'No previous conversation.'}\n\n"
            f"Current guest utterance:\n{normalized_transcript}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": TURN_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            "stream": False,
            "think": False,
            "format": ConversationTurnResult.model_json_schema(),
            "options": {
                "temperature": 0,
                "num_ctx": 8192,
            },
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            response = await client.post(
                self.url,
                json=payload,
            )
            response.raise_for_status()

        result = response.json()
        content = result["message"]["content"]

        return ConversationTurnResult.model_validate_json(content)
