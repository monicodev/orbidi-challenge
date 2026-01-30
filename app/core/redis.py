import json
from typing import Any, Optional
from redis import asyncio as aioredis
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self.client: Optional[aioredis.Redis] = None

    def init(self):
        """Initialize the Redis pool."""
        self.client = aioredis.from_url(
            settings.REDIS_URL, 
            decode_responses=True,
            encoding="utf-8"
        )

    async def get_cache(self, key: str) -> Any:
        """Retrieve and parse JSON data from cache."""
        if not self.client:
            return None
        data = await self.client.get(key)
        return json.loads(data) if data else None

    async def set_cache(self, key: str, value: Any, expire: int = 300):
        """Store data as JSON with a Time-To-Live (TTL)."""
        if self.client:
            await self.client.set(
                key, 
                json.dumps(value), 
                ex=expire
            )

    async def close(self):
        """Close connection pool."""
        if self.client:
            await self.client.close()

# Singleton instance
redis_client = RedisClient()