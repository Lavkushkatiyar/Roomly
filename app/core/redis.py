from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from app.core.config import settings


async def get_redis() -> AsyncGenerator[Redis, None]:
    redis = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )

    try:
        yield redis
    finally:
        await redis.aclose()
