"""
Auth endpoints (MVP): issue JWT tokens by email; no passwords for now.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User, UserRole, Department
from app.core.auth import create_access_token


router = APIRouter()


class TokenRequest(BaseModel):
    email: EmailStr
    role: UserRole | None = None
    full_name: str | None = None
    department: Department | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
async def issue_token(data: TokenRequest, db: AsyncSession = Depends(get_db)):
    # Find or create user by email (passwordless MVP)
    user = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
    if not user:
        user = User(
            email=data.email,
            full_name=data.full_name or data.email.split("@")[0],
            role=data.role or UserRole.DEVELOPER,
            department=data.department or Department.ENGINEERING,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(str(user.id), user.role.value)
    return TokenResponse(access_token=token)

