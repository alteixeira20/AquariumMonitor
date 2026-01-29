from __future__ import annotations

import hashlib
import secrets

import bcrypt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    payload = password[:72].encode("utf-8")
    hashed = bcrypt.hashpw(payload, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    payload = password[:72].encode("utf-8")
    return bcrypt.checkpw(payload, password_hash.encode("utf-8"))


def generate_device_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_device_api_key(api_key: str) -> str:
    settings = get_settings()
    payload = f"{settings.device_api_key_pepper}:{api_key}".encode()
    return hashlib.sha256(payload).hexdigest()
