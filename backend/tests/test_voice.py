import os


def test_voice_identify_and_create_and_status(client, monkeypatch):
    # Configure voice API key for tests
    monkeypatch.setenv('VOICE_API_KEY', 'test-key')
    H = {'X-VOICE-API-KEY': 'test-key'}

    # Identify user
    r = client.post('/voice/identify', headers=H, json={'email':'voice@test.local', 'full_name':'Voice User'})
    assert r.status_code == 200
    assert r.json()['email'] == 'voice@test.local'

    # Create idea via raw text
    r = client.post('/voice/create-idea', headers=H, json={'email':'voice@test.local', 'raw':'My Idea\nIt is great.'})
    assert r.status_code == 200
    data = r.json()
    assert data['idea_id'] > 0
    assert 'status' not in data or data['idea_id']

    # Get status for last idea
    r = client.post('/voice/get-status', headers=H, json={'email':'voice@test.local'})
    assert r.status_code == 200
    s = r.json()
    assert s['idea_id'] == data['idea_id']
    assert 'status' in s

def test_voice_unauthorized(client):
    r = client.post('/voice/identify', json={'email':'x@y'})
    assert r.status_code in (401, 500)

