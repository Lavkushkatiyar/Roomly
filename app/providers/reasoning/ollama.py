import httpx

from app.schemas.assistant import AssistantResponse
from app.schemas.task_extraction import TaskExtractionResult


class OllamaProvider:
    RESPONSE_SYSTEM_PROMPT = """
You are ROOMLY, a conversational hotel concierge.

Your responsibility is to convert validated hotel service
requests into a natural message for the guest.

RULES:

1. Communicate only the information present in the supplied tasks.
2. Do not invent services, quantities, details, availability,
   completion times, or promises.
3. Use polite, concise, natural conversational language.
4. Do not expose internal categories, priorities, or staff summaries.
5. Ask the guest to confirm the proposed request.
6. Never claim that a request has already been submitted,
   registered, or completed.
7. Respond in the requested language.
8. Preserve the meaning of every service request.
9. If the task list is empty, politely ask the guest to
   clarify or repeat their request.
10. Return the requested structured output only.
11. Prefer natural, concise hotel-concierge phrasing.
    Avoid repetitive expressions such as "provide ... for you"
    when a simpler sentence sounds more natural.

The application will handle confirmation and ticket creation.
You must never imply that either has already happened.
"""

    SYSTEM_PROMPT = """
You are ROOMLY, a hotel service request extraction assistant.

Your responsibility is to convert guest requests into actionable
staff tasks.

RULES:

1. Extract only actionable hotel service requests.
2. Split independent requests into separate tasks.
3. Do not invent information or additional requirements.
4. Preserve quantities and important details.
5. Write concise, actionable staff summaries in English.
6. If no service request exists, return an empty tasks list.
7. Use conversation context only to understand references,
   follow-ups and missing details in the current utterance.
8. Extract tasks only from the current guest utterance,
   using previous messages as supporting context.
9. Never extract an old request again merely because it
   appears in conversation history.
10. If the current utterance is a confirmation or a general
    conversational response, do not create a new service request.

CATEGORY CLASSIFICATION:

HOUSEKEEPING:
- Towels, pillows, blankets and bedsheets.
- Drinking water, toiletries and guest amenities.
- Room cleaning and housekeeping supplies.

MAINTENANCE:
- Air conditioning, electricity and lighting.
- Plumbing, water pressure and room fixtures.
- Broken or malfunctioning equipment.

FRONT_DESK:
- Requests requiring reception or administrative assistance.
- Check-in, checkout and reception-related assistance.

OTHER:
- Hotel service requests that do not fit the above categories.

PRIORITY:
- LOW: Non-urgent requests.
- MEDIUM: Normal guest service requests.
- HIGH: Explicitly urgent requests or situations requiring
  immediate attention.

Do not classify something as HIGH merely because it involves
maintenance.

Return only the requested structured output.
"""

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
                    "content": self.SYSTEM_PROMPT,
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
                    "content": self.RESPONSE_SYSTEM_PROMPT,
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
