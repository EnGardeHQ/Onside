"""
Comprehensive Unit Tests for DomainRepository

This module implements comprehensive unit tests for the DomainRepository,
following BDD/TDD practices and targeting 90%+ coverage.

Feature: Domain Repository Database Operations
As a developer,
I want to have comprehensive tests for domain repository operations,
So I can ensure data integrity and reliability.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from src.repositories.domain_repository import DomainRepository
from src.models.domain import Domain


class TestDomainRepositoryGetOperations:
    """Test suite for domain retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_domain_when_exists(self, test_db: AsyncSession):
        """
        Given a domain repository with an existing domain
        When I retrieve the domain by ID
        Then the correct domain should be returned
        """
        # Arrange
        repo = DomainRepository(test_db)
        expected_domain = Domain(id=1, domain="example.com", company_id=1)

        # Mock the database execute call
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_domain
        test_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.domain == "example.com"
        test_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_exists(self, test_db: AsyncSession):
        """
        Given a domain repository
        When I retrieve a non-existent domain by ID
        Then None should be returned
        """
        # Arrange
        repo = DomainRepository(test_db)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        test_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_id(999)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_domain_returns_domain_when_exists(self, test_db: AsyncSession):
        """
        Given a domain repository with an existing domain
        When I retrieve the domain by domain name
        Then the correct domain should be returned
        """
        # Arrange
        repo = DomainRepository(test_db)
        expected_domain = Domain(id=1, domain="example.com", company_id=1)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_domain
        test_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_domain("example.com")

        # Assert
        assert result is not None
        assert result.domain == "example.com"
        test_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_company_returns_all_domains_ordered(self, test_db: AsyncSession):
        """
        Given a domain repository with multiple domains for a company
        When I retrieve domains by company ID
        Then all domains should be returned ordered by primary status
        """
        # Arrange
        repo = DomainRepository(test_db)
        domains = [
            Domain(id=1, domain="primary.com", company_id=1, is_primary=True),
            Domain(id=2, domain="secondary.com", company_id=1, is_primary=False)
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = domains
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        test_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_company(1)

        # Assert
        assert len(result) == 2
        assert result[0].is_primary is True
        assert result[1].is_primary is False


class TestDomainRepositoryCreateOperations:
    """Test suite for domain creation operations."""

    @pytest.mark.asyncio
    async def test_create_domain_successfully(self, test_db: AsyncSession):
        """
        Given a valid domain object
        When I create the domain
        Then it should be persisted to the database
        """
        # Arrange
        repo = DomainRepository(test_db)
        new_domain = Domain(domain="newdomain.com", company_id=1)

        test_db.add = MagicMock()
        test_db.commit = AsyncMock()
        test_db.refresh = AsyncMock()

        # Act
        result = await repo.create(new_domain)

        # Assert
        test_db.add.assert_called_once_with(new_domain)
        test_db.commit.assert_called_once()
        test_db.refresh.assert_called_once_with(new_domain)
        assert result == new_domain

    @pytest.mark.asyncio
    async def test_create_domain_with_all_fields(self, test_db: AsyncSession):
        """
        Given a domain object with all fields populated
        When I create the domain
        Then all fields should be persisted correctly
        """
        # Arrange
        repo = DomainRepository(test_db)
        new_domain = Domain(
            domain="complete.com",
            company_id=1,
            is_primary=True,
            is_verified=True
        )

        test_db.add = MagicMock()
        test_db.commit = AsyncMock()
        test_db.refresh = AsyncMock()

        # Act
        result = await repo.create(new_domain)

        # Assert
        assert result.domain == "complete.com"
        assert result.is_primary is True
        assert result.is_verified is True


class TestDomainRepositoryUpdateOperations:
    """Test suite for domain update operations."""

    @pytest.mark.asyncio
    async def test_update_domain_successfully(self, test_db: AsyncSession):
        """
        Given an existing domain
        When I update its fields
        Then the changes should be persisted
        """
        # Arrange
        repo = DomainRepository(test_db)
        update_data = {"is_verified": True}
        updated_domain = Domain(id=1, domain="example.com", is_verified=True)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = updated_domain
        test_db.execute = AsyncMock(return_value=mock_result)
        test_db.commit = AsyncMock()

        # Act
        result = await repo.update(1, update_data)

        # Assert
        assert result is not None
        assert result.is_verified is True
        test_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_domain_returns_none(self, test_db: AsyncSession):
        """
        Given a non-existent domain ID
        When I attempt to update it
        Then None should be returned
        """
        # Arrange
        repo = DomainRepository(test_db)
        update_data = {"is_verified": True}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        test_db.execute = AsyncMock(return_value=mock_result)
        test_db.commit = AsyncMock()

        # Act
        result = await repo.update(999, update_data)

        # Assert
        assert result is None


class TestDomainRepositoryDeleteOperations:
    """Test suite for domain deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_existing_domain_returns_true(self, test_db: AsyncSession):
        """
        Given an existing domain
        When I delete it
        Then True should be returned
        """
        # Arrange
        repo = DomainRepository(test_db)

        mock_result = MagicMock()
        mock_result.rowcount = 1
        test_db.execute = AsyncMock(return_value=mock_result)
        test_db.commit = AsyncMock()

        # Act
        result = await repo.delete(1)

        # Assert
        assert result is True
        test_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_domain_returns_false(self, test_db: AsyncSession):
        """
        Given a non-existent domain
        When I attempt to delete it
        Then False should be returned
        """
        # Arrange
        repo = DomainRepository(test_db)

        mock_result = MagicMock()
        mock_result.rowcount = 0
        test_db.execute = AsyncMock(return_value=mock_result)
        test_db.commit = AsyncMock()

        # Act
        result = await repo.delete(999)

        # Assert
        assert result is False


class TestDomainRepositoryPrimaryOperations:
    """Test suite for primary domain operations."""

    @pytest.mark.asyncio
    async def test_set_primary_domain_successfully(self, test_db: AsyncSession):
        """
        Given a company with multiple domains
        When I set one as primary
        Then only that domain should be marked as primary
        """
        # Arrange
        repo = DomainRepository(test_db)
        primary_domain = Domain(id=1, company_id=1, is_primary=True)

        # Mock both update operations
        mock_result1 = MagicMock()  # For clearing primary status
        mock_result2 = MagicMock()  # For setting new primary
        mock_result2.scalar_one_or_none.return_value = primary_domain

        test_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])
        test_db.commit = AsyncMock()

        # Act
        result = await repo.set_primary_domain(company_id=1, domain_id=1)

        # Assert
        assert result is True
        assert test_db.execute.call_count == 2
        test_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_primary_domain_for_wrong_company_returns_false(
        self, test_db: AsyncSession
    ):
        """
        Given a domain that doesn't belong to the specified company
        When I attempt to set it as primary
        Then False should be returned
        """
        # Arrange
        repo = DomainRepository(test_db)

        mock_result1 = MagicMock()
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = None

        test_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])
        test_db.commit = AsyncMock()

        # Act
        result = await repo.set_primary_domain(company_id=1, domain_id=999)

        # Assert
        assert result is False


class TestDomainRepositoryEdgeCases:
    """Test suite for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_repository_initialization_with_session(self, test_db: AsyncSession):
        """
        Given a database session
        When I initialize a repository
        Then it should store the session correctly
        """
        # Act
        repo = DomainRepository(test_db)

        # Assert
        assert repo.db == test_db

    @pytest.mark.asyncio
    async def test_get_by_company_with_no_domains_returns_empty_list(
        self, test_db: AsyncSession
    ):
        """
        Given a company with no domains
        When I retrieve domains by company ID
        Then an empty list should be returned
        """
        # Arrange
        repo = DomainRepository(test_db)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        test_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repo.get_by_company(1)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_update_with_empty_data_dict(self, test_db: AsyncSession):
        """
        Given an empty update data dictionary
        When I attempt to update a domain
        Then the operation should complete without changes
        """
        # Arrange
        repo = DomainRepository(test_db)
        update_data = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = Domain(id=1)
        test_db.execute = AsyncMock(return_value=mock_result)
        test_db.commit = AsyncMock()

        # Act
        result = await repo.update(1, update_data)

        # Assert
        assert result is not None
        test_db.commit.assert_called_once()
