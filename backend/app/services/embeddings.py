from typing import Sequence


def generate_embedding(text: str, dims: int = 1536) -> list[float]:
    # Stub embedding generator for scaffolding
    # Deterministic pseudo-vector based on simple hash
    import random
    random.seed(hash(text) % (2**32))
    return [random.uniform(-1, 1) for _ in range(dims)]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-9)
