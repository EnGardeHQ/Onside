# OnSide Project Rules

## Secure Software Coding Standards (SSCS)

### 1. Input Validation & Sanitization
- All user inputs MUST be validated before processing
- Use parameterized queries for all database operations - NEVER use string concatenation for SQL
- Sanitize all data before rendering to prevent XSS attacks
- Validate file uploads: check file type, size, and content
- Use allowlists over denylists for input validation

### 2. Authentication & Authorization
- Store passwords using bcrypt or argon2 with appropriate cost factors
- Implement rate limiting on authentication endpoints
- Use secure session management with httpOnly and secure flags
- Implement proper RBAC (Role-Based Access Control)
- Never expose sensitive credentials in logs, errors, or responses
- API keys and secrets MUST be stored in environment variables, never in code

### 3. Data Protection
- Encrypt sensitive data at rest and in transit
- Use TLS 1.2+ for all network communications
- Implement proper key management practices
- Mask or redact PII in logs
- Follow data retention policies - delete data when no longer needed

### 4. Error Handling & Logging
- Never expose stack traces or internal errors to users
- Log security-relevant events with sufficient context
- Implement centralized logging with tamper protection
- Use structured logging format (JSON)
- Include correlation IDs for request tracing

### 5. Dependency Management
- Keep all dependencies up to date
- Regularly scan for known vulnerabilities (CVE)
- Pin dependency versions in requirements.txt
- Review security advisories for all libraries

### 6. Code Quality
- All code must pass linting (flake8, black, mypy)
- Minimum 80% test coverage for new code
- Security-critical code requires peer review
- No hardcoded secrets or credentials
- Use type hints for all function signatures

---

## Root Directory Policy

### Allowed Files in Root Directory
Only the following files are permitted in the project root:

**Configuration Files (Required):**
- `.env.example` - Environment template (never commit actual .env)
- `.gitignore` - Git ignore patterns
- `pyproject.toml` - Python project configuration
- `pytest.ini` - Pytest configuration
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation

**Configuration Files (Optional):**
- `docker-compose.yml` - Docker orchestration
- `Dockerfile` - Container definition
- `Makefile` - Build automation
- `setup.py` or `setup.cfg` - Package setup (if distributing)

### Allowed Directories in Root
- `.claude/` - Claude Code configuration
- `.git/` - Git repository data
- `.github/` - GitHub workflows and templates
- `alembic/` - Database migrations
- `config/` - Application configuration
- `docs/` - Documentation
- `scripts/` - Utility scripts
- `src/` - Source code
- `tests/` - Test suites
- `templates/` - Template files

### Explicitly Forbidden in Root
- Virtual environments (`venv/`, `*_venv/`, `*env*/`)
- Coverage files (`.coverage*`)
- Database files (`*.db`, `*.sqlite3`)
- Log files (`*.log`)
- Compiled files (`*.pyc`, `__pycache__/`)
- IDE configurations (`.idea/`, `.vscode/`)
- Temporary files (`*.tmp`, `*.bak`)
- Export/report directories (`exports/`, `reports/`)
- Data directories (`*-data/`)

---

## Git Commit Standards

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic change)
- `refactor`: Code restructuring (no feature/fix)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `security`: Security improvements
- `perf`: Performance improvements

### Rules
1. Subject line max 72 characters
2. Use imperative mood ("Add feature" not "Added feature")
3. Reference issue numbers in footer (e.g., `Fixes #123`)
4. Sign commits when possible
5. One logical change per commit
6. Never commit secrets, credentials, or API keys

### Branch Naming
- `feature/<issue-number>-<short-description>`
- `fix/<issue-number>-<short-description>`
- `hotfix/<description>`
- `release/<version>`

---

## Pull Request Requirements

1. All tests must pass
2. Code must pass linting checks
3. Security scan must pass (no high/critical vulnerabilities)
4. At least one approval required
5. Branch must be up to date with main
6. Linked to relevant issue(s)
7. Description includes:
   - Summary of changes
   - Test plan
   - Security considerations (if applicable)
