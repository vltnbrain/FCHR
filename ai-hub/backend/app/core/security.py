"""
Minimal security & RBAC utilities for MVP/testing.
Prefers JWT Bearer role; falls back to `x-user-role` header for dev.
"""
from typing import Iterable, Set, Tuple
from fastapi import Depends, Header, HTTPException, status

from app.core.auth import get_role_from_auth


async def get_current_role(
    x_user_role: str | None = Header(default=None),
    role_and_uid: Tuple[str | None, int | None] = Depends(get_role_from_auth),
) -> str:
    """Extract current role: prefer JWT, fallback to header; default 'developer'."""
    jwt_role, _ = role_and_uid
    role = jwt_role or x_user_role or "developer"
    return role.lower()


def require_roles(allowed: Iterable[str]):
    allowed_set: Set[str] = {r.lower() for r in allowed}

    async def _checker(role: str = Depends(get_current_role)) -> None:
        if role not in allowed_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return _checker
