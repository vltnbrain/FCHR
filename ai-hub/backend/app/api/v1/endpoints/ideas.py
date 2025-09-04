"""
Ideas API endpoints for AI Hub
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.session import get_db
from app.models import Idea, User, IdeaStatus
from app.schemas.idea import (
    IdeaCreate, IdeaResponse, IdeaUpdate,
    IdeaListResponse, DuplicateCheckResponse
)
from app.services import IdeaService, EmbeddingService, AuditService
from app.core.config import settings
from app.core.security import require_roles

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/", response_model=IdeaResponse)
async def create_idea(
    idea_data: IdeaCreate,
    db: AsyncSession = Depends(get_db),
) -> IdeaResponse:
    """
    Create a new idea with automatic structuring and duplicate detection
    """
    try:
        # Resolve or create user
        user = await IdeaService.resolve_user(
            db, idea_data.user_name, idea_data.user_email,
            idea_data.user_role, idea_data.user_department
        )

        # Create the idea
        idea = await IdeaService.create_idea(db, idea_data, user.id)

        # Generate embedding for duplicate detection
        if settings.OPENAI_API_KEY:
            embedding_service = EmbeddingService()
            await embedding_service.generate_embedding(db, idea.id, "idea", idea.raw_input)

            # Check for duplicates
            duplicates = await embedding_service.find_duplicates(db, idea.id)
            if duplicates:
                await IdeaService.mark_potential_duplicate(db, idea.id, duplicates[0])

        # Log audit event
        await AuditService.log_event(
            db, "idea", idea.id, "created", user.id,
            {"raw_input": idea.raw_input[:100]}
        )

        # Route to analyst if no duplicates found
        if idea.status == IdeaStatus.NEW:
            await IdeaService.route_to_analyst(db, idea.id)

        return IdeaResponse.from_orm(idea)

    except Exception as e:
        logger.error("Failed to create idea", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create idea")


@router.get("/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: int,
    db: AsyncSession = Depends(get_db),
) -> IdeaResponse:
    """
    Get detailed information about a specific idea
    """
    idea = await IdeaService.get_idea_with_details(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    return IdeaResponse.from_orm(idea)


@router.get("/", response_model=IdeaListResponse)
async def list_ideas(
    status: Optional[str] = Query(None, description="Filter by status"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
) -> IdeaListResponse:
    """
    List ideas with optional filtering and pagination
    """
    ideas, total = await IdeaService.list_ideas(
        db, status=status, author_id=author_id,
        category=category, skip=skip, limit=limit
    )

    return IdeaListResponse(
        items=[IdeaResponse.from_orm(idea) for idea in ideas],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/{idea_id}/route/analyst", dependencies=[Depends(require_roles(["analyst", "manager", "admin"]))])
async def route_to_analyst(
    idea_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Manually route idea to analyst review
    """
    success = await IdeaService.route_to_analyst(db, idea_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to route idea to analyst")

    return {"message": "Idea routed to analyst successfully"}


@router.post("/{idea_id}/route/finance", dependencies=[Depends(require_roles(["finance", "manager", "admin"]))])
async def route_to_finance(
    idea_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Manually route idea to finance review
    """
    success = await IdeaService.route_to_finance(db, idea_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to route idea to finance")

    return {"message": "Idea routed to finance successfully"}


@router.post("/{idea_id}/route/developers", dependencies=[Depends(require_roles(["manager", "admin"]))])
async def route_to_developers(
    idea_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Route idea to developer assignment
    """
    success = await IdeaService.route_to_developers(db, idea_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to route idea to developers")

    return {"message": "Idea routed to developers successfully"}


@router.get("/{idea_id}/duplicates", response_model=List[DuplicateCheckResponse])
async def check_duplicates(
    idea_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[DuplicateCheckResponse]:
    """
    Check for duplicate ideas
    """
    if not settings.OPENAI_API_KEY:
        return []

    embedding_service = EmbeddingService()
    duplicates = await embedding_service.find_duplicates(db, idea_id)

    return [
        DuplicateCheckResponse(
            idea_id=dup["idea_id"],
            title=dup["title"],
            similarity_score=dup["similarity_score"],
            status=dup["status"]
        )
        for dup in duplicates
    ]


@router.get("/{idea_id}/history")
async def get_idea_history(
    idea_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get complete audit history for an idea
    """
    history = await AuditService.get_entity_history(db, "idea", idea_id)
    return {"history": history}
