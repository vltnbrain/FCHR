def test_e2e_flow(client):
    # health
    r = client.get('/healthz')
    assert r.status_code == 200

    # register admin
    r = client.post('/auth/register', json={'email':'admin@test.local','password':'password8'})
    assert r.status_code == 200
    admin_token = r.json()['access_token']
    HADM = {'Authorization': f'Bearer {admin_token}'}

    # create idea via raw
    r = client.post('/ideas/', headers=HADM, json={'raw':'T1\nBody'})
    assert r.status_code == 200
    idea_id = r.json()['idea']['id']

    # request analyst review
    r = client.post('/reviews/request', headers=HADM, json={'idea_id':idea_id,'stage':'analyst'})
    assert r.status_code == 200

    # create analyst and approve
    client.post('/auth/register', json={'email':'analyst@test.local','password':'password8'})
    client.post('/users/assign-role', headers=HADM, json={'email':'analyst@test.local','role':'analyst'})
    tok = client.post('/auth/login', json={'email':'analyst@test.local','password':'password8'}).json()['access_token']
    HAN = {'Authorization': f'Bearer {tok}'}
    r = client.post('/reviews/analyst/decision', headers=HAN, json={'idea_id':idea_id,'decision':'approved'})
    assert r.status_code == 200

    # finance pending
    r = client.get('/reviews/pending?stage=finance', headers=HADM)
    assert r.status_code == 200
    assert any(p['idea_id']==idea_id for p in r.json())

    # audit endpoint accessible to admin
    r = client.get(f'/events?entity=idea&entity_id={idea_id}', headers=HADM)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
