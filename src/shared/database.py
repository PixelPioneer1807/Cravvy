"""Database clients — MongoDB and Redis initialization."""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis

from src.shared.config import settings

logger = logging.getLogger(__name__)

# Module-level clients — initialized on startup, closed on shutdown
_mongo_client: AsyncIOMotorClient | None = None  # type: ignore[type-arg]
_mongo_db: AsyncIOMotorDatabase | None = None  # type: ignore[type-arg]
_redis_client: Redis | None = None  # type: ignore[type-arg]


async def connect_mongo() -> None:
    """Connect to MongoDB and verify with a ping."""
    global _mongo_client, _mongo_db
    _mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
    _mongo_db = _mongo_client[settings.MONGO_DB_NAME]
    await _mongo_client.admin.command("ping")
    logger.info("MongoDB connected — db: %s", settings.MONGO_DB_NAME)


async def connect_redis() -> None:
    """Connect to Redis and verify with a ping."""
    global _redis_client
    _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    await _redis_client.ping()
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


def get_db() -> AsyncIOMotorDatabase:  # type: ignore[type-arg]
    """Get the MongoDB database instance. Fails if not connected."""
    if _mongo_db is None:
        raise RuntimeError("MongoDB not connected — did startup complete?")
    return _mongo_db


def get_redis() -> Redis:  # type: ignore[type-arg]
    """Get the Redis client instance. Fails if not connected."""
    if _redis_client is None:
        raise RuntimeError("Redis not connected — did startup complete?")
    return _redis_client
