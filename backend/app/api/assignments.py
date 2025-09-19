from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..crud import assignments as asg_crud
from ..crud import emails as emails_crud
from ..crud import ideas as ideas_crud
from ..core.security import RoleChecker, get_current_user
from ..services.email import render_template
from ..crud import events as events_crud


router = APIRouter()


class InviteRequest(BaseModel):
    idea_id: int
    developer_email: str | None = None


@router.post("/invite", dependencies=[Depends(RoleChecker(["manager", "admin"]))])
def invite(req: InviteRequest, db: Session = Depends(get_db)):
    dev_id = None
    if req.developer_email:
        # Resolve to user if exists
        from ..crud.users import get_user_by_email

        user = get_user_by_email(db, req.developer_email)
        if user:
            dev_id = user.id
    row = asg_crud.invite(db, idea_id=req.idea_id, developer_id=dev_id)
    subject, body = render_template("assignment.invite", idea_id=req.idea_id)
    to_email = req.developer_email or "developers@example.com"
    emails_crud.queue_email(db, to_email=to_email, subject=subject, body=body)
    try:
        events_crud.record_event(db, entity="assignment", entity_id=row.id, event="invited", payload={"idea_id": req.idea_id, "to": to_email})
    except Exception:
        pass
    return {"id": row.id, "status": row.status}


class RespondRequest(BaseModel):
    assignment_id: int
    response: str  # accept | decline


@router.post("/respond", dependencies=[Depends(RoleChecker(["developer"]))])
def respond(req: RespondRequest, db: Session = Depends(get_db), user = Depends(get_current_user)):
    try:
        row = asg_crud.respond(db, assignment_id=req.assignment_id, developer_id=user.id, response=req.response)
        try:
            events_crud.record_event(db, entity="assignment", entity_id=row.id, event="responded", payload={"developer_id": user.id, "response": req.response})
        except Exception:
            pass
        return {"id": row.id, "status": row.status}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/pending")
def pending(db: Session = Depends(get_db), user = Depends(get_current_user)):
    if user.role in ("admin", "manager"):
        rows = asg_crud.list_assignments(db, status="invited")
    else:
        rows = asg_crud.list_assignments(db, for_user_id=user.id, status="invited")
    return [{"id": r.id, "idea_id": r.idea_id, "status": r.status, "developer_id": r.developer_id} for r in rows]
