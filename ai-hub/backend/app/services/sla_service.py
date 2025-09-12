"""
SLA service: scans for overdue stages and queues escalation emails.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from app.core.config import settings
from app.models import Idea, IdeaStatus, Assignment, User, UserRole, MarketplaceEntry
from app.services.email_service import EmailService


class SLAService:
    @staticmethod
    async def check(db: AsyncSession) -> Dict[str, int]:
        now = datetime.now(timezone.utc)

        # Analyst overdue
        analyst_cutoff = now - timedelta(days=settings.SLA_ANALYST_DAYS)
        analyst_overdue = (await db.execute(select(Idea).where(
            and_(Idea.status == IdeaStatus.ANALYST_REVIEW, Idea.created_at < analyst_cutoff)
        ))).scalars().all()

        # Finance overdue
        finance_cutoff = now - timedelta(days=settings.SLA_FINANCE_DAYS)
        finance_overdue = (await db.execute(select(Idea).where(
            and_(Idea.status == IdeaStatus.FINANCE_REVIEW, Idea.updated_at < finance_cutoff)
        ))).scalars().all()

        # Developer response overdue
        dev_cutoff = now - timedelta(days=settings.SLA_DEVELOPER_DAYS)
        dev_overdue = (await db.execute(select(Assignment).where(
            and_(Assignment.status == "invited", Assignment.invited_at < dev_cutoff)
        ))).scalars().all()

        # Mark overdue invites as no_response and ensure Marketplace entries
        ideas_listed: set[int] = set()
        for a in dev_overdue:
            # Update assignment status if still invited
            a.status = "no_response"
            if a.idea_id is not None:
                ideas_listed.add(a.idea_id)

        if dev_overdue:
            # Create marketplace entries for affected ideas (idempotent via unique constraint)
            for idea_id in ideas_listed:
                existing = (await db.execute(select(MarketplaceEntry).where(MarketplaceEntry.idea_id == idea_id))).scalar_one_or_none()
                if not existing:
                    entry = MarketplaceEntry(idea_id=idea_id, listed_at=now)
                    db.add(entry)

            await db.commit()

        # Notify admins for each category (single summary email)
        admins = (await db.execute(select(User).where(User.role == UserRole.ADMIN))).scalars().all()
        if admins and (analyst_overdue or finance_overdue or dev_overdue):
            admin_email = admins[0].email
            body = (
                f"Analyst overdue: {len(analyst_overdue)}\n"
                f"Finance overdue: {len(finance_overdue)}\n"
                f"Developer response overdue: {len(dev_overdue)}\n"
            )
            await EmailService.queue_email(db, admin_email, "AI Hub SLA Summary", body)

        return {
            "analyst_overdue": len(analyst_overdue),
            "finance_overdue": len(finance_overdue),
            "developer_overdue": len(dev_overdue),
        }
