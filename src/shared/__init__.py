"""Shared utilities — config, database clients, base exceptions."""

from src.shared.config import settings as settings
from src.shared.database import get_db as get_db
from src.shared.database import get_redis as get_redis

__all__ = [
    "settings",
    "get_db",
    "get_redis",
]
