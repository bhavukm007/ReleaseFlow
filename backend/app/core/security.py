import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.core.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def create_access_token(user_id: UUID) -> tuple[str, datetime]:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    token = jwt.encode({"sub": str(user_id), "type": "access", "exp": expires}, settings.jwt_secret, algorithm=ALGORITHM)
    return token, expires


def create_refresh_token(user_id: UUID) -> tuple[str, str, datetime]:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)
    nonce = secrets.token_urlsafe(32)
    token = jwt.encode(
        {"sub": str(user_id), "type": "refresh", "nonce": nonce, "exp": expires},
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )
    return token, token_hash(token), expires


def decode_token(token: str, expected_type: str) -> UUID:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            raise ValueError("Invalid token type")
        return UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired authentication token") from exc


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
