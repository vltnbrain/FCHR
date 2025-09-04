import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import importlib.util


def make_client():
    # Ensure backend package is importable
    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    # Use a unique SQLite DB per test to avoid cross-test contamination
    from uuid import uuid4
    os.environ["DATABASE_URI"] = f"sqlite+aiosqlite:///./test_aihub_{uuid4().hex}.db"
    # Ensure OpenAI features are disabled during tests
    os.environ.pop("OPENAI_API_KEY", None)

    # Ensure the 'app' package resolves to the backend/app directory, not app.py
    import types
    pkg = types.ModuleType('app')
    pkg.__path__ = [str(backend_root / 'app')]  # make it a namespace-like package
    sys.modules['app'] = pkg

    # Load the FastAPI instance from app.py under a non-conflicting name
    app_py = backend_root / "app.py"
    spec = importlib.util.spec_from_file_location("app_main", app_py)
    module = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore
    return TestClient(module.app)


def test_health_and_idea_flow():
    with make_client() as client:
        # Health check
        r = client.get("/health")
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "healthy"

        # Create idea
        payload = {
            "raw_input": "Improve UI responsiveness by batching state updates.",
            "user_name": "Test User",
            "user_email": "test.user@example.com",
            "user_role": "developer",
            "user_department": "engineering",
        }
        r = client.post("/api/v1/ideas/", json=payload)
        assert r.status_code == 200, r.text
        idea = r.json()
        # The service auto-routes NEW ideas to analyst review
        assert idea["status"] in ("new", "analyst_review")
        idea_id = idea["id"]

        # Fetch idea by id
        r = client.get(f"/api/v1/ideas/{idea_id}")
        assert r.status_code == 200
        assert r.json()["id"] == idea_id

        # List ideas
        r = client.get("/api/v1/ideas/?skip=0&limit=10")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

        # Duplicate check should be empty without OpenAI API key
        r = client.get(f"/api/v1/ideas/{idea_id}/duplicates")
        assert r.status_code == 200
        assert r.json() == []

        # RBAC check: developer cannot route to finance, finance can
        r = client.post(f"/api/v1/ideas/{idea_id}/route/finance", headers={"x-user-role": "developer"})
        assert r.status_code == 403
        r = client.post(f"/api/v1/ideas/{idea_id}/route/finance", headers={"x-user-role": "finance"})
        assert r.status_code == 200
