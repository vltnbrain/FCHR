import pytest


def test_auth_required_for_create_idea(client):
    r = client.post('/ideas/', json={'title':'x','description':'y'})
    assert r.status_code in (401, 403)


def test_rbac_assign_role_forbidden_for_non_admin(client):
    # register user (becomes admin if first); ensure we have at least two
    r = client.post('/auth/register', json={'email':'a@a','password':'password8'})
    assert r.status_code == 200
    # second user — not admin
    r2 = client.post('/auth/register', json={'email':'b@b','password':'password8'})
    assert r2.status_code == 200
    token_user = client.post('/auth/login', json={'email':'b@b','password':'password8'}).json()['access_token']
    HU = {'Authorization': f'Bearer {token_user}'}
    r = client.post('/users/assign-role', headers=HU, json={'email':'a@a','role':'analyst'})
    assert r.status_code == 403


def test_rbac_analyst_only_decision(client):
    # admin
    adm = client.post('/auth/register', json={'email':'adm@x','password':'password8'}).json()['access_token']
    HA = {'Authorization': f'Bearer {adm}'}
    # idea
    idea_id = client.post('/ideas/', headers=HA, json={'title':'t','description':'d'}).json()['idea']['id']
    client.post('/reviews/request', headers=HA, json={'idea_id':idea_id,'stage':'analyst'})
    # developer tries to decide
    client.post('/auth/register', json={'email':'dev@x','password':'password8'})
    client.post('/users/assign-role', headers=HA, json={'email':'dev@x','role':'developer'})
    tok = client.post('/auth/login', json={'email':'dev@x','password':'password8'}).json()['access_token']
    HD = {'Authorization': f'Bearer {tok}'}
    r = client.post('/reviews/analyst/decision', headers=HD, json={'idea_id':idea_id,'decision':'approved'})
    assert r.status_code == 403

