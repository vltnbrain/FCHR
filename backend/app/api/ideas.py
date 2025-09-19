from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..crud import ideas as ideas_crud
from ..crud import embeddings as emb_crud
from ..services.embeddings import generate_embedding
from ..core.security import get_current_user
from ..crud import events as events_crud

router = APIRouter()


class IdeaCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    raw: Optional[str] = None
    author_email: Optional[str] = None

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("description", mode="before")
    @classmethod
    def normalize_desc(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class Idea(BaseModel):
    id: int
    title: str
    description: str
    author_email: Optional[str] = None
    status: Optional[str] = None


@router.get("/", response_model=List[Idea])
def list_ideas(db: Session = Depends(get_db)) -> List[Idea]:
    rows = ideas_crud.list_ideas(db)
    return [Idea(id=r.id, title=r.title, description=r.description, author_email=r.author_email, status=getattr(r, 'status', None)) for r in rows]


class DuplicateCandidate(BaseModel):
    idea_id: int
    score: float


class IdeaCreateResponse(BaseModel):
    idea: Idea
    possible_duplicates: List[DuplicateCandidate] = []


@router.post("/", response_model=IdeaCreateResponse, dependencies=[Depends(get_current_user)])
def create_idea(payload: IdeaCreate, db: Session = Depends(get_db), user = Depends(get_current_user)) -> IdeaCreateResponse:
    # Auto-structure if only raw provided
    title = payload.title
    description = payload.description
    if (not title or not description) and payload.raw:
        text = payload.raw.strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if lines:
            title = title or (lines[0][:120] if lines[0] else "Untitled Idea")
            rest = "\n".join(lines[1:]) if len(lines) > 1 else (description or text)
            description = description or (rest if rest else text)
    if not title or not description:
        raise HTTPException(status_code=400, detail="title/description or raw required")

    # Prepare embedding vector and find duplicates before insert
    vec = generate_embedding(f"{title}\n{description}")
    try:
        dupes = emb_crud.find_similar(db, vector=vec, limit=5, min_score=0.9)
    except Exception:
        dupes = []

    # Create idea
    row = ideas_crud.create_idea(
        db,
        title=title,
        description=description,
        author_email=payload.author_email,
        created_by_id=user.id,
    )
    idea = Idea(id=row.id, title=row.title, description=row.description, author_email=row.author_email, status=getattr(row, 'status', None))

    try:
        emb_crud.add_embedding(db, idea_id=row.id, vector=vec)
    except Exception:
        pass

    try:
        events_crud.record_event(db, entity="idea", entity_id=row.id, event="created", payload={"user": user.email})
    except Exception:
        pass

    return IdeaCreateResponse(
        idea=idea,
        possible_duplicates=[DuplicateCandidate(**d) for d in dupes],
    )
