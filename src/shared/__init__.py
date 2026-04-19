"""Shared utilities — config, database clients, base exceptions, encryption."""

from src.shared.config import settings as settings
from src.shared.database import connect_mongo as connect_mongo
from src.shared.database import connect_redis as connect_redis
from src.shared.database import disconnect_mongo as disconnect_mongo
from src.shared.database import disconnect_redis as disconnect_redis
from src.shared.database import get_db as get_db
from src.shared.database import get_redis as get_redis
from src.shared.encryption import decrypt as decrypt
from src.shared.encryption import decrypt_or_none as decrypt_or_none
from src.shared.encryption import encrypt as encrypt
from src.shared.encryption import encrypt_or_none as encrypt_or_none
from src.shared.exceptions import AppError as AppError
from src.shared.exceptions import AuthError as AuthError
from src.shared.exceptions import ExternalServiceError as ExternalServiceError
from src.shared.exceptions import ForbiddenError as ForbiddenError
from src.shared.exceptions import NotFoundError as NotFoundError
from src.shared.exceptions import RateLimitError as RateLimitError
from src.shared.exceptions import ValidationError as ValidationError

__all__ = [
    "AppError",
    "AuthError",
    "ExternalServiceError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "connect_mongo",
    "connect_redis",
    "decrypt",
    "decrypt_or_none",
    "disconnect_mongo",
    "disconnect_redis",
    "encrypt",
    "encrypt_or_none",
    "get_db",
    "get_redis",
    "settings",
]
