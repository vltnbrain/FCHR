from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
from jose import jwt
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..crud.users import get_user_by_email, create_user, count_users
from ..core.passwords import hash_password, verify_password
from ..core.security import get_current_user


router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    email: str
    role: str


@router.post("/register", response_model=TokenResponse)
def register(req: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if not req.email or not req.password:
        raise HTTPException(status_code=400, detail="Invalid input")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password too short (min 8)")
    existing = get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    ph = hash_password(req.password)
    # First registered user becomes admin (bootstrap)
    role = "admin" if count_users(db) == 0 else "user"
    user = create_user(db, email=req.email, password_hash=ph, role=role)

    secret = os.getenv("SECRET_KEY", "please-change-in-prod")
    alg = os.getenv("JWT_ALGORITHM", "HS256")
    minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    payload = {
        "sub": user.email,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=minutes),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, secret, algorithm=alg)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def me(user = Depends(get_current_user)) -> MeResponse:
    return MeResponse(email=user.email, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if not req.email or not req.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    user = get_user_by_email(db, req.email)
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    secret = os.getenv("SECRET_KEY", "please-change-in-prod")
    alg = os.getenv("JWT_ALGORITHM", "HS256")
    minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    payload = {
        "sub": user.email,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=minutes),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, secret, algorithm=alg)
    return TokenResponse(access_token=token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(user = Depends(get_current_user)) -> TokenResponse:
    import os as _os
    secret = _os.getenv("SECRET_KEY", "please-change-in-prod")
    alg = _os.getenv("JWT_ALGORITHM", "HS256")
    minutes = int(_os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    payload = {
        "sub": user.email,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=minutes),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, secret, algorithm=alg)
    return TokenResponse(access_token=token)
