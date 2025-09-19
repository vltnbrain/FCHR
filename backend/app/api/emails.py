from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..crud import emails as emails_crud
from ..core.security import RoleChecker
from ..services.email import is_retryable


router = APIRouter()


class QueueEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str


@router.post("/queue", dependencies=[Depends(RoleChecker(["admin"]))])
def queue_email(req: QueueEmailRequest, db: Session = Depends(get_db)):
    row = emails_crud.queue_email(db, to_email=req.to_email, subject=req.subject, body=req.body)
    return {"id": row.id, "status": row.status}


@router.get("/pending", dependencies=[Depends(RoleChecker(["admin"]))])
def pending_emails(db: Session = Depends(get_db)):
    rows = emails_crud.get_pending_emails(db)
    return [{"id": r.id, "to": r.to_email, "subject": r.subject, "status": r.status} for r in rows]


@router.post("/retry/{email_id}", dependencies=[Depends(RoleChecker(["admin"]))])
def retry_email(email_id: int, db: Session = Depends(get_db)):
    row = emails_crud.get_email_by_id(db, email_id=email_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    # only retry if not already pending
    if row.status == "pending":
        return {"id": row.id, "status": row.status}
    if not is_retryable(row.status):
        # still allow setting to pending for MVP
        pass
    row = emails_crud.retry_email(db, email_id=email_id)
    return {"id": row.id, "status": row.status}
