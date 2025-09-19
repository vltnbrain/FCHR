import os
import pytest

pytestmark = pytest.mark.skipif(
    not (os.getenv('USE_PGVECTOR') in ('1','true','yes') and os.getenv('DATABASE_URL','').startswith('postgresql')),
    reason='Requires Postgres + pgvector'
)


def test_duplicates_pg(client):
    # admin
    adm = client.post('/auth/register', json={'email':'admin@pg','password':'password8'}).json()['access_token']
    H = {'Authorization': f'Bearer {adm}'}
    # create first idea
    r1 = client.post('/ideas/', headers=H, json={'title':'Hello World','description':'Great idea to test vectors'})
    assert r1.status_code == 200
    # create similar second idea
    r2 = client.post('/ideas/', headers=H, json={'title':'Hello World!','description':'Great idea to test vectors and similarity'})
    assert r2.status_code == 200
    dupes = r2.json().get('possible_duplicates', [])
    assert dupes, 'Expected duplicate candidates from pgvector search'
