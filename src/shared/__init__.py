"""Shared utilities — config, database clients, base exceptions."""

from src.shared.config import Settings as Settings
from src.shared.config import settings as settings

__all__ = [
    "Settings",
    "settings",
]
