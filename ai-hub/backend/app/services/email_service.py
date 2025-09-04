"""
Email service for notifications and communications
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models import EmailQueue, User, Idea
from app.core.config import settings

logger = structlog.get_logger(__name__)


class EmailService:
    """Service for handling email notifications"""

    @staticmethod
    async def queue_email(
        db: AsyncSession,
        to_email: str,
        subject: str,
        body: str,
        priority: str = "normal"
    ) -> int:
        """Queue an email for sending"""
        email = EmailQueue(
            to_email=to_email,
            subject=subject,
            body=body,
            status="pending"
        )

        db.add(email)
        await db.commit()
        await db.refresh(email)

        logger.info("Queued email", email_id=email.id, to_email=to_email, subject=subject)
        return email.id

    @staticmethod
    async def queue_analyst_review_email(db: AsyncSession, idea_id: int) -> None:
        """Queue email to analyst for review"""
        # Get idea details
        from app.services.idea_service import IdeaService
        idea = await IdeaService.get_idea_with_details(db, idea_id)
        if not idea:
            return

        # Find analysts
        from sqlalchemy import select
        from app.models import User, UserRole

        query = select(User).where(
            User.role == UserRole.ANALYST,
            User.email.isnot(None)
        )
        result = await db.execute(query)
        analysts = result.scalars().all()

        if not analysts:
            logger.warning("No analysts found for email notification")
            return

        # Send to first analyst (could be load balanced)
        analyst = analysts[0]

        subject = f"AI Hub: New Idea Review Required - {idea.title}"
        body = f"""
Dear {analyst.full_name},

A new idea has been submitted to the AI Hub that requires your review:

Title: {idea.title}
Submitted by: {idea.author.full_name if idea.author else 'Unknown'}
Submitted: {idea.created_at.strftime('%Y-%m-%d %H:%M UTC')}

Raw Input:
{idea.raw_input}

Please assess whether this idea has >50% uniqueness compared to existing ideas.
If unique, mark as NEW and recommend the appropriate department.
If not unique, mark as IMPROVEMENT and link to the similar existing idea.

Review Link: {settings.SERVER_HOST}/review/analyst/{idea_id}

You have 5 days to complete this review.

Best regards,
AI Hub System
        """.strip()

        await EmailService.queue_email(db, analyst.email, subject, body)

    @staticmethod
    async def queue_finance_review_email(db: AsyncSession, idea_id: int) -> None:
        """Queue email to finance for review"""
        # Get idea details
        from app.services.idea_service import IdeaService
        idea = await IdeaService.get_idea_with_details(db, idea_id)
        if not idea:
            return

        # Find finance users
        from sqlalchemy import select
        from app.models import User, UserRole

        query = select(User).where(
            User.role == UserRole.FINANCE,
            User.email.isnot(None)
        )
        result = await db.execute(query)
        finance_users = result.scalars().all()

        if not finance_users:
            logger.warning("No finance users found for email notification")
            return

        # Send to first finance user
        finance_user = finance_users[0]

        subject = f"AI Hub: Finance Review Required - {idea.title}"
        body = f"""
Dear {finance_user.full_name},

An idea has passed analyst review and requires your finance assessment:

Title: {idea.title}
Submitted by: {idea.author.full_name if idea.author else 'Unknown'}
Analyst Decision: {idea.reviews[0].decision if idea.reviews else 'Unknown'}

Raw Input:
{idea.raw_input}

Please assess the financial viability and confirm/adjust the recommended department.

Review Link: {settings.SERVER_HOST}/review/finance/{idea_id}

You have 5 days to complete this review.

Best regards,
AI Hub System
        """.strip()

        await EmailService.queue_email(db, finance_user.email, subject, body)

    @staticmethod
    async def queue_developer_invitation_email(
        db: AsyncSession,
        idea_id: int,
        developer_id: int
    ) -> None:
        """Queue email to developer for assignment"""
        # Get idea and developer details
        from app.services.idea_service import IdeaService
        from sqlalchemy import select
        from app.models import User

        idea = await IdeaService.get_idea_with_details(db, idea_id)
        query = select(User).where(User.id == developer_id)
        result = await db.execute(query)
        developer = result.scalar_one_or_none()

        if not idea or not developer or not developer.email:
            return

        subject = f"AI Hub: Developer Assignment - {idea.title}"
        body = f"""
Dear {developer.full_name},

You have been invited to work on an idea in the AI Hub:

Title: {idea.title}
Submitted by: {idea.author.full_name if idea.author else 'Unknown'}

Raw Input:
{idea.raw_input}

Please accept or decline this assignment within 5 days.

Assignment Link: {settings.SERVER_HOST}/assignment/{idea_id}

Best regards,
AI Hub System
        """.strip()

        await EmailService.queue_email(db, developer.email, subject, body)

    @staticmethod
    async def send_queued_emails(db: AsyncSession) -> int:
        """Process queued emails (would be called by background worker)"""
        # This would integrate with actual email provider (SendGrid, SMTP, etc.)
        # For now, just mark as sent for demo purposes

        from sqlalchemy import select, update

        query = select(EmailQueue).where(EmailQueue.status == "pending").limit(10)
        result = await db.execute(query)
        emails = result.scalars().all()

        sent_count = 0
        for email in emails:
            # Here you would integrate with actual email service
            # For demo, just mark as sent
            email.status = "sent"
            sent_count += 1

        await db.commit()

        if sent_count > 0:
            logger.info("Processed queued emails", count=sent_count)

        return sent_count
