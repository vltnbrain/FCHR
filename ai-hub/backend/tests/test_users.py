import os
import sys
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient


def make_client():
    # Use a local SQLite DB for tests to avoid requiring Postgres
    os.environ["DATABASE_URI"] = "sqlite+aiosqlite:///./test_aihub.db"
    os.environ.pop("OPENAI_API_KEY", None)

    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    # Ensure the 'app' package resolves correctly
    import types
    pkg = types.ModuleType('app')
    pkg.__path__ = [str(backend_root / 'app')]
    sys.modules['app'] = pkg

    # Load FastAPI app from app.py
    app_py = backend_root / "app.py"
    spec = importlib.util.spec_from_file_location("app_main", app_py)
    module = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore
    return TestClient(module.app)


def test_users_crud_flow():
    with make_client() as client:
        # Create analyst (admin permission required)
        payload_analyst = {
            "full_name": "Analyst One",
            "email": "analyst.one@example.com",
            "role": "analyst",
            "department": "product"
        }
        r = client.post("/api/v1/users/", json=payload_analyst, headers={"x-user-role": "admin"})
        assert r.status_code == 200, r.text
        analyst = r.json()
        assert analyst["role"] == "analyst"

        # Create finance
        payload_finance = {
            "full_name": "Finance One",
            "email": "finance.one@example.com",
            "role": "finance",
            "department": "finance"
        }
        r = client.post("/api/v1/users/", json=payload_finance, headers={"x-user-role": "manager"})
        assert r.status_code == 200, r.text
        finance = r.json()
        assert finance["role"] == "finance"

        # List only analysts
        r = client.get("/api/v1/users/?role=analyst&limit=5")
        assert r.status_code == 200
        data = r.json()
        assert any(u["email"] == "analyst.one@example.com" for u in data["items"])  # includes created analyst

        # Get by id
        r = client.get(f"/api/v1/users/{finance['id']}")
        assert r.status_code == 200
        assert r.json()["email"] == "finance.one@example.com"

