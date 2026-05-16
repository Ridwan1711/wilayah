import json
from typing import Any

import redis.asyncio as redis

from app.core.config import Settings


class RedisCache:
    def __init__(self, settings: Settings) -> None:
        self._ttl = settings.cache_ttl_seconds
        self._client: redis.Redis | None = None
        if settings.redis_url:
            self._client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

    async def get(self, key: str) -> Any | None:
        if self._client is None:
            return None
        try:
            cached = await self._client.get(key)
            return json.loads(cached) if cached else None
        except (redis.RedisError, json.JSONDecodeError):
            return None

    async def set(self, key: str, value: Any) -> None:
        if self._client is None:
            return
        try:
            await self._client.setex(key, self._ttl, json.dumps(value, ensure_ascii=False))
        except (redis.RedisError, TypeError):
            return

    async def ping(self) -> bool:
        if self._client is None:
            return False
        try:
            return bool(await self._client.ping())
        except redis.RedisError:
            return False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
