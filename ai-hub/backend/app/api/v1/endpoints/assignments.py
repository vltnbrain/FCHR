"""
Assignments and Marketplace API endpoints for AI Hub
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import Assignment, Idea, IdeaStatus, MarketplaceEntry
from app.services.email_service import EmailService
from app.core.security import require_roles


router = APIRouter()


class AssignmentCreate(BaseModel):
    idea_id: int
    developer_user_id: int


class AssignmentUpdate(BaseModel):
    action: str  # "accept" | "decline"


@router.post("/", dependencies=[Depends(require_roles(["manager", "admin"]))])
async def create_assignment(
    payload: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
):
    idea = (await db.execute(select(Idea).where(Idea.id == payload.idea_id))).scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    a = Assignment(
        idea_id=payload.idea_id,
        developer_user_id=payload.developer_user_id,
        status="invited",
        invited_at=datetime.now(timezone.utc),
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)

    await EmailService.queue_developer_invitation_email(db, payload.idea_id, payload.developer_user_id)

    return {"id": a.id, "status": a.status}


@router.put("/{assignment_id}")
async def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    a = (await db.execute(select(Assignment).where(Assignment.id == assignment_id))).scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")

    action = payload.action.lower().strip()
    if action not in {"accept", "decline"}:
        raise HTTPException(status_code=400, detail="Invalid action")

    a.status = "accepted" if action == "accept" else "declined"
    a.responded_at = datetime.now(timezone.utc)
    await db.commit()

    # If accepted, move idea to implementation
    if action == "accept":
        idea = (await db.execute(select(Idea).where(Idea.id == a.idea_id))).scalar_one_or_none()
        if idea and idea.status == IdeaStatus.DEVELOPER_ASSIGNMENT:
            idea.status = IdeaStatus.IMPLEMENTATION
            await db.commit()

    return {"id": assignment_id, "status": a.status}


@router.get("/")
async def list_assignments(
    developer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Assignment, Idea).join(Idea, Assignment.idea_id == Idea.id)
    if developer_id:
        query = query.where(Assignment.developer_user_id == developer_id)
    if status:
        query = query.where(Assignment.status == status)

    result = await db.execute(query)
    rows = result.all()
    items = [
        {
            "id": a.id,
            "status": a.status,
            "invited_at": a.invited_at.isoformat() if a.invited_at else None,
            "responded_at": a.responded_at.isoformat() if a.responded_at else None,
            "idea": {
                "id": i.id,
                "title": i.title,
                "status": i.status,
                "created_at": i.created_at.isoformat(),
            },
        }
        for (a, i) in rows
    ]
    return {"items": items}


# Marketplace
@router.get("/marketplace")
async def list_marketplace(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MarketplaceEntry, Idea).join(Idea, MarketplaceEntry.idea_id == Idea.id))
    rows = result.all()
    items = [
        {
            "idea": {
                "id": i.id,
                "title": i.title,
                "status": i.status,
                "created_at": i.created_at.isoformat(),
            },
            "listed_at": m.listed_at.isoformat() if m.listed_at else None,
        }
        for (m, i) in rows
    ]
    return {"items": items}


class ClaimRequest(BaseModel):
    developer_user_id: int


@router.post("/marketplace/{idea_id}/claim")
async def claim_marketplace(
    idea_id: int,
    payload: ClaimRequest,
    db: AsyncSession = Depends(get_db),
):
    # Ensure marketplace entry exists
    m = (await db.execute(select(MarketplaceEntry).where(MarketplaceEntry.idea_id == idea_id))).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Marketplace entry not found for idea")

    # Create accepted assignment
    a = Assignment(
        idea_id=idea_id,
        developer_user_id=payload.developer_user_id,
        status="accepted",
        invited_at=datetime.now(timezone.utc),
        responded_at=datetime.now(timezone.utc),
    )
    db.add(a)

    # Remove marketplace entry
    await db.delete(m)
    await db.commit()

    # Set idea to implementation
    idea = (await db.execute(select(Idea).where(Idea.id == idea_id))).scalar_one_or_none()
    if idea and idea.status == IdeaStatus.DEVELOPER_ASSIGNMENT:
        idea.status = IdeaStatus.IMPLEMENTATION
        await db.commit()

    return {"assignment_id": a.id, "status": a.status}
