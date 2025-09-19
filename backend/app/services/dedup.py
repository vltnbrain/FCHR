from typing import Iterable, Tuple
from .embeddings import cosine_similarity


def find_duplicates(candidate_vec: list[float], existing: Iterable[Tuple[int, list[float]]], threshold: float = 0.9) -> list[int]:
    dupes: list[int] = []
    for idea_id, vec in existing:
        if not vec:
            continue
        if cosine_similarity(candidate_vec, vec) >= threshold:
            dupes.append(idea_id)
    return dupes

