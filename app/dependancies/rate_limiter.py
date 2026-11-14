import logging

from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


def rate_limit(
    *,
    max_requests: int = 5,
    window_seconds: int = 60,
    scope: str = "global",
):
    async def dependency(
        request: Request,
        redis: Redis = Depends(get_redis),
    ):
        client_ip = request.client.host if request.client else "unknown"

        key = f"roomly:rate_limit:{scope}:{client_ip}"

        try:
            count = await redis.incr(key)

            if count == 1:
                await redis.expire(key, window_seconds)

            if count > max_requests:
                ttl = await redis.ttl(key)

                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Try again later.",
                    headers={"Retry-After": str(max(ttl, 1))},
                )

        except RedisError:
            logger.exception("Rate limiter Redis operation failed")

    return dependency
