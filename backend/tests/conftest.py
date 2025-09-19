import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    os.environ.setdefault('DATABASE_URL', 'sqlite+pysqlite:///:memory:')
    os.environ.setdefault('USE_PGVECTOR', '0')
    os.environ.setdefault('EMAIL_PROVIDER', 'mock')
    os.environ.setdefault('PYTHONHASHSEED', '0')
    import app.main as main
    with TestClient(main.app) as c:
        yield c

