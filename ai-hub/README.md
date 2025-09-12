# AI Hub of Ideas & Tasks

A comprehensive web service that centralizes collection of user ideas and converts them into actionable tasks with role-based routing, deduplication, review loops, and a public dashboard.

## 🎯 Overview

The AI Hub system integrates with the existing FCHR voice assistant to capture ideas through natural conversation and routes them through a structured approval process involving analysts, finance, and developers with SLA-driven workflows.

### Key Features

- **🎤 Voice Integration**: Seamless integration with FCHR voice assistant
- **🔍 Duplicate Detection**: AI-powered similarity detection using embeddings
- **📧 Email Workflows**: Automated notifications with 5-day SLA timers
- **👥 Role-Based Access**: Developer, Analyst, Finance, Manager, Admin roles
- **📊 Public Dashboard**: Real-time status tracking and audit trails
- **⏰ SLA Management**: Automated escalation and deadline tracking
- **🔒 Security**: JWT authentication with RBAC and audit logging

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  FCHR Voice     │    │   AI Hub API     │    │   PostgreSQL     │
│   Assistant     │◄──►│   (FastAPI)      │◄──►│   + pgvector     │
│                 │    │                 │    │                 │
│ • User Context  │    │ • Idea Ingestion │    │ • Ideas         │
│ • Idea Capture  │    │ • Duplicate Check│    │ • Users         │
│ • Status Updates│    │ • Email Routing  │    │ • Reviews       │
└─────────────────┘    │ • SLA Timers     │    │ • Embeddings    │
                       └─────────────────┘    └─────────────────┘
                                ▲                       ▲
                                │                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Celery Worker  │    │   Email Queue    │
                       │                 │    │                 │
                       │ • Background Jobs│    │ • SMTP/MailHog  │
                       │ • SLA Escalations│    │ • Templates      │
                       │ • Report Generation│   └─────────────────┘
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for voice assistant integration)
- Python 3.11+ (for backend development)

### 1. Clone and Setup

```bash
# Navigate to the AI Hub directory
cd ai-hub

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration
# Required: OpenAI API key for embeddings
# Optional: Email SMTP settings
```

### 2. Start Infrastructure

```bash
# Start all services (PostgreSQL, Redis, MailHog, Backend, Worker)
cd infra
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

### 3. Initialize Database

```bash
# The database will be automatically initialized with the init.sql script
# Tables will be created when the backend starts
```

### 4. Test the System

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Email testing interface
open http://localhost:8025
```

## 📁 Project Structure

```
ai-hub/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/endpoints/   # API endpoints
│   │   ├── core/              # Configuration & logging
│   │   ├── db/                # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container
├── frontend/                  # React dashboard (TODO)
├── infra/                     # Infrastructure setup
│   ├── docker-compose.yml     # Local development stack
│   └── init.sql              # Database initialization
├── integrations/
│   └── fchr-voice-bot/        # Voice assistant integration
│       └── aihub-client.js    # JavaScript client library
├── docs/
│   └── idea-handling-guide.md # Voice assistant integration guide
├── scripts/                   # Utility scripts
└── .env.example              # Environment configuration template
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Required |
| `DATABASE_URI` | PostgreSQL connection string | Auto-generated |
| `REDIS_HOST` | Redis host for Celery | `localhost` |
| `SMTP_HOST` | Email SMTP host | `localhost` |
| `SMTP_PORT` | Email SMTP port | `1025` (MailHog) |
| `SLA_ANALYST_DAYS` | Analyst review SLA | `5` |
| `DUPLICATE_SIMILARITY_THRESHOLD` | Similarity threshold | `0.8` |

### Database Models

#### Core Entities

- **Users**: Employee directory with roles and departments
- **Ideas**: User-submitted ideas with metadata and status
- **Reviews**: Analyst and finance review decisions
- **Assignments**: Developer assignments with status tracking
- **Embeddings**: Vector embeddings for duplicate detection
- **EmailQueue**: Outbound email notifications
- **AuditEvent**: Complete audit trail of all system events

#### Status Workflows

```
NEW → ANALYST_REVIEW → FINANCE_REVIEW → DEVELOPER_ASSIGNMENT → IMPLEMENTATION → COMPLETED
     ↓              ↓                  ↓                      ↓
DUPLICATE ← IMPROVEMENT ← REJECTED ← MARKETPLACE ← NO_RESPONSE
```

## 🎯 API Endpoints

### Ideas Management
- `POST /api/v1/ideas` - Submit new idea
- `GET /api/v1/ideas` - List ideas with filtering
- `GET /api/v1/ideas/{id}` - Get idea details
- `GET /api/v1/ideas/{id}/duplicates` - Check for duplicates
- `POST /api/v1/ideas/{id}/route/analyst` - Route to analyst

### User Management
- `POST /api/v1/users` - Create user
- `GET /api/v1/users` - List users
- `GET /api/v1/users/{id}` - Get user details

### Reviews & Assignments
- `POST /api/v1/reviews` - Submit review decision
- `POST /api/v1/assignments` - Create developer assignment
- `PUT /api/v1/assignments/{id}` - Update assignment status

### Dashboard
- `GET /api/v1/dashboard` - Dashboard data
- `GET /api/v1/dashboard/stats` - System statistics

## 🔗 Voice Assistant Integration

### Integration Points

1. **User Resolution**: Identify users by name/email, create if new
2. **Idea Submission**: Capture voice input, structure, and submit
3. **Duplicate Detection**: Check similarity against existing ideas
4. **Status Updates**: Provide real-time status via voice
5. **Email Notifications**: Confirm delivery of notification emails

### Client Usage

```javascript
const { AIHubClient, VoiceAssistantHelper } = require('./aihub-client');

// Initialize client
const aiHub = new AIHubClient('http://localhost:8000/api/v1');
const helper = new VoiceAssistantHelper(aiHub);

// Submit idea from voice
const result = await helper.processIdeaSubmission(
  "I think we should add dark mode to the dashboard",
  {
    name: "John Doe",
    email: "john@company.com",
    role: "developer",
    department: "engineering"
  }
);

// Generate voice response
const response = helper.generateResponse(result, 'submit_idea');
console.log(response);
```

## 📧 Email Workflows

### Notification Types

1. **Analyst Review**: New idea notification with 5-day SLA
2. **Finance Review**: Post-analyst review with department confirmation
3. **Developer Invitation**: Assignment opportunities with accept/decline
4. **Escalation**: Admin notifications for missed SLAs
5. **Status Updates**: Progress notifications to idea authors

### SLA Management

- **Analyst Review**: 5 days from idea submission
- **Finance Review**: 5 days from analyst decision
- **Developer Response**: 5 days from invitation
- **Escalation**: Automatic admin notification on SLA breach

## 🔍 Duplicate Detection

### Process Flow

1. **Embedding Generation**: Convert idea text to vector using OpenAI
2. **Similarity Search**: Query pgvector for similar existing ideas
3. **Threshold Application**:
   - ≥80%: Mark as DUPLICATE
   - 50-79%: Mark as IMPROVEMENT with parent link
   - <50%: Treat as NEW idea

### Performance Optimization

- IVFFlat indexing for fast approximate nearest neighbor search
- Cosine similarity for semantic matching
- Configurable similarity thresholds
- Batch processing for bulk operations

## 🛡️ Security & Compliance

### Authentication & Authorization

- JWT-based authentication
- Role-based access control (RBAC)
- API key support for service integrations
- Session management with configurable expiration

### Data Protection

- PII minimization in logs and audit trails
- Configurable data retention policies
- Admin controls for user data export/deletion
- Rate limiting on public endpoints

### Audit Logging

- Complete audit trail for all state changes
- User activity tracking
- System event logging
- Compliance-ready audit reports

## 📊 Monitoring & Analytics

### Key Metrics

- **Idea Submission Rate**: Ideas per day/week
- **Duplicate Detection Accuracy**: True positive/negative rates
- **SLA Compliance**: Percentage of on-time reviews
- **User Engagement**: Active users, session duration
- **System Performance**: API response times, error rates

### Health Checks

- Database connectivity
- Redis/Celery worker status
- Email service availability
- External API dependencies (OpenAI)

## 🚀 Deployment

### Production Setup

1. **Infrastructure**:
   ```bash
   # Use production docker-compose.prod.yml
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Environment**:
   ```bash
   # Set production environment variables
   export OPENAI_API_KEY="your-production-key"
   export DATABASE_URI="postgresql://user:pass@prod-host:5432/aihub"
   export SMTP_HOST="smtp.sendgrid.net"
   ```

3. **SSL/TLS**:
   - Configure SSL termination
   - Update CORS origins for production domains
   - Set secure cookie flags

### Scaling Considerations

- **Database**: Connection pooling, read replicas
- **Redis**: Cluster configuration for high availability
- **Workers**: Horizontal scaling with multiple Celery instances
- **API**: Load balancer with rate limiting
- **Storage**: External file storage for attachments

### Supabase Setup (Postgres)

You can use Supabase as the managed Postgres for AI Hub:

1. In Supabase dashboard, copy the database connection string (user, password, host, db `postgres`).
2. Set in your `.env`:

```
DATABASE_URI=postgresql://USER:PASSWORD@YOUR-PROJECT-HOST.supabase.co:5432/postgres
DB_SSL=True
```

3. The app will attempt to enable the `vector` extension on startup. Alternatively, run:

```
CREATE EXTENSION IF NOT EXISTS vector;
```

4. For Cloud Run deployments, use the template `ai-hub/infra/cloudrun.env.supabase.example.yaml` and pass it with `--env-vars-file`.

## 🧪 Testing

### Test Categories

- **Unit Tests**: Individual service methods
- **Integration Tests**: API endpoint testing
- **E2E Tests**: Complete workflow testing
- **Performance Tests**: Load testing and benchmarking

### Test Data

```bash
# Seed test data
python scripts/seed_test_data.py

# Run test suite
pytest tests/ -v --cov=app

# Load testing
locust -f tests/load_tests.py
```

## 🤝 Contributing

### Development Workflow

1. **Setup**: Follow Quick Start guide
2. **Branch**: Create feature branch from `main`
3. **Code**: Implement changes with tests
4. **Test**: Run full test suite
5. **Review**: Create pull request
6. **Deploy**: Merge to main triggers deployment

### Code Standards

- **Backend**: Black formatting, isort imports, mypy type checking
- **Frontend**: ESLint, Prettier, TypeScript strict mode
- **Documentation**: Keep README and API docs updated
- **Testing**: Minimum 80% code coverage

## 📚 Additional Documentation

- [API Reference](http://localhost:8000/docs) - Interactive API documentation
- [Voice Integration Guide](./docs/idea-handling-guide.md) - FCHR assistant integration
- [Database Schema](./docs/schema.md) - Complete data model documentation
- [Deployment Guide](./docs/deployment.md) - Production deployment instructions

## 🆘 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Reset database
docker-compose down -v && docker-compose up -d postgres
```

**Email Not Sending**
```bash
# Check MailHog
open http://localhost:8025

# Verify SMTP configuration in .env
# Test email sending
curl -X POST http://localhost:8000/api/v1/test-email
```

**OpenAI API Errors**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Check API quota
open https://platform.openai.com/usage
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🙏 Acknowledgments

- FCHR Voice Assistant team for the integration foundation
- OpenAI for embedding and AI capabilities
- PostgreSQL and pgvector for vector search
- FastAPI community for the excellent framework
