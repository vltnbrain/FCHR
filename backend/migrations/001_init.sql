-- Initial schema for AI Hub (MVP)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255),
  role VARCHAR(50) NOT NULL DEFAULT 'user',
  department VARCHAR(100),
  password_hash VARCHAR(255),
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ideas (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  author_email VARCHAR(255),
  created_by_id INT REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  status VARCHAR(50) NOT NULL DEFAULT 'submitted'
);

CREATE TABLE IF NOT EXISTS reviews (
  id SERIAL PRIMARY KEY,
  idea_id INT NOT NULL REFERENCES ideas(id),
  reviewer_id INT REFERENCES users(id),
  stage VARCHAR(50) NOT NULL,
  decision VARCHAR(50),
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assignments (
  id SERIAL PRIMARY KEY,
  idea_id INT NOT NULL REFERENCES ideas(id),
  developer_id INT REFERENCES users(id),
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks_marketplace (
  id SERIAL PRIMARY KEY,
  idea_id INT NOT NULL REFERENCES ideas(id),
  open BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events_audit (
  id SERIAL PRIMARY KEY,
  entity VARCHAR(50) NOT NULL,
  entity_id INT NOT NULL,
  event VARCHAR(100) NOT NULL,
  payload JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_queue (
  id SERIAL PRIMARY KEY,
  to_email VARCHAR(255) NOT NULL,
  subject VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Using pgvector (1536 dims typical; can be adjusted)
CREATE TABLE IF NOT EXISTS embeddings (
  id SERIAL PRIMARY KEY,
  idea_id INT NOT NULL REFERENCES ideas(id),
  vector vector(1536),
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Voice usage for quotas
CREATE TABLE IF NOT EXISTS voice_usage (
  id SERIAL PRIMARY KEY,
  api_key VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Voice sessions for dialog tracing/state
CREATE TABLE IF NOT EXISTS voice_sessions (
  id SERIAL PRIMARY KEY,
  api_key VARCHAR(255) NOT NULL,
  user_email VARCHAR(255),
  context JSONB,
  last_response TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
