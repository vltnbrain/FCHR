from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..crud import reviews as reviews_crud
from ..crud import events as events_crud
from ..crud import emails as emails_crud


def review_sla_pass(db: Session, *, days: int = 5) -> int:
    count = 0
    overdue = reviews_crud.overdue_reviews(db, older_than_days=days)
    if overdue:
        admins = db.execute(text("SELECT email FROM users WHERE role='admin' LIMIT 5")).all()
        admin_emails = [row[0] for row in admins] or ["admin@example.com"]
        from ..services.email import render_template
        for r in overdue:
            if events_crud.has_event(db, entity="review", entity_id=r.id, event="sla_escalated"):
                continue
            subj, body = render_template("review.sla_overdue", review_id=r.id, stage=r.stage, idea_id=r.idea_id)
            for em in admin_emails:
                emails_crud.queue_email(db, to_email=em, subject=subj, body=body)
            events_crud.record_event(db, entity="review", entity_id=r.id, event="sla_escalated", payload={"idea_id": r.idea_id, "stage": r.stage})
            count += 1
    return count


def assignment_sla_pass(db: Session, *, days: int = 5) -> int:
    from ..crud import assignments as asg_crud
    from ..db import models
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    # Generic query across DBs
    overdue = db.query(models.Assignment).filter(models.Assignment.status == 'invited', models.Assignment.created_at < cutoff).all()
    from ..services.email import render_template
    admins = db.execute(text("SELECT email FROM users WHERE role='admin' LIMIT 5")).all()
    admin_emails = [row[0] for row in admins] or ["admin@example.com"]
    count = 0
    for a in overdue:
        if events_crud.has_event(db, entity="assignment", entity_id=a.id, event="sla_escalated"):
            continue
        try:
            row = asg_crud.escalate(db, assignment_id=a.id)
        except Exception:
            continue
        subj, body = render_template("assignment.escalated", assignment_id=row.id, idea_id=row.idea_id)
        for em in admin_emails:
            emails_crud.queue_email(db, to_email=em, subject=subj, body=body)
        events_crud.record_event(db, entity="assignment", entity_id=row.id, event="sla_escalated", payload={"idea_id": row.idea_id})
        count += 1
    return count
