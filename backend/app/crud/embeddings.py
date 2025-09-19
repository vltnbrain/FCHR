from sqlalchemy.orm import Session
from sqlalchemy import select, text
from ..db import models


def add_embedding(db: Session, *, idea_id: int, vector: list[float]) -> models.Embedding:
    emb = models.Embedding(idea_id=idea_id, vector=vector)  # type: ignore[arg-type]
    db.add(emb)
    db.commit()
    db.refresh(emb)
    return emb


def get_all_embeddings(db: Session) -> list[tuple[int, list[float]]]:
    rows = db.execute(select(models.Embedding.id, models.Embedding.idea_id, models.Embedding.vector)).all()
    return [(row.idea_id, row.vector) for row in rows]  # type: ignore[return-value]


def find_similar(db: Session, *, vector: list[float], limit: int = 5, min_score: float = 0.85) -> list[dict]:
    # Use cosine distance operator; similarity = 1 - distance
    sql = text(
        """
        SELECT idea_id, 1 - (vector <=> :vec) AS score
        FROM embeddings
        ORDER BY vector <=> :vec
        LIMIT :limit
        """
    )
    rows = db.execute(sql, {"vec": vector, "limit": limit}).all()
    results = [{"idea_id": r[0], "score": float(r[1])} for r in rows]
    return [r for r in results if r["score"] >= min_score]
