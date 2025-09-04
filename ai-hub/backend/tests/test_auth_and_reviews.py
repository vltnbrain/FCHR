import os
import sys
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient


def make_client():
    os.environ["DATABASE_URI"] = "sqlite+aiosqlite:///./test_aihub.db"
    from uuid import uuid4
    os.environ["DATABASE_URI"] = f"sqlite+aiosqlite:///./test_aihub_{uuid4().hex}.db"
    os.environ.pop("OPENAI_API_KEY", None)

    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    import types
    pkg = types.ModuleType('app')
    pkg.__path__ = [str(backend_root / 'app')]
    sys.modules['app'] = pkg

    app_py = backend_root / "app.py"
    spec = importlib.util.spec_from_file_location("app_main", app_py)
    module = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore
    return TestClient(module.app)


def issue_token(client: TestClient, email: str, role: str, name: str = "Test User") -> str:
    r = client.post("/api/v1/auth/token", json={
        "email": email,
        "role": role,
        "full_name": name,
        "department": "engineering"
    })
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_reviews_flow():
    with make_client() as client:
        # Issue tokens for roles
        admin_token = issue_token(client, "admin@example.com", "admin", name="Admin")
        analyst_token = issue_token(client, "analyst@example.com", "analyst", name="Analyst")
        finance_token = issue_token(client, "finance@example.com", "finance", name="Finance")

        # Create idea (public)
        r = client.post("/api/v1/ideas/", json={
            "raw_input": "Add export to CSV feature",
            "user_name": "Alice",
            "user_email": "alice@example.com",
            "user_role": "developer",
            "user_department": "engineering",
        })
        assert r.status_code == 200, r.text
        idea_id = r.json()["id"]

        # Analyst accepts -> status moves to finance_review
        r = client.post("/api/v1/reviews/", json={
            "idea_id": idea_id,
            "stage": "analyst",
            "decision": "accepted",
            "notes": "Unique enough",
            "recommended_department": "engineering"
        }, headers=bearer(analyst_token))
        assert r.status_code == 200, r.text

        # Finance accepts -> status moves to developer_assignment
        r = client.post("/api/v1/reviews/", json={
            "idea_id": idea_id,
            "stage": "finance",
            "decision": "accepted",
            "notes": "Budget approved"
        }, headers=bearer(finance_token))
        assert r.status_code == 200, r.text

        # Dashboard minimal check
        r = client.get("/api/v1/dashboard/")
        assert r.status_code == 200
        assert "counts" in r.json()
