"""
JWT utilities for MVP auth.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import Depends, Header, HTTPException, status
from jose import jwt, JWTError

from app.core.config import settings


ALGORITHM = "HS256"


def create_access_token(subject: str, role: str, expires_minutes: int = 60 * 24) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "iss": settings.SERVER_NAME,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def _parse_bearer(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_role_from_auth(
    authorization: Optional[str] = Header(default=None)
) -> Tuple[Optional[str], Optional[int]]:
    """Extract (role, user_id) from Bearer token if present."""
    token = _parse_bearer(authorization)
    if not token:
        return None, None
    payload = decode_token(token)
    role = str(payload.get("role") or "").lower() or None
    sub = payload.get("sub")
    try:
        user_id = int(sub) if sub is not None else None
    except ValueError:
        user_id = None
    return role, user_id

