"""
Dashboard API endpoints for AI Hub
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models import Idea, IdeaStatus
from app.services.audit_service import AuditService
from app.services.sla_service import SLAService

router = APIRouter()


@router.get("/")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Get dashboard data with ideas, stats, and SLA status"""
    counts = {}
    for st in [s for s in IdeaStatus]:
        total = (await db.execute(select(func.count()).where(Idea.status == st))).scalar() or 0
        counts[st.value] = total

    sla = await SLAService.check(db)
    latest = (await db.execute(select(Idea).order_by(Idea.created_at.desc()).limit(10))).scalars().all()
    latest_items = [
        {"id": i.id, "title": i.title, "status": i.status, "created_at": i.created_at.isoformat()}
        for i in latest
    ]
    return {"counts": counts, "sla": sla, "latest": latest_items}


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics"""
    total_ideas = (await db.execute(select(func.count()).select_from(Idea))).scalar() or 0
    return {"total_ideas": total_ideas}


@router.get("/recent-activity")
async def get_recent_activity(db: AsyncSession = Depends(get_db)):
    """Get recent system activity"""
    activity = await AuditService.get_recent_activity(db, limit=50)
    return {"items": activity}
