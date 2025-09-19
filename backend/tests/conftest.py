import os
import uuid
import tempfile
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def client():
    db_path = os.path.join(tempfile.gettempdir(), f"pytest_{uuid.uuid4().hex}.db")
    os.environ['DATABASE_URL'] = f'sqlite+pysqlite:///{db_path}'
    os.environ['USE_PGVECTOR'] = '0'
    os.environ['EMAIL_PROVIDER'] = 'mock'
    os.environ['PYTHONHASHSEED'] = '0'
    import importlib
    # Reset settings cache and reload DB/session + app
    try:
        cfg = importlib.import_module('app.core.config')
        if hasattr(cfg, 'get_settings') and hasattr(cfg.get_settings, 'cache_clear'):
            cfg.get_settings.cache_clear()
    except Exception:
        pass
    if 'app.db.session' in importlib.sys.modules:
        importlib.reload(importlib.import_module('app.db.session'))
    if 'app.main' in importlib.sys.modules:
        importlib.reload(importlib.import_module('app.main'))
    from app.main import app
    with TestClient(app) as c:
        yield c
