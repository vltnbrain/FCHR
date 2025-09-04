"""
Idea service for business logic
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import structlog

from app.models import (
    Idea, User, IdeaStatus, UserRole, Department,
    Review, Assignment, MarketplaceEntry
)
from app.schemas.idea import IdeaCreate, IdeaUpdate
from app.services.email_service import EmailService

logger = structlog.get_logger(__name__)


class IdeaService:
    """Service class for idea-related business logic"""

    @staticmethod
    async def resolve_user(
        db: AsyncSession,
        user_name: str,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        user_department: Optional[str] = None
    ) -> User:
        """Resolve user by name/email or create new user"""
        # Try to find existing user
        query = select(User).where(User.full_name == user_name)
        if user_email:
            query = query.where(User.email == user_email)

        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            # Update last contact time
            user.last_contact_at = func.now()
            await db.commit()
            return user

        # Create new user
        role = UserRole(user_role) if user_role else UserRole.DEVELOPER
        department = Department(user_department) if user_department else Department.ENGINEERING

        new_user = User(
            full_name=user_name,
            email=user_email or f"{user_name.lower().replace(' ', '.')}@company.com",
            role=role,
            department=department
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info("Created new user", user_id=new_user.id, user_name=user_name)
        return new_user

    @staticmethod
    async def create_idea(db: AsyncSession, idea_data: IdeaCreate, author_id: int) -> Idea:
        """Create a new idea with basic structuring"""
        # Basic title extraction from raw input
        title = idea_data.raw_input[:100]
        if len(idea_data.raw_input) > 100:
            title = title.rsplit(' ', 1)[0] + "..."

        idea = Idea(
            title=title,
            raw_input=idea_data.raw_input,
            author_user_id=author_id,
            status=IdeaStatus.NEW
        )

        db.add(idea)
        await db.commit()
        await db.refresh(idea)

        logger.info("Created new idea", idea_id=idea.id, author_id=author_id)
        return idea

    @staticmethod
    async def get_idea_with_details(db: AsyncSession, idea_id: int) -> Optional[Idea]:
        """Get idea with related data"""
        query = select(Idea).where(Idea.id == idea_id)
        result = await db.execute(query)
        idea = result.scalar_one_or_none()

        if idea:
            # Load related data
            await db.refresh(idea, ["author", "reviews", "assignments"])

        return idea

    @staticmethod
    async def list_ideas(
        db: AsyncSession,
        status: Optional[str] = None,
        author_id: Optional[int] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Idea], int]:
        """List ideas with filtering and pagination"""
        query = select(Idea)

        # Apply filters
        if status:
            query = query.where(Idea.status == IdeaStatus(status))
        if author_id:
            query = query.where(Idea.author_user_id == author_id)
        if category:
            query = query.where(Idea.category == category)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(Idea.created_at.desc())

        result = await db.execute(query)
        ideas = result.scalars().all()

        return list(ideas), total

    @staticmethod
    async def mark_potential_duplicate(
        db: AsyncSession,
        idea_id: int,
        duplicate_info: dict
    ) -> None:
        """Mark idea as potential duplicate"""
        query = select(Idea).where(Idea.id == idea_id)
        result = await db.execute(query)
        idea = result.scalar_one_or_none()

        if idea:
            if duplicate_info["similarity_score"] >= 0.8:
                idea.status = IdeaStatus.DUPLICATE
                idea.similarity_parent_id = duplicate_info["idea_id"]
            else:
                idea.status = IdeaStatus.IMPROVEMENT
                idea.similarity_parent_id = duplicate_info["idea_id"]

            idea.similarity_score = duplicate_info["similarity_score"]
            await db.commit()

            logger.info(
                "Marked idea as potential duplicate",
                idea_id=idea_id,
                duplicate_id=duplicate_info["idea_id"],
                similarity_score=duplicate_info["similarity_score"]
            )

    @staticmethod
    async def route_to_analyst(db: AsyncSession, idea_id: int) -> bool:
        """Route idea to analyst review"""
        query = select(Idea).where(Idea.id == idea_id)
        result = await db.execute(query)
        idea = result.scalar_one_or_none()

        if not idea or idea.status != IdeaStatus.NEW:
            return False

        idea.status = IdeaStatus.ANALYST_REVIEW
        await db.commit()

        # Queue email to analyst
        await EmailService.queue_analyst_review_email(db, idea_id)

        logger.info("Routed idea to analyst", idea_id=idea_id)
        return True

    @staticmethod
    async def route_to_finance(db: AsyncSession, idea_id: int) -> bool:
        """Route idea to finance review"""
        query = select(Idea).where(Idea.id == idea_id)
        result = await db.execute(query)
        idea = result.scalar_one_or_none()

        if not idea or idea.status != IdeaStatus.ANALYST_REVIEW:
            return False

        idea.status = IdeaStatus.FINANCE_REVIEW
        await db.commit()

        # Queue email to finance
        await EmailService.queue_finance_review_email(db, idea_id)

        logger.info("Routed idea to finance", idea_id=idea_id)
        return True

    @staticmethod
    async def route_to_developers(db: AsyncSession, idea_id: int) -> bool:
        """Route idea to developer assignment"""
        query = select(Idea).where(Idea.id == idea_id)
        result = await db.execute(query)
        idea = result.scalar_one_or_none()

        if not idea or idea.status not in [IdeaStatus.ANALYST_REVIEW, IdeaStatus.FINANCE_REVIEW]:
            return False

        idea.status = IdeaStatus.DEVELOPER_ASSIGNMENT
        await db.commit()

        # Find and invite developers
        await IdeaService.invite_developers(db, idea_id)

        logger.info("Routed idea to developers", idea_id=idea_id)
        return True

    @staticmethod
    async def invite_developers(db: AsyncSession, idea_id: int) -> None:
        """Find and invite suitable developers"""
        # Find developers in the required team/department
        query = select(User).where(
            and_(
                User.role == UserRole.DEVELOPER,
                User.email.isnot(None)  # Must have email for notifications
            )
        )

        result = await db.execute(query)
        developers = result.scalars().all()

        for developer in developers[:3]:  # Invite up to 3 developers
            assignment = Assignment(
                idea_id=idea_id,
                developer_user_id=developer.id,
                status="invited",
                invited_at=func.now()
            )
            db.add(assignment)

            # Queue invitation email
            await EmailService.queue_developer_invitation_email(db, idea_id, developer.id)

        await db.commit()

        logger.info("Invited developers", idea_id=idea_id, developer_count=len(developers[:3]))
