import httpx

from app.schemas.task_extraction import TaskExtractionResult


class OllamaProvider:
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
    ) -> TaskExtractionResult:
        print("request_recieved", transcript)
        schema = TaskExtractionResult.model_json_schema()

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": transcript,
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
            print(payload, "payloadggit")
            response = await client.post(
                self.url,
                json=payload,
            )
            response.raise_for_status()

        result = response.json()
        content = result["message"]["content"]

        return TaskExtractionResult.model_validate_json(content)
