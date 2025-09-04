"""
Users API endpoints for AI Hub
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.db.session import get_db
from app.models.user import User, UserRole, Department
from app.schemas.user import UserCreate, UserResponse, UserListResponse
from app.core.config import settings
from app.core.security import require_roles

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    department: Optional[str] = Query(None, description="Filter by department"),
    q: Optional[str] = Query(None, description="Search by name or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)

    if role:
        query = query.where(User.role == UserRole(role))
    if department:
        query = query.where(User.department == Department(department))
    if q:
        ql = f"%{q.lower()}%"
        query = query.where(or_(func.lower(User.full_name).like(ql), func.lower(User.email).like(ql)))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
    users = (await db.execute(query)).scalars().all()

    return UserListResponse(
        items=[UserResponse.from_orm(u) for u in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=UserResponse, dependencies=[Depends(require_roles(["admin", "manager"]))])
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    # Check unique email
    exists = (await db.execute(select(User).where(User.email == user_data.email))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        role=user_data.role,
        department=user_data.department,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.from_orm(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)
