from typing import Optional, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, asc

from ..db.session import get_db
from ..db import models
from ..core.security import RoleChecker


router = APIRouter()


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        # Accept both with and without timezone
        return datetime.fromisoformat(value)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {value}")


@router.get("/", dependencies=[Depends(RoleChecker(["admin"]))])
def list_events(
    db: Session = Depends(get_db),
    entity: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    event: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="ISO datetime inclusive"),
    date_to: Optional[str] = Query(None, description="ISO datetime inclusive"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    conditions = []
    if entity:
        conditions.append(models.EventAudit.entity == entity)
    if entity_id is not None:
        conditions.append(models.EventAudit.entity_id == entity_id)
    if event:
        conditions.append(models.EventAudit.event == event)
    dt_from = _parse_dt(date_from)
    dt_to = _parse_dt(date_to)
    if dt_from:
        conditions.append(models.EventAudit.created_at >= dt_from)
    if dt_to:
        conditions.append(models.EventAudit.created_at <= dt_to)

    stmt = select(models.EventAudit)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(desc(models.EventAudit.created_at) if order == "desc" else asc(models.EventAudit.created_at))
    stmt = stmt.offset(offset).limit(limit)

    rows = list(db.execute(stmt).scalars())
    return [
        {
            "id": r.id,
            "entity": r.entity,
            "entity_id": r.entity_id,
            "event": r.event,
            "payload": r.payload,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/export", dependencies=[Depends(RoleChecker(["admin"]))])
def export_events(
    db: Session = Depends(get_db),
    entity: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    event: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    # Reuse filtering without pagination; cap maximum rows implicitly by time window
    conditions = []
    if entity:
        conditions.append(models.EventAudit.entity == entity)
    if entity_id is not None:
        conditions.append(models.EventAudit.entity_id == entity_id)
    if event:
        conditions.append(models.EventAudit.event == event)
    dt_from = _parse_dt(date_from)
    dt_to = _parse_dt(date_to)
    if dt_from:
        conditions.append(models.EventAudit.created_at >= dt_from)
    if dt_to:
        conditions.append(models.EventAudit.created_at <= dt_to)

    stmt = select(models.EventAudit)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(desc(models.EventAudit.created_at) if order == "desc" else asc(models.EventAudit.created_at))

    rows = list(db.execute(stmt).scalars())

    # Build CSV
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "entity", "entity_id", "event", "created_at", "payload"])
    for r in rows:
        writer.writerow([
            r.id,
            r.entity,
            r.entity_id,
            r.event,
            r.created_at.isoformat(),
            (str(r.payload) if r.payload is not None else ""),
        ])
    data = buf.getvalue()
    return Response(content=data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=events.csv"})

