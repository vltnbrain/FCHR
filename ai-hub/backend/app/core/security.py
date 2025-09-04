"""
Minimal security & RBAC utilities for MVP/testing.
"""
from typing import Iterable, Set
from fastapi import Depends, Header, HTTPException, status


async def get_current_role(x_user_role: str | None = Header(default=None)) -> str:
    """Extract current role from header; default to 'developer' if absent."""
    return (x_user_role or "developer").lower()


def require_roles(allowed: Iterable[str]):
    allowed_set: Set[str] = {r.lower() for r in allowed}

    async def _checker(role: str = Depends(get_current_role)) -> None:
        if role not in allowed_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return _checker

