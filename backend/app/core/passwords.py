import hashlib
import bcrypt

_MAX_BCRYPT_LENGTH = 72


def _normalize_password(password: str) -> bytes:
    data = password.encode("utf-8")
    if len(data) > _MAX_BCRYPT_LENGTH:
        # bcrypt only uses first 72 bytes; pre-hash to preserve entropy for long secrets
        return hashlib.sha256(data).digest()
    return data


def hash_password(password: str) -> str:
    candidate = _normalize_password(password)
    return bcrypt.hashpw(candidate, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    candidate = _normalize_password(password)
    try:
        return bcrypt.checkpw(candidate, password_hash.encode("utf-8"))
    except ValueError:
        return False
