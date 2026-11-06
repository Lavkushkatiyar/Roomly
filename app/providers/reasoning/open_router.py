import httpx

from app.providers.reasoning.prompts import (
    RESPONSE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    TURN_SYSTEM_PROMPT,
)
from app.schemas.assistant import AssistantResponse
from app.schemas.conversation_turn import ConversationTurnResult
from app.schemas.task_extraction import TaskExtractionResult


class OpenRouterProvider:
    MODEL = "nvidia/nemotron-3.5-super-vl:free"

    def __init__(
        self,
        api_key: str,
        model: str = MODEL,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key
        self.model = self.MODEL
        self.url = f"{base_url.rstrip('/')}/chat/completions"
        self.timeout = timeout

    async def _request(
        self,
        messages: list[dict[str, str]],
        schema: dict,
        schema_name: str,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.url,
                headers=headers,
                json=payload,
            )
            if response.is_error:
                print("OpenRouter status:", response.status_code)
                print("OpenRouter error:", response.text)

            response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        if not content:
            raise ValueError("OpenRouter returned an empty response.")

        return content

    async def extract_tasks(
        self,
        transcript: str,
        context: list[dict[str, str]] | None = None,
    ) -> TaskExtractionResult:
        conversation_history = "\n".join(
            f"{message['role']}: {message['content']}" for message in (context or [])
        )

        user_content = (
            f"Previous conversation:\n"
            f"{conversation_history or 'No previous conversation.'}\n\n"
            f"Current guest utterance:\n{transcript}"
        )

        content = await self._request(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            schema=TaskExtractionResult.model_json_schema(),
            schema_name="task_extraction",
        )

        return TaskExtractionResult.model_validate_json(content)

    async def generate_response(
        self,
        extraction: TaskExtractionResult,
        language: str,
    ) -> AssistantResponse:
        content = await self._request(
            messages=[
                {"role": "system", "content": RESPONSE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Requested language: {language}\n"
                        f"Validated tasks:\n"
                        f"{extraction.model_dump_json()}"
                    ),
                },
            ],
            schema=AssistantResponse.model_json_schema(),
            schema_name="assistant_response",
        )

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

        content = await self._request(
            messages=[
                {"role": "system", "content": TURN_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            schema=ConversationTurnResult.model_json_schema(),
            schema_name="conversation_turn",
        )

        return ConversationTurnResult.model_validate_json(content)
