import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault('DATABASE_URL', 'sqlite+pysqlite:///:memory:')
os.environ.setdefault('USE_PGVECTOR', '0')
os.environ.setdefault('EMAIL_PROVIDER', 'mock')

from fastapi.testclient import TestClient
from app.main import app

def assert_ok(resp, code=200):
    assert resp.status_code == code, f"Status {resp.status_code}: {resp.text}"
    return resp

def run():
    with TestClient(app) as client:
        _run_with_client(client)


def _run_with_client(client: TestClient):
    # Health
    assert_ok(client.get('/healthz'))

    # Register admin
    r = assert_ok(client.post('/auth/register', json={'email':'admin@example.com','password':'secret'}), 200)
    token_admin = r.json()['access_token']
    headers_admin = {'Authorization': f'Bearer {token_admin}'}

    # Create idea with raw
    payload = {'raw': 'New Idea Title\nThis is the idea description.'}
    r = assert_ok(client.post('/ideas/', json=payload, headers=headers_admin))
    idea = r.json()['idea']
    assert idea['title']
    idea_id = idea['id']

    # Request analyst review
    assert_ok(client.post('/reviews/request', json={'idea_id': idea_id, 'stage':'analyst'}, headers=headers_admin))

    # Pending analyst
    r = assert_ok(client.get('/reviews/pending?stage=analyst', headers=headers_admin))
    pend = r.json()
    assert any(p['idea_id']==idea_id for p in pend)

    # Create analyst user and assign role
    assert_ok(client.post('/auth/register', json={'email':'analyst@example.com','password':'secret'}))
    assert_ok(client.post('/users/assign-role', json={'email':'analyst@example.com','role':'analyst'}, headers=headers_admin))
    login_analyst = assert_ok(client.post('/auth/login', json={'email':'analyst@example.com','password':'secret'}))
    tok_an = login_analyst.json()['access_token']
    headers_an = {'Authorization': f'Bearer {tok_an}'}

    # Analyst approve
    assert_ok(client.post('/reviews/analyst/decision', json={'idea_id':idea_id,'decision':'approved'}, headers=headers_an))

    # Finance pending must appear
    r = assert_ok(client.get('/reviews/pending?stage=finance', headers=headers_admin))
    assert any(p['idea_id']==idea_id for p in r.json())

    # Create finance user and approve
    assert_ok(client.post('/auth/register', json={'email':'finance@example.com','password':'secret'}))
    assert_ok(client.post('/users/assign-role', json={'email':'finance@example.com','role':'finance'}, headers=headers_admin))
    login_fin = assert_ok(client.post('/auth/login', json={'email':'finance@example.com','password':'secret'}))
    tok_fin = login_fin.json()['access_token']
    headers_fin = {'Authorization': f'Bearer {tok_fin}'}
    assert_ok(client.post('/reviews/finance/decision', json={'idea_id':idea_id,'decision':'approved'}, headers=headers_fin))

    # Create dev user and role, then invite
    assert_ok(client.post('/auth/register', json={'email':'dev@example.com','password':'secret'}))
    assert_ok(client.post('/users/assign-role', json={'email':'dev@example.com','role':'developer'}, headers=headers_admin))
    login_dev = assert_ok(client.post('/auth/login', json={'email':'dev@example.com','password':'secret'}))
    tok_dev = login_dev.json()['access_token']
    headers_dev = {'Authorization': f'Bearer {tok_dev}'}
    assert_ok(client.post('/assignments/invite', json={'idea_id': idea_id, 'developer_email': 'dev@example.com'}, headers=headers_admin))

    # Developer sees pending assignments and accepts
    r = assert_ok(client.get('/assignments/pending', headers=headers_dev))
    assigns = r.json()
    assert assigns, 'No pending assignments for developer'
    aid = assigns[0]['id']
    assert_ok(client.post('/assignments/respond', json={'assignment_id': aid, 'response':'accept'}, headers=headers_dev))

    # Audit events list as admin
    r = assert_ok(client.get('/events?entity=idea&entity_id='+str(idea_id), headers=headers_admin))
    assert r.json(), 'No audit events for idea'

    print('OK: end-to-end flow passed')

if __name__ == '__main__':
    run()
