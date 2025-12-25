# OnSide - Claude Code Project Configuration

## Project Overview
OnSide is a competitive intelligence and SEO analytics platform built with Python/FastAPI. It integrates multiple external APIs (Google Analytics, Google Search Console, SEMrush, Ahrefs, etc.) to provide comprehensive market analysis and competitor tracking.

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Database**: PostgreSQL (production), SQLite (development)
- **Caching**: Redis
- **Task Queue**: Celery
- **Testing**: pytest, pytest-cov
- **Linting**: flake8, black, mypy

## Project Structure
```
OnSide/
├── src/                    # Source code
│   ├── api/               # API endpoints (FastAPI routers)
│   ├── models/            # SQLAlchemy models
│   ├── services/          # Business logic services
│   ├── repositories/      # Data access layer
│   └── core/              # Core utilities and config
├── tests/                  # Test suites
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── scripts/               # Utility scripts
├── alembic/               # Database migrations
├── config/                # Configuration files
└── docs/                  # Documentation
```

## Documentation Reference

### Core Rules (MUST READ)
| Document | Purpose |
|----------|---------|
| `rules.md` | Security standards, root directory policy, code quality |
| `git-rules.md` | **STRICT** commit format, NO AI attribution policy |
| `issue-tracking-rules.md` | Mandatory issue tracking for all work |

### Architecture & API
| Document | Purpose |
|----------|---------|
| `architecture.md` | System architecture, data flow, components |
| `api-reference.md` | All API endpoints, error formats, rate limits |

### Development Guidelines
| Document | Purpose |
|----------|---------|
| `testing-standards.md` | Testing patterns, coverage requirements, BDD/TDD |
| `agent-guidelines.md` | Agent assignment, code patterns, checklists |

## Important Rules
**ALWAYS refer to `.claude/rules.md` for:**
- Secure Software Coding Standards (SSCS)
- Root directory policy
- Git commit standards
- Pull request requirements

**ALWAYS refer to `.claude/git-rules.md` for:**
- NO AI attribution policy (zero tolerance)
- Commit message format
- PR requirements

## Key Conventions

### Code Style
- Use type hints for all functions
- Follow PEP 8 with black formatting
- Maximum line length: 100 characters
- Use docstrings for public functions and classes

### File Organization
- New source files go in `src/` subdirectories
- New tests go in `tests/` matching the src structure
- Utility scripts go in `scripts/`
- **NEVER add files to root directory** unless explicitly allowed in rules.md

### Database
- All schema changes require Alembic migrations
- Use repository pattern for data access
- Models defined in `src/models/`

### API Design
- RESTful conventions
- Version APIs under `/api/v1/`
- Use Pydantic for request/response validation
- Include OpenAPI documentation

### Testing
- Minimum 80% coverage for new code
- Use fixtures for test data
- Mock external API calls
- Integration tests for API endpoints

### Security
- No hardcoded credentials
- Use environment variables for secrets
- Validate all inputs
- Sanitize outputs

## Common Commands
```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Lint code
flake8 src/ tests/
black src/ tests/ --check
mypy src/

# Format code
black src/ tests/

# Run application
uvicorn src.main:app --reload

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Environment Variables
Required environment variables are documented in `.env.example`. Copy to `.env` and configure:
- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - Application secret
- API keys for external services

## Git Workflow
1. Create branch from `main`: `feature/<issue-number>-<description>`
2. Make changes following SSCS
3. Write tests
4. Run linting and tests locally
5. Commit with conventional commit format
6. Push and create PR
7. Address review feedback
8. Merge after approval

## Issue Assignment
When assigning issues to agents:
- Backend issues: `backend-api-architect` or `system-architect`
- Testing issues: `test-automation-specialist` or `qa-bug-hunter`
- Infrastructure issues: `devops-orchestrator`
- Frontend issues: `frontend-ui-builder` or `frontend-ux-architect`
