from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError

from app.dependancies.rate_limiter import rate_limit


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("max_requests", "window_seconds", "scope", "client_ip", "count"),
    [
        (5, 60, "global", "192.168.1.10", 1),
        (10, 300, "api", "10.0.0.25", 3),
        (100, 1, "login", "203.0.113.42", 100),
    ],
    ids=[
        "first-request-global-scope",
        "request-with-custom-scope",
        "request-at-limit",
    ],
)
async def test_rate_limit_allows_requests_and_sets_expiry_on_first_request(
    max_requests,
    window_seconds,
    scope,
    client_ip,
    count,
):
    # Arrange
    redis = MagicMock()
    redis.incr = AsyncMock(return_value=count)
    redis.expire = AsyncMock()
    request = MagicMock()
    request.client.host = client_ip

    dependency = rate_limit(
        max_requests=max_requests,
        window_seconds=window_seconds,
        scope=scope,
    )

    # Act
    result = await dependency(request, redis)

    # Assert
    key = f"roomly:rate_limit:{scope}:{client_ip}"

    assert result is None
    redis.incr.assert_awaited_once_with(key)

    if count == 1:
        redis.expire.assert_awaited_once_with(key, window_seconds)
    else:
        redis.expire.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("max_requests", "window_seconds", "scope", "count"),
    [
        (5, 60, "global", 2),
        (5, 1, "short-window", 5),
        (100, 3600, "high-volume", 100),
    ],
    ids=[
        "subsequent-request-at-limit",
        "minimum-window-at-limit",
        "large-request-limit",
    ],
)
async def test_rate_limit_allows_requests_at_limit_without_expiring_again(
    max_requests,
    window_seconds,
    scope,
    count,
):
    # Arrange
    redis = MagicMock()
    redis.incr = AsyncMock(return_value=count)
    redis.expire = AsyncMock()
    request = MagicMock()
    request.client.host = "198.51.100.7"

    dependency = rate_limit(
        max_requests=max_requests,
        window_seconds=window_seconds,
        scope=scope,
    )

    # Act
    result = await dependency(request, redis)

    # Assert
    key = f"roomly:rate_limit:{scope}:198.51.100.7"

    assert result is None
    redis.incr.assert_awaited_once_with(key)
    redis.expire.assert_not_awaited()
    redis.ttl.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("max_requests", "window_seconds", "scope", "count", "ttl", "retry_after"),
    [
        (5, 60, "global", 6, 42, "42"),
        (1, 300, "login", 2, 0, "1"),
        (10, 120, "api", 11, -1, "1"),
    ],
    ids=[
        "over-limit-with-positive-ttl",
        "over-limit-with-zero-ttl",
        "over-limit-with-negative-ttl",
    ],
)
async def test_rate_limit_rejects_requests_over_limit(
    max_requests,
    window_seconds,
    scope,
    count,
    ttl,
    retry_after,
):
    # Arrange
    redis = MagicMock()
    redis.incr = AsyncMock(return_value=count)
    redis.expire = AsyncMock()
    redis.ttl = AsyncMock(return_value=ttl)
    request = MagicMock()
    request.client.host = "203.0.113.15"

    dependency = rate_limit(
        max_requests=max_requests,
        window_seconds=window_seconds,
        scope=scope,
    )

    # Act
    with pytest.raises(HTTPException) as exc_info:
        await dependency(request, redis)

    # Assert
    key = f"roomly:rate_limit:{scope}:203.0.113.15"

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Too many requests. Try again later."
    assert exc_info.value.headers == {"Retry-After": retry_after}
    redis.incr.assert_awaited_once_with(key)
    redis.expire.assert_not_awaited()
    redis.ttl.assert_awaited_once_with(key)


@pytest.mark.asyncio
async def test_rate_limit_uses_unknown_when_request_has_no_client():
    # Arrange
    redis = MagicMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock()
    request = MagicMock()
    request.client = None

    dependency = rate_limit()

    # Act
    result = await dependency(request, redis)

    # Assert
    key = "roomly:rate_limit:global:unknown"

    assert result is None
    redis.incr.assert_awaited_once_with(key)
    redis.expire.assert_awaited_once_with(key, 40)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    ["incr", "expire", "ttl"],
    ids=[
        "redis-increment-error",
        "redis-expiry-error",
        "redis-ttl-error",
    ],
)
async def test_rate_limit_ignores_redis_errors(operation):
    # Arrange
    redis = MagicMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock()
    redis.ttl = AsyncMock(return_value=30)
    request = MagicMock()
    request.client.host = "192.0.2.20"

    if operation == "incr":
        redis.incr.side_effect = RedisError("increment failed")
    elif operation == "expire":
        redis.expire.side_effect = RedisError("expiry failed")
    else:
        redis.incr.return_value = 6
        redis.ttl.side_effect = RedisError("ttl failed")

    dependency = rate_limit(max_requests=5)

    # Act
    result = await dependency(request, redis)

    # Assert
    assert result is None
