from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..crud.users import get_user_by_email
from ..core.security import RoleChecker, ROLES, get_current_user


router = APIRouter()


class AssignRoleRequest(BaseModel):
    email: str
    role: str


class UserOut(BaseModel):
    email: str
    full_name: str | None = None
    role: str
    department: str | None = None


@router.post("/assign-role", dependencies=[Depends(RoleChecker(["admin"]))])
def assign_role(payload: AssignRoleRequest, db: Session = Depends(get_db)) -> UserOut:
    role = payload.role.strip().lower()
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    user = get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(email=user.email, full_name=user.full_name, role=user.role, department=user.department)


@router.get("/me", response_model=UserOut)
def get_me(current = Depends(get_current_user)) -> UserOut:
    return UserOut(email=current.email, full_name=current.full_name, role=current.role, department=current.department)

