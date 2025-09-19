from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
import os
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..crud.users import get_user_by_email, create_user
from ..crud import ideas as ideas_crud
from ..crud import embeddings as emb_crud
from ..services.embeddings import generate_embedding
from ..crud import events as events_crud


router = APIRouter()


def require_voice_key(x_voice_api_key: Optional[str] = Header(None)):
    key = os.getenv("VOICE_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="Voice API key not configured")
    if x_voice_api_key != key:
        raise HTTPException(status_code=401, detail="Invalid voice API key")


class IdentifyRequest(BaseModel):
    external_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None


class IdentifyResponse(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: str


@router.post("/identify", response_model=IdentifyResponse, dependencies=[Depends(require_voice_key)])
def identify(req: IdentifyRequest, db: Session = Depends(get_db)):
    if not req.email and not req.phone and not req.external_id:
        raise HTTPException(status_code=400, detail="Provide at least one of email/phone/external_id")
    # For MVP we use email as primary; if missing, synthesize pseudo-email from external_id/phone
    email = (req.email or (f"{req.external_id}@voice.local" if req.external_id else None) or (f"{req.phone}@voice.local" if req.phone else None))
    if not email:
        raise HTTPException(status_code=400, detail="Cannot resolve user identity")
    user = get_user_by_email(db, email)
    if not user:
        user = create_user(db, email=email, password_hash="", full_name=req.full_name or None)
    return IdentifyResponse(email=user.email, full_name=user.full_name, role=user.role)


class VoiceIdeaRequest(BaseModel):
    email: str
    title: Optional[str] = None
    description: Optional[str] = None
    raw: Optional[str] = None


class DuplicateCandidate(BaseModel):
    idea_id: int
    score: float


class VoiceIdeaResponse(BaseModel):
    response: str
    idea_id: int
    possible_duplicates: List[DuplicateCandidate] = []


@router.post("/create-idea", response_model=VoiceIdeaResponse, dependencies=[Depends(require_voice_key)])
def voice_create_idea(req: VoiceIdeaRequest, db: Session = Depends(get_db)):
    # resolve user
    user = get_user_by_email(db, req.email)
    if not user:
        user = create_user(db, email=req.email, password_hash="")

    title = req.title
    desc = req.description
    if (not title or not desc) and req.raw:
        text = req.raw.strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if lines:
            title = title or (lines[0][:120] if lines[0] else "Untitled Idea")
            rest = "\n".join(lines[1:]) if len(lines) > 1 else (desc or text)
            desc = desc or (rest if rest else text)
    if not title or not desc:
        raise HTTPException(status_code=400, detail="title/description or raw required")

    vec = generate_embedding(f"{title}\n{desc}")
    try:
        dupes_raw = emb_crud.find_similar(db, vector=vec, limit=5, min_score=0.9)
    except Exception:
        dupes_raw = []

    row = ideas_crud.create_idea(db, title=title, description=desc, author_email=req.email, created_by_id=user.id)
    try:
        emb_crud.add_embedding(db, idea_id=row.id, vector=vec)
    except Exception:
        pass
    try:
        events_crud.record_event(db, entity="idea", entity_id=row.id, event="created_voice", payload={"user": req.email})
    except Exception:
        pass

    response_text = f"Idea #{row.id} created. Current status: {getattr(row,'status', 'submitted')}"
    return VoiceIdeaResponse(
        response=response_text,
        idea_id=row.id,
        possible_duplicates=[DuplicateCandidate(**d) for d in dupes_raw],
    )


class VoiceStatusRequest(BaseModel):
    email: str
    idea_id: Optional[int] = None


class VoiceStatusResponse(BaseModel):
    response: str
    idea_id: Optional[int] = None
    status: Optional[str] = None


@router.post("/get-status", response_model=VoiceStatusResponse, dependencies=[Depends(require_voice_key)])
def voice_get_status(req: VoiceStatusRequest, db: Session = Depends(get_db)):
    # fetch idea by id (and optionally verify ownership via email)
    from sqlalchemy import select
    from ..db import models

    idea = None
    if req.idea_id is not None:
        idea = db.get(models.Idea, req.idea_id)
        if idea and req.email and idea.author_email and idea.author_email != req.email:
            # do not disclose other users' ideas
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        # pick most recent idea by this email
        res = db.execute(
            select(models.Idea).where(models.Idea.author_email == req.email).order_by(models.Idea.id.desc()).limit(1)
        ).scalars().first()
        idea = res

    if not idea:
        return VoiceStatusResponse(response="No ideas found for this user.")

    status = getattr(idea, 'status', None) or "submitted"
    return VoiceStatusResponse(response=f"Idea #{idea.id} status is {status}.", idea_id=idea.id, status=status)

