from datetime import datetime, timedelta


def test_review_sla_escalation(client):
    # admin
    adm = client.post('/auth/register', json={'email':'adm@sla','password':'password8'}).json()['access_token']
    H = {'Authorization': f'Bearer {adm}'}
    # idea + review
    idea_id = client.post('/ideas/', headers=H, json={'title':'sla','description':'check'}).json()['idea']['id']
    client.post('/reviews/request', headers=H, json={'idea_id':idea_id,'stage':'analyst'})

    # Make the review older than 5 days by direct SQL update (sqlite friendly)
    from app.db.session import SessionLocal
    from app.db import models
    db = SessionLocal()
    try:
        r = db.query(models.Review).filter(models.Review.idea_id==idea_id, models.Review.stage=='analyst').first()
        r.created_at = datetime.utcnow() - timedelta(days=6)
        db.add(r)
        db.commit()
        # Trigger one SLA pass
        from app.services.sla import review_sla_pass
        n = review_sla_pass(db, days=5)
        assert n >= 1
    finally:
        db.close()


def test_assignment_sla_escalation(client):
    # admin
    adm = client.post('/auth/register', json={'email':'adm@sla2','password':'password8'}).json()['access_token']
    H = {'Authorization': f'Bearer {adm}'}
    # idea + invite
    idea_id = client.post('/ideas/', headers=H, json={'title':'sla2','description':'check2'}).json()['idea']['id']
    client.post('/assignments/invite', headers=H, json={'idea_id':idea_id})

    from app.db.session import SessionLocal
    from app.db import models
    db = SessionLocal()
    try:
        a = db.query(models.Assignment).filter(models.Assignment.idea_id==idea_id).first()
        a.created_at = datetime.utcnow() - timedelta(days=6)
        a.status = 'invited'
        db.add(a)
        db.commit()
        from app.services.sla import assignment_sla_pass
        n = assignment_sla_pass(db, days=5)
        assert n >= 1
    finally:
        db.close()

