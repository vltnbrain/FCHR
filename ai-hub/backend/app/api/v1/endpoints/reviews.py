"""
Reviews API endpoints for AI Hub
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Review, Idea, IdeaStatus, User
from app.core.security import require_roles
from app.services import IdeaService, AuditService, EmailService

from pydantic import BaseModel


router = APIRouter()


class ReviewCreate(BaseModel):
    idea_id: int
    stage: str  # 'analyst' | 'finance'
    decision: str  # 'accepted' | 'rejected' | 'needs_info'
    notes: Optional[str] = None
    recommended_department: Optional[str] = None


@router.post("/", dependencies=[Depends(require_roles(["analyst", "finance", "manager", "admin"]))])
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    idea = (await db.execute(select(Idea).where(Idea.id == data.idea_id))).scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Save review
    reviewer = (await db.execute(select(User).limit(1))).scalar_one_or_none()
    review = Review(
        idea_id=idea.id,
        reviewer_user_id=reviewer.id if reviewer else 0,
        stage=data.stage,
        decision=data.decision,
        notes=data.notes,
        recommended_department=data.recommended_department,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(review)
    await db.commit()

    # Transition logic
    if data.stage == "analyst":
        if data.decision == "accepted":
            idea.status = IdeaStatus.FINANCE_REVIEW
            await db.commit()
            await EmailService.queue_finance_review_email(db, idea.id)
        elif data.decision == "rejected":
            idea.status = IdeaStatus.REJECTED
            await db.commit()
        # needs_info -> remain in ANALYST_REVIEW
    elif data.stage == "finance":
        if data.decision == "accepted":
            # Move to developer assignment
            await IdeaService.route_to_developers(db, idea.id)
        elif data.decision == "rejected":
            idea.status = IdeaStatus.REJECTED
            await db.commit()

    await AuditService.log_event(
        db, "review", review.id, "created", None, {"idea_id": idea.id, "stage": data.stage, "decision": data.decision}
    )

    return {"message": "Review created", "idea_status": idea.status}


@router.get("/")
async def list_reviews(
    idea_id: Optional[int] = Query(None),
    stage: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Review)
    if idea_id:
        query = query.where(Review.idea_id == idea_id)
    if stage:
        query = query.where(Review.stage == stage)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    reviews = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [
        {
            "id": r.id,
            "idea_id": r.idea_id,
            "stage": r.stage,
            "decision": r.decision,
            "notes": r.notes,
            "recommended_department": r.recommended_department,
            "decided_at": r.decided_at.isoformat(),
        } for r in reviews
    ], "total": total, "skip": skip, "limit": limit}
