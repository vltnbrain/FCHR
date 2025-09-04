-- Initialize pgvector extension for AI Hub
CREATE EXTENSION IF NOT EXISTS vector;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_embeddings_entity ON embeddings(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(status);
CREATE INDEX IF NOT EXISTS idx_ideas_author ON ideas(author_user_id);
CREATE INDEX IF NOT EXISTS idx_ideas_created ON ideas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_idea ON reviews(idea_id);
CREATE INDEX IF NOT EXISTS idx_assignments_idea ON assignments(idea_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON events_audit(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue(status);
