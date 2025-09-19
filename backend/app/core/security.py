from typing import List
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import os
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db import models


ROLES = {
    "developer",
    "analyst",
    "finance",
    "manager",
    "admin",
    "user",
}


bearer = HTTPBearer(auto_error=False)


def get_current_user(db: Session = Depends(get_db), creds: HTTPAuthorizationCredentials = Depends(bearer)) -> models.User:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = creds.credentials
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY", "please-change-in-prod"),
            algorithms=[os.getenv("JWT_ALGORITHM", "HS256")],
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


class RoleChecker:
    def __init__(self, allowed: List[str]):
        self.allowed = set(allowed)

    def __call__(self, user: models.User = Depends(get_current_user)):
        if user.role not in self.allowed:
            raise HTTPException(status_code=403, detail="Forbidden")
