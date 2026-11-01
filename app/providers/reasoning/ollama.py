import httpx

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
    ) -> TaskExtractionResult:
        print("request_recieved", transcript)
        schema = TaskExtractionResult.model_json_schema()

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are ROOMLY, a hotel service request "
                        "extraction assistant. Extract only actionable "
                        "hotel service requests explicitly requested "
                        "or reported by the guest. Split independent "
                        "requests into separate tasks. Do not invent "
                        "details. Use concise, actionable English "
                        "staff summaries. Use the provided categories "
                        "and priorities. If no service request exists, "
                        "return an empty tasks list."
                    ),
                },
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
