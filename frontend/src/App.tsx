import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent, MouseEvent, ReactNode } from 'react'

type Idea = {
  id: number
  title: string
  description: string
  author_email?: string | null
  status?: string
}

type NavSection = {
  id: string
  label: string
  available: boolean
}

type ReviewItem = {
  id: number
  idea_id: number
  stage: string
  created_at?: string
}

type AssignmentSummary = {
  id: number
  idea_id: number
  status: string
  developer_id?: number | null
}

type EmailQueueItem = {
  id: number
  to: string
  subject: string
  status: string
}

type AuditEvent = {
  id: number
  created_at: string
  entity: string
  entity_id: number | string
  event: string
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

  const [activeSection, setActiveSection] = useState('auth')
  const [navOpen, setNavOpen] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)
  const [showToTop, setShowToTop] = useState(false)

  const navSections = useMemo<NavSection[]>(
    () => [
      { id: 'auth', label: 'Auth', available: true },
      { id: 'ideas', label: 'Ideas', available: true },
      { id: 'admin', label: 'Admin', available: me?.role === 'admin' },
      {
        id: 'analyst',
        label: 'Analyst',
        available: me?.role === 'analyst' || me?.role === 'admin',
      },
      {
        id: 'finance',
        label: 'Finance',
        available: me?.role === 'finance' || me?.role === 'admin',
      },
      { id: 'assignments', label: 'Assignments', available: Boolean(me) },
      { id: 'emails', label: 'Emails', available: me?.role === 'admin' },
    ],
    [me]
  )

  const loadIdeas = async () => {
    const res = await fetch('/ideas/')
    const data = await res.json()
    setIdeas(data)
  }

  useEffect(() => {
    loadIdeas()
  }, [])

  const refreshMe = useCallback(async (t: string) => {
    const res = await fetch('/auth/me', {
      headers: { Authorization: `Bearer ${t}` },
    })
    if (res.ok) {
      const data = await res.json()
      setMe(data)
    }
  }, [])

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

  const submit = async (e: FormEvent<HTMLFormElement>) => {
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
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ idea_id: ideaId, stage: 'analyst' }),
    })
  }

  const [pendingAnalyst, setPendingAnalyst] = useState<ReviewItem[]>([])
  const [pendingFinance, setPendingFinance] = useState<ReviewItem[]>([])
  const loadPending = useCallback(async () => {
    if (!token) {
      setPendingAnalyst([])
      setPendingFinance([])
      return
    }
    const headers = { Authorization: `Bearer ${token}` }
    try {
      const [analystRes, financeRes] = await Promise.all([
        fetch('/reviews/pending?stage=analyst', { headers }),
        fetch('/reviews/pending?stage=finance', { headers }),
      ])
      setPendingAnalyst(analystRes.ok ? ((await analystRes.json()) as ReviewItem[]) : [])
      setPendingFinance(financeRes.ok ? ((await financeRes.json()) as ReviewItem[]) : [])
    } catch (error) {
      console.error('Failed to load pending reviews', error)
      setPendingAnalyst([])
      setPendingFinance([])
    }
  }, [token])

  const decision = async (stage: 'analyst' | 'finance', ideaId: number, d: string) => {
    await fetch(`/reviews/${stage}/decision`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ idea_id: ideaId, decision: d }),
    })
    loadPending()
    loadIdeas()
  }

  const [assignEmail, setAssignEmail] = useState('')
  const inviteDev = async (ideaId: number) => {
    await fetch('/assignments/invite', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ idea_id: ideaId, developer_email: assignEmail || null }),
    })
  }

  const [pendingAsg, setPendingAsg] = useState<AssignmentSummary[]>([])
  const loadAsg = useCallback(async () => {
    if (!token) {
      setPendingAsg([])
      return
    }
    const headers = { Authorization: `Bearer ${token}` }
    try {
      const response = await fetch('/assignments/pending', { headers })
      setPendingAsg(response.ok ? ((await response.json()) as AssignmentSummary[]) : [])
    } catch (error) {
      console.error('Failed to load assignments', error)
      setPendingAsg([])
    }
  }, [token])

  const respondAsg = async (id: number, resp: 'accept' | 'decline') => {
    await fetch('/assignments/respond', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ assignment_id: id, response: resp }),
    })
    loadAsg()
  }

  useEffect(() => {
    if (!token) {
      setPendingAnalyst([])
      setPendingFinance([])
      setPendingAsg([])
      return
    }
    loadPending()
    loadAsg()
    refreshMe(token)
  }, [token, loadPending, loadAsg, refreshMe])

  const [emails, setEmails] = useState<EmailQueueItem[]>([])
  const loadEmails = useCallback(async () => {
    if (!token) {
      setEmails([])
      return
    }
    const headers = { Authorization: `Bearer ${token}` }
    try {
      const response = await fetch('/emails/pending', { headers })
      setEmails(response.ok ? ((await response.json()) as EmailQueueItem[]) : [])
    } catch (error) {
      console.error('Failed to load emails', error)
      setEmails([])
    }
  }, [token])
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

  useEffect(() => {
    const syncStateWithScroll = () => {
      const y = window.scrollY || document.documentElement.scrollTop
      setIsScrolled(y > 8)
      setShowToTop(y > 480)
    }
    syncStateWithScroll()
    window.addEventListener('scroll', syncStateWithScroll, { passive: true })
    return () => window.removeEventListener('scroll', syncStateWithScroll)
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      return
    }
    const observer = new IntersectionObserver(
      entries => {
        const visible = entries
          .filter(entry => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
        if (visible && visible.target.id !== activeSection) {
          setActiveSection(visible.target.id)
        }
      },
      { rootMargin: '-64px 0px -55%', threshold: [0.25, 0.5, 0.75] }
    )

    navSections.forEach(section => {
      const el = document.getElementById(section.id)
      if (el) {
        observer.observe(el)
      }
    })

    return () => observer.disconnect()
  }, [navSections, activeSection])

  useEffect(() => {
    if (!navSections.some(section => section.id === activeSection)) {
      setActiveSection(navSections[0]?.id ?? 'auth')
    }
  }, [navSections, activeSection])

  const handleNavLinkClick = (e: MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault()
    setNavOpen(false)
    setActiveSection(id)
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      if (window.history?.replaceState) {
        window.history.replaceState(null, '', `#${id}`)
      }
    }
  }

  const requireRole = (roles: string[], content: ReactNode) => {
    if (!me) {
      return <p className="lk-section__placeholder">Available after login.</p>
    }
    if (!roles.includes(me.role)) {
      return <p className="lk-section__placeholder">Requires role: {roles.join(', ')}</p>
    }
    return content
  }

  return (
    <div className="lk-app">
      <header className={`lk-nav ${isScrolled ? 'lk-nav--scrolled' : ''}`}>
        <div className="lk-nav__brand">
          <span className="lk-nav__logo" aria-hidden>AI</span>
          <div className="lk-nav__title">
            <strong>Personal Cabinet</strong>
            <span>AI Hub</span>
          </div>
        </div>
        <button
          type="button"
          className={`lk-nav__toggle ${navOpen ? 'is-active' : ''}`}
          aria-label="Toggle navigation"
          aria-expanded={navOpen}
          onClick={() => setNavOpen(open => !open)}
        >
          <span />
        </button>
        <nav className={`lk-nav__links ${navOpen ? 'is-open' : ''}`}>
          {navSections.map(section => (
            <a
              key={section.id}
              href={`#${section.id}`}
              className={`lk-nav__link ${activeSection === section.id ? 'is-active' : ''} ${
                section.available ? '' : 'is-disabled'
              }`}
              title={section.available ? undefined : 'Requires additional permissions'}
              onClick={event => handleNavLinkClick(event, section.id)}
            >
              {section.label}
            </a>
          ))}
        </nav>
      </header>

      <main className="lk-main">
        <section id="auth" className="lk-section">
          <header className="lk-section__header">
            <h2>Auth</h2>
            <p>Sign in to unlock personal features.</p>
          </header>
          <div className="lk-auth">
            <div className="lk-auth__form">
              <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
              <input
                placeholder="Password"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
              <div className="lk-auth__actions">
                <button type="button" onClick={register}>
                  Register
                </button>
                <button type="button" onClick={login}>
                  Login
                </button>
              </div>
            </div>
            {me ? (
              <div className="lk-auth__status">
                <span className="lk-auth__dot" aria-hidden />
                <div>
                  <div className="lk-auth__user">{me.email}</div>
                  <div className="lk-auth__role">Role: {me.role}</div>
                </div>
                <button type="button" onClick={logout} className="lk-auth__logout">
                  Logout
                </button>
              </div>
            ) : (
              <p className="lk-section__placeholder">Not authenticated.</p>
            )}
          </div>
        </section>

        <section id="ideas" className="lk-section">
          <header className="lk-section__header">
            <h2>Ideas</h2>
            <p>Submit and track ideas across the pipeline.</p>
          </header>
          <form onSubmit={submit} className="lk-ideas__form">
            <input data-testid="idea-title-input" placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} required />
            <textarea
              data-testid="idea-description-input"
              placeholder="Description"
              value={description}
              onChange={e => setDescription(e.target.value)}
              required
            />
            <button type="submit">Add Idea</button>
          </form>
          <div className="lk-ideas__filters">
            <label>
              Status
              <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                <option value="">All</option>
                <option value="submitted">submitted</option>
                <option value="analyst_pending">analyst_pending</option>
                <option value="finance_pending">finance_pending</option>
                <option value="approved">approved</option>
                <option value="rejected">rejected</option>
              </select>
            </label>
          </div>
          <ul className="lk-ideas__list">
            {ideas
              .filter(i => !statusFilter || i.status === statusFilter)
              .map(i => (
                <li key={i.id} className="lk-ideas__item">
                  <strong>{i.title}</strong>
                  <div>{i.description}</div>
                  {i.status && <div className="lk-ideas__status">Status: {i.status}</div>}
                  {(me?.role === 'admin' || me?.role === 'manager') && (
                    <button type="button" onClick={() => requestAnalystReview(i.id)}>
                      Request analyst review
                    </button>
                  )}
                  {(me?.role === 'admin' || me?.role === 'manager') && (
                    <div className="lk-ideas__assign">
                      <input
                        placeholder="Developer email (optional)"
                        value={assignEmail}
                        onChange={e => setAssignEmail(e.target.value)}
                      />
                      <button type="button" onClick={() => inviteDev(i.id)}>
                        Invite developer
                      </button>
                    </div>
                  )}
                </li>
              ))}
          </ul>
        </section>

        <section id="admin" className="lk-section">
          <header className="lk-section__header">
            <h2>Admin Tools</h2>
            <p>Manage user roles and access event history.</p>
          </header>
          {requireRole(['admin'], (
            <>
              <AdminAssignRole onAssign={assignRole} />
              <div className="lk-section__subheader">Audit trail</div>
              <AuditViewer token={token} />
            </>
          ))}
        </section>

        <section id="analyst" className="lk-section">
          <header className="lk-section__header">
            <h2>Analyst Reviews</h2>
            <p>Process pending analyst-stage reviews.</p>
          </header>
          {requireRole(['analyst', 'admin'], (
            <PendingReviews items={pendingAnalyst} onDecision={(ideaId, d) => decision('analyst', ideaId, d)} />
          ))}
        </section>

        <section id="finance" className="lk-section">
          <header className="lk-section__header">
            <h2>Finance Reviews</h2>
            <p>Review ideas awaiting finance approval.</p>
          </header>
          {requireRole(['finance', 'admin'], (
            <PendingReviews items={pendingFinance} onDecision={(ideaId, d) => decision('finance', ideaId, d)} />
          ))}
        </section>

        <section id="assignments" className="lk-section">
          <header className="lk-section__header">
            <h2>Assignments</h2>
            <p>Track and respond to developer assignments.</p>
          </header>
          {!me ? (
            <p className="lk-section__placeholder">Login to view assignments.</p>
          ) : pendingAsg.length === 0 ? (
            <p className="lk-section__placeholder">No assignments yet.</p>
          ) : (
            <ul className="lk-assignments__list">
              {pendingAsg.map(a => (
                <li key={a.id}>
                  #{a.id} idea {a.idea_id} - {a.status}
                  {me.role === 'developer' && (
                    <span className="lk-assignments__actions">
                      <button type="button" onClick={() => respondAsg(a.id, 'accept')}>
                        Accept
                      </button>
                      <button type="button" onClick={() => respondAsg(a.id, 'decline')}>
                        Decline
                      </button>
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section id="emails" className="lk-section">
          <header className="lk-section__header">
            <h2>Emails</h2>
            <p>Inspect and retry pending notifications.</p>
          </header>
          {requireRole([
            'admin',
          ], (
            <>
              <div className="lk-emails__actions">
                <button type="button" onClick={loadEmails}>
                  Refresh
                </button>
              </div>
              <ul className="lk-emails__list">
                {emails.map(e => (
                  <li key={e.id}>
                    #{e.id} to {e.to} - {e.subject} - {e.status}
                    <button type="button" onClick={() => retryEmail(e.id)}>
                      Retry
                    </button>
                  </li>
                ))}
              </ul>
            </>
          ))}
        </section>
      </main>

      {showToTop && (
        <button type="button" className="lk-scroll-top" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          ↑ Top
        </button>
      )}
    </div>
  )
}

function AdminAssignRole({ onAssign }: { onAssign: (email: string, role: string) => Promise<boolean> }) {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('developer')
  const [ok, setOk] = useState<string | null>(null)
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const r = await onAssign(email, role)
    setOk(r ? 'Assigned' : 'Error')
  }
  return (
    <form onSubmit={submit} className="lk-admin__form">
      <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
      <select value={role} onChange={e => setRole(e.target.value)}>
        <option value="developer">developer</option>
        <option value="analyst">analyst</option>
        <option value="finance">finance</option>
        <option value="manager">manager</option>
        <option value="admin">admin</option>
      </select>
      <button type="submit">Assign</button>
      {ok && <span className="lk-admin__status">{ok}</span>}
    </form>
  )
}

function PendingReviews({ items, onDecision }: { items: ReviewItem[]; onDecision: (ideaId: number, d: 'approved' | 'rejected') => void }) {
  if (items.length === 0) {
    return <p className="lk-section__placeholder">No pending reviews.</p>
  }

  return (
    <ul className="lk-reviews__list">
      {items.map(r => (
        <li key={r.id}>
          Review #{r.id} for idea {r.idea_id} - {r.stage}
          <span className="lk-reviews__actions">
            <button type="button" onClick={() => onDecision(r.idea_id, 'approved')}>
              Approve
            </button>
            <button type="button" onClick={() => onDecision(r.idea_id, 'rejected')}>
              Reject
            </button>
          </span>
        </li>
      ))}
    </ul>
  )
}

function AuditViewer({ token }: { token: string | null }) {
  const [entity, setEntity] = useState('')
  const [entityId, setEntityId] = useState('')
  const [event, setEvent] = useState('')
  const [items, setItems] = useState<AuditEvent[]>([])
  const load = async () => {
    const params = new URLSearchParams()
    if (entity) params.set('entity', entity)
    if (entityId) params.set('entity_id', entityId)
    if (event) params.set('event', event)
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    try {
      const response = await fetch(`/events?${params.toString()}`, { headers })
      setItems(response.ok ? ((await response.json()) as AuditEvent[]) : [])
    } catch (error) {
      console.error('Failed to load audit events', error)
      setItems([])
    }
  }
  return (
    <div className="lk-audit">
      <div className="lk-audit__controls">
        <input placeholder="entity (idea/review/assignment)" value={entity} onChange={e => setEntity(e.target.value)} />
        <input placeholder="entity_id" value={entityId} onChange={e => setEntityId(e.target.value)} />
        <input placeholder="event" value={event} onChange={e => setEvent(e.target.value)} />
        <button type="button" onClick={load}>
          Load
        </button>
      </div>
      <ul className="lk-audit__list">
        {items.map(it => (
          <li key={it.id}>
            #{it.id} [{it.created_at}] {it.entity}({it.entity_id}) {it.event}
          </li>
        ))}
      </ul>
    </div>
  )
}
