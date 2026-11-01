import asyncio
from pathlib import Path

from app.services.task_extraction import TaskExtractionServices


async def upload_audio(file):
    audio_path = Path("./request2.wav")
    task_service = TaskExtractionServices()
    audio_bytes = audio_path.read_bytes()
    tasks = await task_service.extractTaskFromVoice(audio=audio_bytes)
    print(tasks)

    return tasks


asyncio.run(upload_audio(file="nothing"))
