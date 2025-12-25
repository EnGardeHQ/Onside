"""
Tests for the domain API endpoints.

These tests verify the functionality of the domain-related API endpoints,
including CRUD operations and domain-specific functionality.

These tests use the actual database connection as per project requirements.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from sqlalchemy import select

from src.models.domain import Domain
from src.models.user import User, UserRole
from src.schemas.domain import DomainCreate, DomainResponse, DomainUpdate
from src.services.domain_service import DomainService
from src.exceptions import DomainValidationError
from src.database import get_db, async_session
from src.auth.security import create_access_token

# Test data
TEST_DOMAIN = "example.com"
TEST_DOMAIN_2 = "test.com"
TEST_COMPANY_ID = 1
TEST_METADATA = {"registrar": "GoDaddy", "expires_at": "2024-01-01"}
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

# Fixture for a test domain data
@pytest.fixture
def domain_data():
    """Test domain data."""
    return {
        "domain": TEST_DOMAIN,
        "is_active": True,
        "is_primary": False,
        "company_id": TEST_COMPANY_ID,
        "metadata": TEST_METADATA
    }

# Fixture for a test user
@pytest_asyncio.fixture
async def test_user():
    """Create a test user in the database."""
    from src.auth.password_utils import generate_password_hash
    
    async with async_session() as session:
        # Check if user already exists
        result = await session.execute(select(User).where(User.email == TEST_EMAIL))
        user = result.scalars().first()
        
        if not user:
            user = User(
                email=TEST_EMAIL,
                username="testuser",
                hashed_password=generate_password_hash(TEST_PASSWORD),
                name="Test User",
                role=UserRole.USER,
                is_active=True,
                is_admin=False
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        return user

# Fixture for an auth token
@pytest_asyncio.fixture
async def auth_token(test_user):
    """Create an auth token for the test user."""
    return create_access_token({"sub": str(test_user.id)})

# Fixture for an authenticated client
@pytest_asyncio.fixture
async def auth_client(test_client, auth_token):
    """Create an authenticated test client."""
    test_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return test_client

# Fixture for a test domain in the database
@pytest_asyncio.fixture
async def test_domain(test_user):
    """Create a test domain in the database."""
    async with async_session() as session:
        domain = Domain(
            domain=TEST_DOMAIN,
            is_active=True,
            is_primary=False,
            company_id=TEST_COMPANY_ID,
            metadata_=TEST_METADATA,
            created_by=test_user.id
        )
        session.add(domain)
        await session.commit()
        await session.refresh(domain)
        return domain

# Test create domain endpoint
@pytest.mark.asyncio
async def test_create_domain_success(auth_client: AsyncClient, domain_data: dict, test_user):
    """Test creating a new domain successfully."""
    # Make the request
    response = await auth_client.post(
        "/api/v1/domains/",
        json=domain_data
    )
    
    # Assert the response
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == TEST_DOMAIN
    assert data["company_id"] == TEST_COMPANY_ID
    assert data["metadata"] == TEST_METADATA
    assert "id" in data
    
    # Verify the domain was created in the database
    async with async_session() as session:
        result = await session.execute(select(Domain).where(Domain.domain == TEST_DOMAIN))
        db_domain = result.scalars().first()
        assert db_domain is not None
        assert db_domain.domain == TEST_DOMAIN
        assert db_domain.company_id == TEST_COMPANY_ID
        assert db_domain.created_by == test_user.id

# Test get domain by ID
@pytest.mark.asyncio
async def test_get_domain_by_id(auth_client: AsyncClient, test_domain: Domain):
    """Test getting a domain by ID."""
    # Make the request
    response = await auth_client.get(f"/api/v1/domains/{test_domain.id}")
    
    # Assert the response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_domain.id
    assert data["domain"] == test_domain.domain

# Test get domain by name
@pytest.mark.asyncio
async def test_get_domain_by_name(auth_client: AsyncClient, test_domain: Domain):
    """Test getting a domain by name."""
    # Make the request
    response = await auth_client.get(f"/api/v1/domains/lookup/{TEST_DOMAIN}")
    
    # Assert the response
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == TEST_DOMAIN
    assert data["id"] == test_domain.id

# Test list domains
@pytest.mark.asyncio
async def test_list_domains(auth_client: AsyncClient, test_domain: Domain):
    """Test listing domains with pagination."""
    # Make the request
    response = await auth_client.get("/api/v1/domains/")
    
    # Assert the response
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert any(d["domain"] == TEST_DOMAIN for d in data["items"])
    assert data["total"] >= 1

# Test update domain
@pytest.mark.asyncio
async def test_update_domain(auth_client: AsyncClient, test_domain: Domain):
    """Test updating a domain."""
    # Update data
    update_data = {"is_active": False, "metadata": {"registrar": "Namecheap"}}
    
    # Make the request
    response = await auth_client.patch(
        f"/api/v1/domains/{test_domain.id}",
        json=update_data
    )
    
    # Assert the response
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["metadata"]["registrar"] == "Namecheap"
    
    # Verify the update in the database
    async with async_session() as session:
        result = await session.execute(select(Domain).where(Domain.id == test_domain.id))
        db_domain = result.scalars().first()
        assert db_domain.is_active is False
        assert db_domain.metadata_["registrar"] == "Namecheap"

# Test delete domain
@pytest.mark.asyncio
async def test_delete_domain(auth_client: AsyncClient, test_domain: Domain):
    """Test deleting a domain."""
    # Make the request
    response = await auth_client.delete(f"/api/v1/domains/{test_domain.id}")
    
    # Assert the response
    assert response.status_code == 204
    
    # Verify the domain was deleted from the database
    async with async_session() as session:
        result = await session.execute(select(Domain).where(Domain.id == test_domain.id))
        db_domain = result.scalars().first()
        assert db_domain is None

# Test set primary domain
@pytest.mark.asyncio
async def test_set_primary_domain(auth_client: AsyncClient, test_domain: Domain):
    """Test setting a domain as primary."""
    # Make the request
    response = await auth_client.post(
        f"/api/v1/domains/{test_domain.id}/set-primary",
        params={"company_id": TEST_COMPANY_ID}
    )
    
    # Assert the response
    assert response.status_code == 200
    data = response.json()
    assert data["is_primary"] is True
    
    # Verify the update in the database
    async with async_session() as session:
        result = await session.execute(select(Domain).where(Domain.id == test_domain.id))
        db_domain = result.scalars().first()
        assert db_domain.is_primary is True
        
        # Verify no other domains are primary for this company
        other_domains = await session.execute(
            select(Domain).where(
                Domain.company_id == TEST_COMPANY_ID,
                Domain.id != test_domain.id,
                Domain.is_primary == True  # noqa: E712
            )
        )
        assert other_domains.scalars().first() is None

# Test domain validation error
@pytest.mark.asyncio
async def test_domain_validation_error(auth_client: AsyncClient, domain_data: dict):
    """Test domain validation error."""
    # Make the request with invalid domain data
    invalid_data = domain_data.copy()
    invalid_data["domain"] = "invalid-domain"
    
    response = await auth_client.post("/api/v1/domains/", json=invalid_data)
    
    # Assert the response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid domain format" in data["detail"]

# Test domain not found
@pytest.mark.asyncio
async def test_domain_not_found(auth_client: AsyncClient):
    """Test getting a non-existent domain."""
    # Make the request with a non-existent domain ID
    response = await auth_client.get("/api/v1/domains/999999")
    
    # Assert the response
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
