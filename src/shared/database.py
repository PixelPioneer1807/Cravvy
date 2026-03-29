"""Database clients — MongoDB and Redis initialization."""

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis

from src.shared.config import settings

logger = logging.getLogger(__name__)

# Module-level clients — initialized on startup, closed on shutdown
_mongo_client: Any = None
_mongo_db: Any = None
_redis_client: Any = None


async def connect_mongo() -> None:
    """Connect to MongoDB and verify with a ping."""
    global _mongo_client, _mongo_db
    client: Any = AsyncIOMotorClient(settings.MONGO_URI)
    db: Any = client[settings.MONGO_DB_NAME]
    await client.admin.command("ping")
    _mongo_client = client
    _mongo_db = db
    logger.info("MongoDB connected — db: %s", settings.MONGO_DB_NAME)


async def connect_redis() -> None:
    """Connect to Redis and verify with a ping."""
    global _redis_client
    client: Any = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    await client.ping()
    _redis_client = client
    logger.info("Redis connected")


async def disconnect_mongo() -> None:
    """Close MongoDB connection."""
    global _mongo_client, _mongo_db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        logger.info("MongoDB disconnected")


async def disconnect_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis disconnected")


def get_db() -> Any:
    """Get the MongoDB database instance. Fails if not connected."""
    if _mongo_db is None:
        raise RuntimeError("MongoDB not connected — did startup complete?")
    return _mongo_db


def get_redis() -> Any:
    """Get the Redis client instance. Fails if not connected."""
    if _redis_client is None:
        raise RuntimeError("Redis not connected — did startup complete?")
    return _redis_client
