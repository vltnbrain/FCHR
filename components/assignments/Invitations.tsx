import React, { useEffect, useMemo, useState } from 'react';

type AssignmentItem = {
  id: number;
  status: string;
  invited_at?: string;
  responded_at?: string;
  idea: { id: number; title: string; status: string; created_at: string };
};

const API_BASE: string = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function Invitations() {
  const [devId, setDevId] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('devId') || (import.meta as any).env?.VITE_DEV_USER_ID || '';
    }
    return '';
  });
  const [items, setItems] = useState<AssignmentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const endpoint = useMemo(() => API_BASE.replace(/\/$/, ''), []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('devId', devId);
    }
  }, [devId]);

  const fetchInvites = async () => {
    if (!devId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${endpoint}/assignments?developer_id=${encodeURIComponent(devId)}&status=invited`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setItems(data.items || []);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvites();
    // Also refetch on idea submissions
    const onCreated = () => fetchInvites();
    if (typeof window !== 'undefined') {
      window.addEventListener('idea:created', onCreated as EventListener);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('idea:created', onCreated as EventListener);
      }
    };
  }, [devId]);

  const act = async (assignmentId: number, action: 'accept' | 'decline') => {
    try {
      const res = await fetch(`${endpoint}/assignments/${assignmentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await fetchInvites();
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('assignment:updated', { detail: assignmentId }));
      }
    } catch (e) {
      alert(`Failed to ${action}: ${e}`);
    }
  };

  return (
    <section style={{ padding: '1rem', borderTop: '1px solid #eee' }}>
      <h2 style={{ margin: '0 0 0.5rem 0' }}>Developer Invitations</h2>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <label>
          Your Developer ID:{' '}
          <input value={devId} onChange={(e) => setDevId(e.target.value)} placeholder="e.g., 1" style={{ width: 80 }} />
        </label>
        <button onClick={fetchInvites} disabled={!devId || loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      {error && <div style={{ color: 'crimson' }}>Failed to load: {error}</div>}
      {!devId && <div style={{ color: '#666' }}>Set your developer ID to view invites.</div>}
      {devId && items.length === 0 && <div style={{ color: '#666' }}>No invitations.</div>}
      {items.length > 0 && (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {items.map((it) => (
            <li key={it.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
              <div>
                <div style={{ fontWeight: 600 }}>{it.idea.title}</div>
                <div style={{ fontSize: 12, color: '#666' }}>Assignment #{it.id} · Invited {it.invited_at ? new Date(it.invited_at).toLocaleString() : ''}</div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={() => act(it.id, 'accept')}>Accept</button>
                <button onClick={() => act(it.id, 'decline')}>Decline</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

