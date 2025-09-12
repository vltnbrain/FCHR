import React, { useMemo, useState } from 'react';

type IdeaCreateRequest = {
  raw_input: string;
  user_name: string;
  user_email?: string;
  user_role?: string;
  user_department?: string;
};

type IdeaResponse = {
  id: number;
  title: string;
};

const API_BASE: string = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function IdeaSubmit() {
  const [form, setForm] = useState<IdeaCreateRequest>({ raw_input: '', user_name: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const endpoint = useMemo(() => {
    const base = API_BASE.replace(/\/$/, '');
    return `${base}/ideas/`;
  }, []);

  const onChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (!form.raw_input.trim() || !form.user_name.trim()) {
      setError('Please fill required fields.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const idea = (await res.json()) as IdeaResponse;
      setSuccess(`Idea submitted (#${idea.id})`);
      setForm({ raw_input: '', user_name: '', user_email: form.user_email, user_role: form.user_role, user_department: form.user_department });
      // Notify listeners (e.g., Dashboard) to refresh
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('idea:created', { detail: idea.id }));
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section style={{ padding: '1rem', borderTop: '1px solid #eee' }}>
      <h2 style={{ margin: '0 0 0.5rem 0' }}>Submit Idea</h2>
      <p style={{ color: '#666', marginTop: 0 }}>Provide your idea and basic details.</p>

      {error && <div style={{ color: 'crimson', marginBottom: '0.5rem' }}>{error}</div>}
      {success && <div style={{ color: 'green', marginBottom: '0.5rem' }}>{success}</div>}

      <form onSubmit={onSubmit} style={{ display: 'grid', gap: '0.5rem', maxWidth: 720 }}>
        <label style={{ display: 'grid', gap: 4 }}>
          <span>Idea (required)</span>
          <textarea
            name="raw_input"
            value={form.raw_input}
            onChange={onChange}
            rows={4}
            placeholder="Describe your idea..."
            required
          />
        </label>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <label style={{ display: 'grid', gap: 4, flex: '1 1 220px' }}>
            <span>Your name (required)</span>
            <input
              name="user_name"
              value={form.user_name}
              onChange={onChange}
              placeholder="Jane Doe"
              required
            />
          </label>
          <label style={{ display: 'grid', gap: 4, flex: '1 1 220px' }}>
            <span>Email</span>
            <input
              name="user_email"
              type="email"
              value={form.user_email || ''}
              onChange={onChange}
              placeholder="jane@example.com"
            />
          </label>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <label style={{ display: 'grid', gap: 4, flex: '1 1 220px' }}>
            <span>Role</span>
            <input
              name="user_role"
              value={form.user_role || ''}
              onChange={onChange}
              placeholder="developer | analyst | ..."
            />
          </label>
          <label style={{ display: 'grid', gap: 4, flex: '1 1 220px' }}>
            <span>Department</span>
            <input
              name="user_department"
              value={form.user_department || ''}
              onChange={onChange}
              placeholder="engineering | finance | ..."
            />
          </label>
        </div>

        <div>
          <button type="submit" disabled={loading}>
            {loading ? 'Submitting…' : 'Submit Idea'}
          </button>
        </div>
      </form>
    </section>
  );
}

