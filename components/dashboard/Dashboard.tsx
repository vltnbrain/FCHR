import React, { useEffect, useMemo, useState } from 'react';

type DashboardCounts = Record<string, number>;
type DashboardSLA = {
  analyst_overdue: number;
  finance_overdue: number;
  developer_overdue: number;
};
type DashboardItem = {
  id: number;
  title: string;
  status: string;
  created_at: string;
};

type DashboardResponse = {
  counts: DashboardCounts;
  sla: DashboardSLA;
  latest: DashboardItem[];
};

const API_BASE: string = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function Dashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const endpoint = useMemo(() => {
    // Ensure single trailing slash behavior
    const base = API_BASE.replace(/\/$/, '');
    return `${base}/dashboard`;
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(endpoint)
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = (await r.json()) as DashboardResponse;
        if (!cancelled) setData(j);
      })
      .catch((e) => !cancelled && setError(String(e)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [endpoint, reloadKey]);

  useEffect(() => {
    const onCreated = () => setReloadKey((k) => k + 1);
    if (typeof window !== 'undefined') {
      window.addEventListener('idea:created', onCreated as EventListener);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('idea:created', onCreated as EventListener);
      }
    };
  }, []);

  return (
    <section style={{ padding: '1rem', borderTop: '1px solid #eee' }}>
      <h2 style={{ margin: '0 0 0.5rem 0' }}>AI Hub Dashboard</h2>
      <p style={{ color: '#666', marginTop: 0 }}>Minimal counters and recent ideas.</p>

      {loading && <div>Loading dashboard…</div>}
      {error && (
        <div style={{ color: 'crimson' }}>Failed to load dashboard: {error}</div>
      )}

      {data && (
        <div style={{ display: 'grid', gap: '1rem' }}>
          <div>
            <h3 style={{ margin: '0 0 0.5rem 0' }}>Counts</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
              {Object.entries(data.counts).map(([k, v]) => (
                <div
                  key={k}
                  style={{
                    border: '1px solid #ddd',
                    borderRadius: 6,
                    padding: '0.5rem 0.75rem',
                    minWidth: 120,
                  }}
                >
                  <div style={{ fontSize: 12, color: '#666', textTransform: 'capitalize' }}>{k}</div>
                  <div style={{ fontSize: 18, fontWeight: 600 }}>{v}</div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 style={{ margin: '0 0 0.5rem 0' }}>SLA</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div style={{ border: '1px solid #ddd', borderRadius: 6, padding: '0.5rem 0.75rem' }}>
                Analyst overdue: <b>{data.sla.analyst_overdue}</b>
              </div>
              <div style={{ border: '1px solid #ddd', borderRadius: 6, padding: '0.5rem 0.75rem' }}>
                Finance overdue: <b>{data.sla.finance_overdue}</b>
              </div>
              <div style={{ border: '1px solid #ddd', borderRadius: 6, padding: '0.5rem 0.75rem' }}>
                Developer overdue: <b>{data.sla.developer_overdue}</b>
              </div>
            </div>
          </div>

          <div>
            <h3 style={{ margin: '0 0 0.5rem 0' }}>Recent Ideas</h3>
            {data.latest.length === 0 ? (
              <div style={{ color: '#666' }}>No ideas yet.</div>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {data.latest.map((i) => (
                  <li
                    key={i.id}
                    style={{
                      padding: '0.5rem 0',
                      borderBottom: '1px solid #eee',
                      display: 'flex',
                      justifyContent: 'space-between',
                      gap: '1rem',
                      alignItems: 'baseline',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600 }}>{i.title}</div>
                      <div style={{ fontSize: 12, color: '#666' }}>ID: {i.id}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 12, color: '#666', textTransform: 'capitalize' }}>{i.status}</div>
                      <div style={{ fontSize: 12, color: '#666' }}>
                        {new Date(i.created_at).toLocaleString()}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
