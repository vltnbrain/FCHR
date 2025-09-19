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
from ..db import models


router = APIRouter()


def _normalize_email(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    try:
        from email_validator import validate_email, EmailNotValidError
        v = validate_email(email, check_deliverability=False)
        return v.normalized
    except Exception:
        return email.strip().lower()


def _normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    try:
        import phonenumbers
        num = phonenumbers.parse(phone, None)
        if phonenumbers.is_valid_number(num):
            return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    # Fallback: digits only prefixed
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if not digits:
        return None
    if not digits.startswith('+' ):
        digits = '+' + digits
    return digits


def _record_usage_and_check_quota(db: Session, api_key: str):
    # record usage
    row = models.VoiceUsage(api_key=api_key)
    db.add(row)
    db.commit()
    # quotas
    from datetime import datetime, timedelta
    qpm = int(os.getenv('VOICE_QUOTA_PER_MINUTE', '60') or 60)
    qpd = int(os.getenv('VOICE_QUOTA_PER_DAY', '5000') or 5000)
    now = datetime.utcnow()
    min_cut = now - timedelta(minutes=1)
    day_cut = now - timedelta(days=1)
    per_min = db.query(models.VoiceUsage).filter(models.VoiceUsage.api_key==api_key, models.VoiceUsage.created_at >= min_cut).count()
    per_day = db.query(models.VoiceUsage).filter(models.VoiceUsage.api_key==api_key, models.VoiceUsage.created_at >= day_cut).count()
    if per_min > qpm or per_day > qpd:
        raise HTTPException(status_code=429, detail="Voice API quota exceeded")


def require_voice_key(x_voice_api_key: Optional[str] = Header(None), db: Session = Depends(get_db)):
    key = os.getenv("VOICE_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="Voice API key not configured")
    if x_voice_api_key != key:
        raise HTTPException(status_code=401, detail="Invalid voice API key")
    # quota accounting
    _record_usage_and_check_quota(db, x_voice_api_key)


class IdentifyRequest(BaseModel):
    external_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    session_id: Optional[int] = None


class IdentifyResponse(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: str
    session_id: int


@router.post("/identify", response_model=IdentifyResponse, dependencies=[Depends(require_voice_key)])
def identify(req: IdentifyRequest, db: Session = Depends(get_db)):
    if not req.email and not req.phone and not req.external_id:
        raise HTTPException(status_code=400, detail="Provide at least one of email/phone/external_id")
    # For MVP we use email as primary; if missing, synthesize pseudo-email from external_id/phone
    email = _normalize_email(req.email)
    phone = _normalize_phone(req.phone)
    if not email:
        email = (f"{req.external_id}@voice.local" if req.external_id else None) or (f"{(phone or '').replace('+','') }@voice.local" if phone else None)
    if not email:
        raise HTTPException(status_code=400, detail="Cannot resolve user identity")
    user = get_user_by_email(db, email)
    if not user:
        user = create_user(db, email=email, password_hash="", full_name=req.full_name or None)
    # ensure session
    session_id = req.session_id or None
    if session_id:
        sess = db.get(models.VoiceSession, session_id)
        if not sess:
            session_id = None
    if not session_id:
        sess = models.VoiceSession(api_key=os.getenv('VOICE_API_KEY',''), user_email=user.email, context={})
        db.add(sess)
        db.commit()
        db.refresh(sess)
        session_id = sess.id
    try:
        events_crud.record_event(db, entity="voice_session", entity_id=session_id, event="identify", payload={"email": user.email})
    except Exception:
        pass
    return IdentifyResponse(email=user.email, full_name=user.full_name, role=user.role, session_id=session_id)


class VoiceIdeaRequest(BaseModel):
    email: str
    title: Optional[str] = None
    description: Optional[str] = None
    raw: Optional[str] = None
    session_id: Optional[int] = None


class DuplicateCandidate(BaseModel):
    idea_id: int
    score: float


class VoiceIdeaResponse(BaseModel):
    response: str
    idea_id: int
    possible_duplicates: List[DuplicateCandidate] = []
    need: List[str] = []
    session_id: Optional[int] = None


@router.post("/create-idea", response_model=VoiceIdeaResponse, dependencies=[Depends(require_voice_key)])
def voice_create_idea(req: VoiceIdeaRequest, db: Session = Depends(get_db)):
    # resolve user
    user = get_user_by_email(db, req.email)
    if not user:
        user = create_user(db, email=req.email, password_hash="")
    # session
    sess = None
    if req.session_id:
        sess = db.get(models.VoiceSession, req.session_id)
    if not sess:
        sess = models.VoiceSession(api_key=os.getenv('VOICE_API_KEY',''), user_email=req.email, context={})
        db.add(sess)
        db.commit()
        db.refresh(sess)

    title = req.title
    desc = req.description
    if (not title or not desc) and req.raw:
        text = req.raw.strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if lines:
            title = title or (lines[0][:120] if lines[0] else "Untitled Idea")
            rest = "\n".join(lines[1:]) if len(lines) > 1 else (desc or text)
            desc = desc or (rest if rest else text)
    need = []
    if not title:
        need.append('title')
    if not desc:
        need.append('description')
    if need:
        # store pending fields in session context
        sess.context = {**(sess.context or {}), 'pending': {'title': title, 'description': desc}}
        sess.last_response = f"Need: {', '.join(need)}"
        db.add(sess)
        db.commit()
        try:
            events_crud.record_event(db, entity="voice_session", entity_id=sess.id, event="clarify", payload={'need': need})
        except Exception:
            pass
        return VoiceIdeaResponse(response=sess.last_response, idea_id=0, possible_duplicates=[], need=need, session_id=sess.id)

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

    dupes_sentence = ""
    if dupes_raw:
        parts = [f"#{d['idea_id']} ({d['score']:.2f})" for d in dupes_raw]
        dupes_sentence = " Possible duplicates: " + ", ".join(parts)
    response_text = f"Idea #{row.id} created. Current status: {getattr(row,'status', 'submitted')}." + dupes_sentence
    # update session
    try:
        sess.last_response = response_text
        sess.context = {**(sess.context or {}), 'last_idea_id': row.id}
        db.add(sess)
        db.commit()
    except Exception:
        pass
    return VoiceIdeaResponse(
        response=response_text,
        idea_id=row.id,
        possible_duplicates=[DuplicateCandidate(**d) for d in dupes_raw],
        need=[],
        session_id=sess.id if sess else None,
    )


class VoiceStatusRequest(BaseModel):
    email: str
    idea_id: Optional[int] = None
    session_id: Optional[int] = None


class VoiceStatusResponse(BaseModel):
    response: str
    idea_id: Optional[int] = None
    status: Optional[str] = None
    session_id: Optional[int] = None


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
        sid = req.session_id
        try:
            events_crud.record_event(db, entity="voice_session", entity_id=(sid or 0), event="status_none", payload={'email': req.email})
        except Exception:
            pass
        return VoiceStatusResponse(response="No ideas found for this user.", session_id=sid)

    status = getattr(idea, 'status', None) or "submitted"
    sid = req.session_id
    try:
        events_crud.record_event(db, entity="voice_session", entity_id=(sid or 0), event="status", payload={'idea_id': idea.id, 'status': status})
    except Exception:
        pass
    return VoiceStatusResponse(response=f"Idea #{idea.id} status is {status}.", idea_id=idea.id, status=status, session_id=sid)


class VoiceRepeatRequest(BaseModel):
    session_id: int


class VoiceRepeatResponse(BaseModel):
    response: str
    session_id: int


@router.post("/repeat", response_model=VoiceRepeatResponse, dependencies=[Depends(require_voice_key)])
def voice_repeat(req: VoiceRepeatRequest, db: Session = Depends(get_db)):
    sess = db.get(models.VoiceSession, req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    resp = sess.last_response or "No previous response."
    try:
        events_crud.record_event(db, entity="voice_session", entity_id=sess.id, event="repeat", payload={})
    except Exception:
        pass
    return VoiceRepeatResponse(response=resp, session_id=sess.id)
