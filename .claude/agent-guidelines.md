# OnSide Agent Guidelines

## Agent Assignment Matrix

| Issue Type | Primary Agent | Secondary Agent |
|------------|---------------|-----------------|
| Backend API | `backend-api-architect` | `system-architect` |
| External API Integration | `backend-api-architect` | - |
| Database/Models | `backend-api-architect` | `system-architect` |
| Testing | `test-automation-specialist` | `qa-bug-hunter` |
| QA/Bug Hunting | `qa-bug-hunter` | `test-automation-specialist` |
| Infrastructure/DevOps | `devops-orchestrator` | - |
| Architecture Design | `system-architect` | `Plan` agent |
| Frontend UI | `frontend-ui-builder` | `frontend-ux-architect` |
| Frontend UX | `frontend-ux-architect` | `frontend-ui-builder` |
| Code Exploration | `Explore` agent | - |

---

## Pre-Work Requirements

### Before Writing ANY Code

1. **Check for existing issue**
   ```bash
   gh issue list --state open --label "<type>"
   ```

2. **Create issue if none exists** (see `issue-tracking-rules.md`)

3. **Create feature branch**
   ```bash
   git checkout -b <type>/issue-<number>-<description>
   ```

4. **Review relevant .claude files**
   - `rules.md` - Security and coding standards
   - `git-rules.md` - Commit message format
   - `architecture.md` - System architecture
   - `api-reference.md` - API endpoints

---

## Code Quality Standards

### Required for All Code

1. **Type hints** on all functions
   ```python
   async def get_article(self, article_id: int) -> Optional[GNewsArticle]:
   ```

2. **Docstrings** for public functions
   ```python
   async def search(self, query: str) -> SearchResult:
       """
       Search for news articles.

       Args:
           query: Search query string

       Returns:
           SearchResult containing articles and metadata
       """
   ```

3. **Error handling** with proper exceptions
   ```python
   try:
       result = await self._make_request(url)
   except httpx.HTTPError as e:
       logger.error(f"API request failed: {e}")
       raise ExternalAPIError(f"GNews API error: {e}") from e
   ```

4. **Logging** for important operations
   ```python
   logger.info(f"Searching GNews for query: {query}")
   logger.debug(f"API response: {response.status_code}")
   ```

---

## File Organization

### Where to Put New Files

| File Type | Location |
|-----------|----------|
| API endpoints | `src/api/v1/<service>.py` |
| Services | `src/services/<domain>/<service>_service.py` |
| External APIs | `src/services/external_api/<api>_service.py` |
| Models | `src/models/<domain>.py` |
| Repositories | `src/repositories/<service>_repository.py` |
| Schemas | `src/schemas/<domain>.py` |
| Unit tests | `tests/unit/<matching path>/test_<file>.py` |
| Integration tests | `tests/integration/test_<feature>.py` |
| API tests | `tests/api/v1/test_<endpoint>.py` |

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Test functions**: `test_<method>_<scenario>_<expected>`

---

## External API Integration Pattern

When integrating a new external API:

### 1. Model Layer (`src/models/`)
```python
class APIRecord(Base):
    __tablename__ = "api_records"

    id = Column(Integer, primary_key=True)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    cached_until = Column(DateTime)
```

### 2. Repository Layer (`src/repositories/`)
```python
class APIRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: int) -> Optional[APIRecord]:
        pass

    async def create(self, record: APIRecord) -> APIRecord:
        pass
```

### 3. Service Layer (`src/services/external_api/`)
```python
class ExternalAPIService:
    def __init__(self, api_key: str, repository: Optional[APIRepository] = None):
        self.api_key = api_key
        self.repository = repository
        self.base_url = "https://api.example.com"

    async def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make authenticated API request with retry logic."""
        pass
```

### 4. API Endpoints (`src/api/v1/`)
```python
router = APIRouter(prefix="/api/v1/example", tags=["example"])

@router.get("/data")
async def get_data(
    query: str,
    service: ExternalAPIService = Depends(get_service)
) -> DataResponse:
    pass
```

### 5. Tests (parallel structure in `tests/`)
```python
# tests/unit/services/external_api/test_example_service.py
# tests/api/v1/test_example.py
```

---

## Commit Guidelines

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

Closes #<issue-number>
```

### FORBIDDEN (see git-rules.md)
- NO AI attribution
- NO Co-Authored-By lines with AI names
- NO "Generated with" messages
- NO links to AI tools

### Example
```
feat(external-api): Add GNews service integration

- Implement GNewsService with search and headlines
- Add rate limiting (1000 req/day)
- Add retry logic with exponential backoff
- Include 36 unit tests

Closes #21
```

---

## Testing Requirements

### Before Marking Task Complete

1. **Write tests first** (TDD/BDD)
2. **Run test suite**
   ```bash
   pytest tests/ -v --cov=src
   ```
3. **Check coverage** (minimum 80% for new code)
4. **Run linting**
   ```bash
   flake8 src/ tests/
   black src/ tests/ --check
   mypy src/
   ```

### Test Counts Expected

| Component | Minimum Tests |
|-----------|---------------|
| Service class | 15-25 tests |
| Repository class | 8-12 tests |
| API endpoint | 10-15 tests |
| Model class | 5-8 tests |

---

## Security Checklist

Before completing any task:

- [ ] No hardcoded credentials
- [ ] API keys from environment variables
- [ ] Input validation on all endpoints
- [ ] Parameterized database queries
- [ ] No sensitive data in logs
- [ ] Error messages don't expose internals
- [ ] Rate limiting considered
- [ ] Authentication/authorization checked

---

## Documentation Requirements

### Required Documentation

1. **Docstrings** for all public functions/classes
2. **API documentation** via Pydantic schemas (OpenAPI auto-generated)
3. **README updates** for new features
4. **Architecture updates** in `.claude/architecture.md` for major changes

---

## Parallel Task Execution

When assigned multiple issues:

1. **Check dependencies** between issues
2. **Independent issues** can run in parallel
3. **Create separate branches** for each issue
4. **Merge in sequence** to avoid conflicts

### Example Parallel Pattern
```
Issue #21 (GNews) ─────────┐
Issue #22 (GNews+Comp) ────┼──> Merge to main
Issue #23 (IPInfo) ────────┤
Issue #24 (WhoAPI) ────────┘
```

---

## Error Handling Pattern

### Service Layer
```python
from src.core.exceptions import ExternalAPIError, ValidationError

async def fetch_data(self, query: str) -> Data:
    if not query:
        raise ValidationError("Query cannot be empty")

    try:
        response = await self._make_request(query)
    except httpx.HTTPError as e:
        logger.error(f"API error: {e}")
        raise ExternalAPIError(f"Failed to fetch data: {e}") from e

    return self._parse_response(response)
```

### API Layer
```python
@router.get("/data")
async def get_data(query: str):
    try:
        return await service.fetch_data(query)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ExternalAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
```

---

## Rate Limiting & Caching

### External API Rate Limits

| API | Daily Limit | Cache TTL |
|-----|-------------|-----------|
| GNews | 1000 requests | 1 hour |
| IPInfo | 1000 requests | 24 hours |
| WhoAPI | 500 requests | 24 hours |

### Caching Pattern
```python
async def get_with_cache(self, key: str) -> Optional[Data]:
    # Check cache first
    cached = await self.cache.get(key)
    if cached:
        return cached

    # Fetch and cache
    data = await self._fetch(key)
    await self.cache.set(key, data, ttl=3600)
    return data
```

---

## Completion Checklist

Before marking any issue as complete:

- [ ] Issue created and linked
- [ ] Branch created from main
- [ ] Code written following standards
- [ ] Tests written (80%+ coverage)
- [ ] All tests passing
- [ ] Linting passes
- [ ] Documentation updated
- [ ] Commit message follows format
- [ ] PR created with "Closes #XX"
- [ ] NO AI attribution anywhere
