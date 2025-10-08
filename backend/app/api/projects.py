from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.security import get_current_user
from ..crud import ideas as ideas_crud
from ..crud import assignments as assignments_crud
from ..crud import reviews as reviews_crud
from ..db import models
from ..db.session import get_db

router = APIRouter()


class StatusCount(BaseModel):
    status: str
    count: int


class ProjectCard(BaseModel):
    id: int
    title: str
    status: Optional[str] = None
    owner_email: Optional[str] = None
    created_at: Optional[datetime] = None


class ReviewCard(BaseModel):
    id: int
    idea_id: int
    idea_title: str
    stage: str
    decision: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewer_email: Optional[str] = None
    created_at: Optional[datetime] = None


class AssignmentCard(BaseModel):
    id: int
    idea_id: int
    idea_title: str
    assignment_status: str
    idea_status: Optional[str] = None
    developer_id: Optional[int] = None
    created_at: Optional[datetime] = None


class OverviewResponse(BaseModel):
    role: str
    my_projects: List[ProjectCard]
    company_projects: List[ProjectCard]
    status_counts: List[StatusCount]
    analyst_queue: List[ReviewCard] = []
    finance_queue: List[ReviewCard] = []
    developer_assignments: List[AssignmentCard] = []
    invites: List[AssignmentCard] = []


def _resolve_user_emails(db: Session, user_ids: List[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    rows = (
        db.execute(select(models.User).where(models.User.id.in_(set(user_ids))))
        .scalars()
        .all()
    )
    return {row.id: row.email for row in rows}


def _idea_to_card(idea: models.Idea, owner_email: Optional[str]) -> ProjectCard:
    return ProjectCard(
        id=idea.id,
        title=idea.title,
        status=getattr(idea, "status", None),
        owner_email=idea.author_email or owner_email,
        created_at=getattr(idea, "created_at", None),
    )


@router.get("/overview", response_model=OverviewResponse)
def projects_overview(user = Depends(get_current_user), db: Session = Depends(get_db)) -> OverviewResponse:
    my_ideas_rows = ideas_crud.list_ideas_for_user(db, user_id=user.id)
    owner_lookup = _resolve_user_emails(db, [user.id])
    my_projects = [_idea_to_card(row, owner_lookup.get(row.created_by_id)) for row in my_ideas_rows]

    company_rows = (
        db.execute(select(models.Idea).order_by(models.Idea.created_at.desc()).limit(20))
        .scalars()
        .all()
    )
    creator_ids = [row.created_by_id for row in company_rows if row.created_by_id]
    creator_lookup = _resolve_user_emails(db, creator_ids)
    company_projects = [_idea_to_card(row, creator_lookup.get(row.created_by_id)) for row in company_rows]

    status_counts_rows = db.execute(
        select(models.Idea.status, func.count(models.Idea.id)).group_by(models.Idea.status)
    ).all()
    status_counts = [StatusCount(status=row[0] or "unknown", count=row[1]) for row in status_counts_rows]

    analyst_queue: List[ReviewCard] = []
    finance_queue: List[ReviewCard] = []
    developer_assignments: List[AssignmentCard] = []
    invites: List[AssignmentCard] = []

    if user.role in ("analyst", "admin"):
        pending = reviews_crud.list_pending_for_stage(db, stage="analyst", reviewer_id=None if user.role == "admin" else user.id)
        idea_ids = [rev.idea_id for rev in pending]
        idea_lookup = {idea.id: idea for idea in db.execute(select(models.Idea).where(models.Idea.id.in_(idea_ids))).scalars().all()}
        reviewer_lookup = _resolve_user_emails(db, [rev.reviewer_id for rev in pending if rev.reviewer_id])
        for rev in pending:
            idea = idea_lookup.get(rev.idea_id)
            if not idea:
                continue
            analyst_queue.append(
                ReviewCard(
                    id=rev.id,
                    idea_id=rev.idea_id,
                    idea_title=idea.title,
                    stage=rev.stage,
                    decision=rev.decision,
                    reviewer_id=rev.reviewer_id,
                    reviewer_email=reviewer_lookup.get(rev.reviewer_id),
                    created_at=rev.created_at,
                )
            )

    if user.role in ("finance", "admin"):
        pending = reviews_crud.list_pending_for_stage(db, stage="finance", reviewer_id=None if user.role == "admin" else user.id)
        idea_ids = [rev.idea_id for rev in pending]
        idea_lookup = {idea.id: idea for idea in db.execute(select(models.Idea).where(models.Idea.id.in_(idea_ids))).scalars().all()}
        reviewer_lookup = _resolve_user_emails(db, [rev.reviewer_id for rev in pending if rev.reviewer_id])
        for rev in pending:
            idea = idea_lookup.get(rev.idea_id)
            if not idea:
                continue
            finance_queue.append(
                ReviewCard(
                    id=rev.id,
                    idea_id=rev.idea_id,
                    idea_title=idea.title,
                    stage=rev.stage,
                    decision=rev.decision,
                    reviewer_id=rev.reviewer_id,
                    reviewer_email=reviewer_lookup.get(rev.reviewer_id),
                    created_at=rev.created_at,
                )
            )

    if user.role in ("developer", "admin"):
        assignments = assignments_crud.list_assignments(db, for_user_id=user.id if user.role != "admin" else None)
        idea_ids = [assignment.idea_id for assignment in assignments]
        idea_lookup = {idea.id: idea for idea in db.execute(select(models.Idea).where(models.Idea.id.in_(idea_ids))).scalars().all()}
        for assignment in assignments:
            idea = idea_lookup.get(assignment.idea_id)
            if not idea:
                continue
            card = AssignmentCard(
                id=assignment.id,
                idea_id=assignment.idea_id,
                idea_title=idea.title,
                assignment_status=assignment.status,
                idea_status=getattr(idea, "status", None),
                developer_id=assignment.developer_id,
                created_at=assignment.created_at,
            )
            developer_assignments.append(card)
            if assignment.status == "invited" and (user.role == "developer" or user.role == "admin"):
                invites.append(card)

    return OverviewResponse(
        role=user.role,
        my_projects=my_projects,
        company_projects=company_projects,
        status_counts=status_counts,
        analyst_queue=analyst_queue,
        finance_queue=finance_queue,
        developer_assignments=developer_assignments,
        invites=invites,
    )
