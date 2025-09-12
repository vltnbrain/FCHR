import React, { useEffect, useMemo, useState } from 'react';

type MarketItem = {
  idea: { id: number; title: string; status: string; created_at: string };
  listed_at?: string;
};

const API_BASE: string = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function Marketplace() {
  const [devId, setDevId] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('devId') || (import.meta as any).env?.VITE_DEV_USER_ID || '';
    }
    return '';
  });
  const [items, setItems] = useState<MarketItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const endpoint = useMemo(() => API_BASE.replace(/\/$/, ''), []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('devId', devId);
    }
  }, [devId]);

  const fetchMarket = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${endpoint}/assignments/marketplace`);
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
    fetchMarket();
  }, []);

  const claim = async (ideaId: number) => {
    if (!devId) {
      alert('Set your developer ID first');
      return;
    }
    try {
      const res = await fetch(`${endpoint}/assignments/marketplace/${ideaId}/claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ developer_user_id: Number(devId) }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await fetchMarket();
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('assignment:claimed', { detail: ideaId }));
        window.dispatchEvent(new CustomEvent('idea:created')); // reuse to refresh dashboard counts
      }
    } catch (e) {
      alert(`Failed to claim: ${e}`);
    }
  };

  return (
    <section style={{ padding: '1rem', borderTop: '1px solid #eee' }}>
      <h2 style={{ margin: '0 0 0.5rem 0' }}>Tasks Marketplace</h2>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <label>
          Your Developer ID:{' '}
          <input value={devId} onChange={(e) => setDevId(e.target.value)} placeholder="e.g., 1" style={{ width: 80 }} />
        </label>
        <button onClick={fetchMarket} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      {error && <div style={{ color: 'crimson' }}>Failed to load: {error}</div>}
      {items.length === 0 && <div style={{ color: '#666' }}>No items in marketplace.</div>}
      {items.length > 0 && (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {items.map((it) => (
            <li key={it.idea.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
              <div>
                <div style={{ fontWeight: 600 }}>{it.idea.title}</div>
                <div style={{ fontSize: 12, color: '#666' }}>Idea #{it.idea.id} · Listed {it.listed_at ? new Date(it.listed_at).toLocaleString() : ''}</div>
              </div>
              <div>
                <button onClick={() => claim(it.idea.id)}>Claim</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

