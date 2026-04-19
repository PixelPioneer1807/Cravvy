"""AES-256-GCM field-level encryption for PII at rest.

How it works:
    1. encrypt("hello") → base64 string containing: nonce + ciphertext + auth tag
    2. decrypt(encrypted_string) → "hello"

AES-256-GCM provides:
    - Confidentiality: data is encrypted (AES-256)
    - Integrity: tampered ciphertext fails decryption (GCM auth tag)
    - Authenticity: proves data was encrypted by someone with the key

Each encrypt() call generates a fresh 12-byte nonce (IV). This means
encrypting the same plaintext twice produces different ciphertext — an
attacker can't tell if two users have the same email by comparing encrypted values.

Storage format: base64(nonce + ciphertext + tag) → single string in MongoDB.
"""

import base64
import logging
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.shared.config import settings

logger = logging.getLogger(__name__)

# AES-256 needs a 32-byte key. We store it as 64 hex chars in the env var.
_key_cache: bytes | None = None


def _get_key() -> bytes:
    """Lazily load and cache the encryption key from settings."""
    global _key_cache
    if _key_cache is None:
        if not settings.ENCRYPTION_KEY:
            raise RuntimeError(
                "ENCRYPTION_KEY is not set. "
                'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        _key_cache = bytes.fromhex(settings.ENCRYPTION_KEY)
        if len(_key_cache) != 32:
            raise RuntimeError("ENCRYPTION_KEY must be exactly 64 hex characters (32 bytes)")
    return _key_cache


def encrypt(plaintext: str) -> str:
    """Encrypt a string with AES-256-GCM. Returns base64-encoded ciphertext.

    Each call uses a fresh random nonce — same input produces different output.
    """
    key = _get_key()
    aesgcm = AESGCM(key)

    # 12-byte nonce recommended by NIST for GCM
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    # Pack nonce + ciphertext into one blob, then base64 for safe storage
    # ciphertext already includes the 16-byte auth tag (appended by GCM)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt(encrypted: str) -> str:
    """Decrypt a base64-encoded AES-256-GCM ciphertext back to plaintext."""
    key = _get_key()
    aesgcm = AESGCM(key)

    raw = base64.b64decode(encrypted)

    # First 12 bytes = nonce, rest = ciphertext + auth tag
    nonce = raw[:12]
    ciphertext = raw[12:]

    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext_bytes.decode("utf-8")


def encrypt_or_none(value: str | None) -> str | None:
    """Encrypt if value exists, return None if None. Convenience for optional fields."""
    if value is None:
        return None
    return encrypt(value)


def decrypt_or_none(value: str | None) -> str | None:
    """Decrypt if value exists, return None if None. Convenience for optional fields."""
    if value is None:
        return None
    return decrypt(value)
