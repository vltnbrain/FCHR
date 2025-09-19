from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..crud import reviews as reviews_crud
from ..crud import events as events_crud
from ..crud import emails as emails_crud
from ..crud import ideas as ideas_crud
from ..services.email import render_template
from ..crud import events as events_crud
from ..core.security import RoleChecker, get_current_user


router = APIRouter()


class ReviewRequest(BaseModel):
    idea_id: int
    stage: str  # analyst | finance


@router.post("/request", dependencies=[Depends(RoleChecker(["manager", "admin"]))])
def request_review(payload: ReviewRequest, db: Session = Depends(get_db)):
    if payload.stage not in ("analyst", "finance"):
        raise HTTPException(status_code=400, detail="Invalid stage")
    row = reviews_crud.create_review(db, idea_id=payload.idea_id, stage=payload.stage)
    # Update idea status
    if payload.stage == "analyst":
        ideas_crud.set_idea_status(db, idea_id=payload.idea_id, status="analyst_pending")
    else:
        ideas_crud.set_idea_status(db, idea_id=payload.idea_id, status="finance_pending")
    # Notify via email queue (template)
    subject, body = render_template("review.request", stage=payload.stage, idea_id=payload.idea_id)
    emails_crud.queue_email(db, to_email="analyst-team@example.com" if payload.stage == "analyst" else "finance-team@example.com", subject=subject, body=body)
    try:
        events_crud.record_event(db, entity="idea", entity_id=payload.idea_id, event="review_requested", payload={"stage": payload.stage})
    except Exception:
        pass
    return {"id": row.id, "stage": row.stage, "decision": row.decision}


class DecisionRequest(BaseModel):
    idea_id: int
    decision: str  # approved | rejected | needs_more_info
    notes: str | None = None


@router.post("/analyst/decision", dependencies=[Depends(RoleChecker(["analyst"]))])
def analyst_decision(payload: DecisionRequest, db: Session = Depends(get_db), user = Depends(get_current_user)):
    row = reviews_crud.set_decision(db, idea_id=payload.idea_id, stage="analyst", decision=payload.decision, notes=payload.notes, reviewer_id=user.id)
    # Progression
    if payload.decision == "approved":
        ideas_crud.set_idea_status(db, idea_id=payload.idea_id, status="finance_pending")
        # auto-request finance review and notify
        fr = reviews_crud.create_review(db, idea_id=payload.idea_id, stage="finance")
        subject, body = render_template("review.request", stage="finance", idea_id=payload.idea_id)
        emails_crud.queue_email(db, to_email="finance-team@example.com", subject=subject, body=body)
    elif payload.decision == "rejected":
        ideas_crud.set_idea_status(db, idea_id=payload.idea_id, status="rejected")
    try:
        events_crud.record_event(db, entity="review", entity_id=row.id, event="decision", payload={"decision": payload.decision, "stage": "analyst"})
    except Exception:
        pass
    return {"id": row.id, "stage": row.stage, "decision": row.decision}


@router.post("/finance/decision", dependencies=[Depends(RoleChecker(["finance"]))])
def finance_decision(payload: DecisionRequest, db: Session = Depends(get_db), user = Depends(get_current_user)):
    row = reviews_crud.set_decision(db, idea_id=payload.idea_id, stage="finance", decision=payload.decision, notes=payload.notes, reviewer_id=user.id)
    # Finalize status
    if payload.decision == "approved":
        ideas_crud.set_idea_status(db, idea_id=payload.idea_id, status="approved")
    elif payload.decision == "rejected":
        ideas_crud.set_idea_status(db, idea_id=payload.idea_id, status="rejected")
    try:
        events_crud.record_event(db, entity="review", entity_id=row.id, event="decision", payload={"decision": payload.decision, "stage": "finance"})
    except Exception:
        pass
    return {"id": row.id, "stage": row.stage, "decision": row.decision}


@router.get("/pending")
def pending(stage: str = Query(..., pattern="^(analyst|finance)$"), db: Session = Depends(get_db)):
    rows = reviews_crud.list_pending(db, stage=stage)
    return [{"id": r.id, "idea_id": r.idea_id, "stage": r.stage, "created_at": r.created_at.isoformat()} for r in rows]
