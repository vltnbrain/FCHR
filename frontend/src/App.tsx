import { useEffect, useState } from 'react'

type Idea = {
  id: number
  title: string
  description: string
  author_email?: string | null
  status?: string
}

export default function App() {
  const [ideas, setIdeas] = useState<Idea[]>([])
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [me, setMe] = useState<{ email: string; role: string } | null>(null)

  const loadIdeas = async () => {
    const res = await fetch('/ideas/')
    const data = await res.json()
    setIdeas(data)
  }

  useEffect(() => {
    loadIdeas()
  }, [])

  const refreshMe = async (t: string) => {
    const res = await fetch('/auth/me', {
      headers: { Authorization: `Bearer ${t}` },
    })
    if (res.ok) {
      const data = await res.json()
      setMe(data)
    }
  }

  const register = async () => {
    const res = await fetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()
    if (data?.access_token) {
      setToken(data.access_token)
      localStorage.setItem('token', data.access_token)
      refreshMe(data.access_token)
    }
  }

  const login = async () => {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()
    if (data?.access_token) {
      setToken(data.access_token)
      localStorage.setItem('token', data.access_token)
      refreshMe(data.access_token)
    }
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    await fetch('/ideas/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ title, description }),
    })
    setTitle('')
    setDescription('')
    loadIdeas()
  }

  const assignRole = async (emailToAssign: string, role: string) => {
    const res = await fetch('/users/assign-role', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ email: emailToAssign, role }),
    })
    return res.ok
  }

  const requestAnalystReview = async (ideaId: number) => {
    await fetch('/reviews/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ idea_id: ideaId, stage: 'analyst' }),
    })
  }

  const [pendingAnalyst, setPendingAnalyst] = useState<any[]>([])
  const [pendingFinance, setPendingFinance] = useState<any[]>([])
  const loadPending = async () => {
    const h = token ? { Authorization: `Bearer ${token}` } : {}
    const a = await fetch('/reviews/pending?stage=analyst', { headers: h })
    const f = await fetch('/reviews/pending?stage=finance', { headers: h })
    setPendingAnalyst(a.ok ? await a.json() : [])
    setPendingFinance(f.ok ? await f.json() : [])
  }

  const decision = async (stage: 'analyst'|'finance', ideaId: number, d: string) => {
    await fetch(`/reviews/${stage}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ idea_id: ideaId, decision: d }),
    })
    loadPending()
    loadIdeas()
  }

  const [assignEmail, setAssignEmail] = useState('')
  const inviteDev = async (ideaId: number) => {
    await fetch('/assignments/invite', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ idea_id: ideaId, developer_email: assignEmail || null }),
    })
  }

  const [pendingAsg, setPendingAsg] = useState<any[]>([])
  const loadAsg = async () => {
    const h = token ? { Authorization: `Bearer ${token}` } : {}
    const r = await fetch('/assignments/pending', { headers: h })
    setPendingAsg(r.ok ? await r.json() : [])
  }

  const respondAsg = async (id: number, resp: 'accept'|'decline') => {
    await fetch('/assignments/respond', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ assignment_id: id, response: resp }),
    })
    loadAsg()
  }

  useEffect(() => {
    if (token) {
      loadPending();
      loadAsg();
    }
  }, [token])

  // Emails queue (admin)
  const [emails, setEmails] = useState<any[]>([])
  const loadEmails = async () => {
    const h = token ? { Authorization: `Bearer ${token}` } : {}
    const r = await fetch('/emails/pending', { headers: h })
    setEmails(r.ok ? await r.json() : [])
  }
  const retryEmail = async (id: number) => {
    const h = token ? { Authorization: `Bearer ${token}` } : {}
    await fetch(`/emails/retry/${id}`, { method: 'POST', headers: h })
    loadEmails()
  }

  const logout = () => {
    setToken(null)
    setMe(null)
    localStorage.removeItem('token')
  }

  return (
    <div style={{ maxWidth: 800, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <h1>AI Hub Dashboard (MVP)</h1>
      <section style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #ddd', borderRadius: 8 }}>
        <h3>Auth</h3>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button type="button" onClick={register}>Register</button>
          <button type="button" onClick={login}>Login</button>
        </div>
        {me ? (
          <div style={{ marginTop: '0.5rem' }}>Logged in as {me.email} ({me.role}) <button type="button" onClick={logout}>Logout</button></div>
        ) : (
          <div style={{ marginTop: '0.5rem', color: '#666' }}>Not authenticated</div>
        )}
      </section>
      <form onSubmit={submit} style={{ display: 'grid', gap: '0.5rem' }}>
        <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} required />
        <textarea placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} required />
        <button type="submit">Add Idea</button>
      </form>
      <h2 style={{ marginTop: '2rem' }}>Ideas</h2>
      <div style={{ marginBottom: 8 }}>
        <label>Status:&nbsp;</label>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All</option>
          <option value="submitted">submitted</option>
          <option value="analyst_pending">analyst_pending</option>
          <option value="finance_pending">finance_pending</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
        </select>
      </div>
      <ul>
        {ideas.filter(i => !statusFilter || i.status === statusFilter).map((i) => (
          <li key={i.id}>
            <strong>{i.title}</strong>
            <div>{i.description}</div>
            {i.status && <div>Status: {i.status}</div>}
            {(me?.role === 'admin' || me?.role === 'manager') && (
              <button type="button" onClick={() => requestAnalystReview(i.id)}>Request analyst review</button>
            )}
            {(me?.role === 'admin' || me?.role === 'manager') && (
              <div style={{ marginTop: 8 }}>
                <input placeholder="Developer email (optional)" value={assignEmail} onChange={(e) => setAssignEmail(e.target.value)} />
                <button type="button" onClick={() => inviteDev(i.id)}>Invite developer</button>
              </div>
            )}
          </li>
        ))}
      </ul>

      {me?.role === 'admin' && (
        <section style={{ marginTop: '2rem' }}>
          <h2>Admin: Assign Role</h2>
          <AdminAssignRole onAssign={assignRole} />
        </section>
      )}

      {me?.role === 'admin' && (
        <section style={{ marginTop: '2rem' }}>
          <h2>Audit Viewer</h2>
          <AuditViewer token={token} />
        </section>
      )}

      {(me?.role === 'analyst' || me?.role === 'admin') && (
        <section style={{ marginTop: '2rem' }}>
          <h2>Analyst: Pending Reviews</h2>
          <PendingReviews items={pendingAnalyst} onDecision={(ideaId, d) => decision('analyst', ideaId, d)} />
        </section>
      )}

      {(me?.role === 'finance' || me?.role === 'admin') && (
        <section style={{ marginTop: '2rem' }}>
          <h2>Finance: Pending Reviews</h2>
          <PendingReviews items={pendingFinance} onDecision={(ideaId, d) => decision('finance', ideaId, d)} />
        </section>
      )}

      {me && (
        <section style={{ marginTop: '2rem' }}>
          <h2>Assignments: Pending</h2>
          <ul>
            {pendingAsg.map((a) => (
              <li key={a.id}>
                #{a.id} idea {a.idea_id} - {a.status}
                {me.role === 'developer' && (
                  <>
                    <button type="button" onClick={() => respondAsg(a.id, 'accept')}>Accept</button>
                    <button type="button" onClick={() => respondAsg(a.id, 'decline')}>Decline</button>
                  </>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {me?.role === 'admin' && (
        <section style={{ marginTop: '2rem' }}>
          <h2>Emails: Pending</h2>
          <div style={{ marginBottom: 8 }}>
            <button type="button" onClick={loadEmails}>Refresh</button>
          </div>
          <ul>
            {emails.map((e) => (
              <li key={e.id}>
                #{e.id} to {e.to} — {e.subject} — {e.status}
                <button type="button" onClick={() => retryEmail(e.id)} style={{ marginLeft: 8 }}>Retry</button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}

function AdminAssignRole({ onAssign }: { onAssign: (email: string, role: string) => Promise<boolean> }) {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('developer')
  const [ok, setOk] = useState<string | null>(null)
  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const r = await onAssign(email, role)
    setOk(r ? 'Assigned' : 'Error')
  }
  return (
    <form onSubmit={submit} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <select value={role} onChange={(e) => setRole(e.target.value)}>
        <option value="developer">developer</option>
        <option value="analyst">analyst</option>
        <option value="finance">finance</option>
        <option value="manager">manager</option>
        <option value="admin">admin</option>
      </select>
      <button type="submit">Assign</button>
      {ok && <span>{ok}</span>}
    </form>
  )
}

function PendingReviews({ items, onDecision }: { items: any[]; onDecision: (ideaId: number, d: string) => void }) {
  return (
    <ul>
      {items.map((r) => (
        <li key={r.id}>
          Review #{r.id} for idea {r.idea_id} — {r.stage}
          <button type="button" onClick={() => onDecision(r.idea_id, 'approved')}>Approve</button>
          <button type="button" onClick={() => onDecision(r.idea_id, 'rejected')}>Reject</button>
        </li>
      ))}
    </ul>
  )
}

function AuditViewer({ token }: { token: string | null }) {
  const [entity, setEntity] = useState('')
  const [entityId, setEntityId] = useState('')
  const [event, setEvent] = useState('')
  const [items, setItems] = useState<any[]>([])
  const load = async () => {
    const params = new URLSearchParams()
    if (entity) params.set('entity', entity)
    if (entityId) params.set('entity_id', entityId)
    if (event) params.set('event', event)
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const r = await fetch(`/events?${params.toString()}`, { headers })
    setItems(r.ok ? await r.json() : [])
  }
  return (
    <div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
        <input placeholder="entity (idea/review/assignment)" value={entity} onChange={(e) => setEntity(e.target.value)} />
        <input placeholder="entity_id" value={entityId} onChange={(e) => setEntityId(e.target.value)} />
        <input placeholder="event" value={event} onChange={(e) => setEvent(e.target.value)} />
        <button type="button" onClick={load}>Load</button>
      </div>
      <ul>
        {items.map((it) => (
          <li key={it.id}>
            #{it.id} [{it.created_at}] {it.entity}({it.entity_id}) {it.event}
          </li>
        ))}
      </ul>
    </div>
  )
}
