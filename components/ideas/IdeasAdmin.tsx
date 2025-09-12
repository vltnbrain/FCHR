import React, { useEffect, useMemo, useState } from 'react';

type IdeaItem = {
  id: number;
  title: string;
  status: string;
  created_at: string;
};

type IdeaListResponse = {
  items: IdeaItem[];
  total: number;
  skip: number;
  limit: number;
};

const API_BASE: string = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const STATUS_OPTIONS = [
  'new',
  'analyst_review',
  'finance_review',
  'developer_assignment',
  'implementation',
  'completed',
  'rejected',
  'duplicate',
  'improvement',
];

export default function IdeasAdmin() {
  const [status, setStatus] = useState<string>('analyst_review');
  const [items, setItems] = useState<IdeaItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actAsManager, setActAsManager] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('actAsManager') === '1';
    }
    return true;
  });

  const endpoint = useMemo(() => API_BASE.replace(/\/$/, ''), []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('actAsManager', actAsManager ? '1' : '0');
    }
  }, [actAsManager]);

  const fetchIdeas = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = new URL(`${endpoint}/ideas/`);
      if (status) url.searchParams.set('status', status);
      url.searchParams.set('limit', '50');
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as IdeaListResponse;
      setItems(data.items || []);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIdeas();
  }, [status]);

  const action = async (ideaId: number, kind: 'analyst' | 'finance' | 'developers') => {
    try {
      const res = await fetch(`${endpoint}/ideas/${ideaId}/route/${kind}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(actAsManager ? { 'x-user-role': 'manager' } : {}),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await fetchIdeas();
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('idea:created', { detail: ideaId }));
      }
    } catch (e) {
      alert(`Failed to route: ${e}`);
    }
  };

  return (
    <section style={{ padding: '1rem', borderTop: '1px solid #eee' }}>
      <h2 style={{ margin: '0 0 0.5rem 0' }}>Ideas Admin</h2>
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
        <label>
          Status:{' '}
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <button onClick={fetchIdeas} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
        <label style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
          <input type="checkbox" checked={actAsManager} onChange={(e) => setActAsManager(e.target.checked)} />
          Act as Manager (dev)
        </label>
      </div>
      {error && <div style={{ color: 'crimson' }}>Failed to load: {error}</div>}
      {items.length === 0 && <div style={{ color: '#666' }}>No ideas.</div>}
      {items.length > 0 && (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {items.map((it) => (
            <li key={it.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600 }}>{it.title}</div>
                <div style={{ fontSize: 12, color: '#666' }}>
                  ID: {it.id} · {it.status} · {new Date(it.created_at).toLocaleString()}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {it.status === 'new' && (
                  <button onClick={() => action(it.id, 'analyst')}>Route: Analyst</button>
                )}
                {it.status === 'analyst_review' && (
                  <>
                    <button onClick={() => action(it.id, 'finance')}>Route: Finance</button>
                    <button onClick={() => action(it.id, 'developers')}>Route: Developers</button>
                  </>
                )}
                {it.status === 'finance_review' && (
                  <button onClick={() => action(it.id, 'developers')}>Route: Developers</button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

