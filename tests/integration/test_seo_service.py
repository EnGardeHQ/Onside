print("\n[test_seo_service.py VERY EARLY DEBUG] File is being read\n")

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, Dict, Any

from src.services.domain_service import DomainService
from src.models.domain import Domain  
from src.models.company import Company 
from src.models.user import User, UserRole 
from src.auth.password_utils import generate_password_hash 
from src.services.seo.seo_service import SEOService
from src.repositories.domain_repository import DomainRepository

# Helper function to get or create a domain for testing
async def get_or_create_user(session: AsyncSession, email: str, username: str, password: str = "testpassword") -> User:
    print(f"[Test Helper] Attempting to get or create user: {email}")
    result = await session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    if not user:
        # Use a simple hash for testing purposes
        hashed_password = f"test_hash_{password}"
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            role=UserRole.USER,
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"[Test Helper] Created user: {email} with ID: {user.id}")
    else:
        print(f"[Test Helper] Found existing user: {email} with ID: {user.id}")
    return user

async def get_or_create_company(session: AsyncSession, company_name: str, company_domain_name: str, user_id: int) -> Company:
    print(f"[Test Helper] Attempting to get or create company: {company_name}")
    result = await session.execute(select(Company).filter_by(name=company_name))
    company = result.scalars().first()
    if not company:
        company = Company(
            name=company_name,
            domain=company_domain_name, 
            user_id=user_id,
            is_active=True
        )
        session.add(company)
        await session.commit()
        await session.refresh(company)
        print(f"[Test Helper] Created company: {company_name} with ID: {company.id}")
    else:
        print(f"[Test Helper] Found existing company: {company_name} with ID: {company.id}")
    return company

async def get_or_create_domain(session: AsyncSession, domain_name: str, company_id: int) -> Domain:
    print(f"[get_or_create_domain] DEBUG: Attempting to get or create domain: {domain_name} for company_id: {company_id}")
    # Ensure the domain name is clean and standardized
    normalized_domain_name = DomainService.normalize_domain(domain_name)
    print(f"[get_or_create_domain] DEBUG: Normalized domain name: {normalized_domain_name}")

    result = await session.execute(select(Domain).filter_by(name=normalized_domain_name))
    domain = result.scalars().first()
    if not domain:
        print(f"[Test Helper] Domain {normalized_domain_name} not found, creating new one for company_id {company_id}.")
        domain = Domain(
            name=normalized_domain_name, 
            is_active=True, 
            company_id=company_id 
        )
        session.add(domain)
        await session.commit()
        await session.refresh(domain)
        print(f"[Test Helper] Created domain: {normalized_domain_name} with ID: {domain.id} for company_id: {domain.company_id}")
    else:
        # If domain exists, its company_id should ideally match or test logic needs to be aware.
        # For now, we assume if it's found by unique name, it's the one we work with.
        # If domain.company_id != company_id:
        #     print(f"[Test Helper] WARNING: Existing domain {domain.name} (ID: {domain.id}) belongs to company {domain.company_id}, but test requested {company_id}.")
        print(f"[Test Helper] Found existing domain: {normalized_domain_name} with ID: {domain.id}. Its current company_id is {domain.company_id}")
    return domain

@pytest.mark.asyncio
async def test_seo_service_integration(db_session: AsyncSession):
    print("\n[TEST_SEO_SERVICE_INTEGRATION] Starting test_seo_service_integration")
    
    # Ensure the db_session is active
    assert db_session is not None, "Database session is None"
    print(f"[TEST_SEO_SERVICE_INTEGRATION] db_session object: {db_session}")
    
    # Initialize SEOService with the active database session
    print("[TEST_SEO_SERVICE_INTEGRATION] Initializing SEOService")
    try:
        seo_service = SEOService(db=db_session)
        assert seo_service is not None, "SEOService initialization failed"
        print("[TEST_SEO_SERVICE_INTEGRATION] SEOService initialized successfully")
        assert seo_service.db is db_session, "SEOService.db is not the provided db_session"
        assert seo_service.domain_repo is not None, "SEOService.domain_repo was not initialized"
        assert seo_service.domain_repo.db is db_session, "DomainRepository in SEOService does not have the correct db_session"

    except Exception as e:
        print(f"[TEST_SEO_SERVICE_INTEGRATION] Error during SEOService initialization: {e}")
        pytest.fail(f"SEOService initialization failed: {e}", pytrace=True)

    # Test data
    test_user_email = "testuser.integration@example.com"
    test_user_username = "testuser_integration"
    test_company_name = "Integration Test Corp"
    test_company_main_domain = "integrationtestcorp.com"
    test_domain_name = "exampleintegrationtest.com"

    # Create/get test user
    print(f"[TEST_SEO_SERVICE_INTEGRATION] Getting/creating test user: {test_user_email}")
    test_user = await get_or_create_user(db_session, test_user_email, test_user_username)
    assert test_user is not None and test_user.id is not None, "Test user creation/retrieval failed"

    # Create/get test company
    print(f"[TEST_SEO_SERVICE_INTEGRATION] Getting/creating test company: {test_company_name}")
    test_company = await get_or_create_company(db_session, test_company_name, test_company_main_domain, test_user.id)
    assert test_company is not None and test_company.id is not None, "Test company creation/retrieval failed"

    normalized_test_domain = DomainService.normalize_domain(test_domain_name)

    print(f"[TEST_SEO_SERVICE_INTEGRATION] Attempting to get_or_create_domain for: {test_domain_name} with company_id {test_company.id}")
    try:
        domain_entry = await get_or_create_domain(db_session, test_domain_name, test_company.id)
        assert domain_entry is not None, f"Failed to get or create domain: {test_domain_name}"
        assert domain_entry.name == normalized_test_domain
        assert domain_entry.company_id == test_company.id, f"Domain {domain_entry.name} created with company_id {domain_entry.company_id} but expected {test_company.id}"
        print(f"[TEST_SEO_SERVICE_INTEGRATION] Domain get_or_create_domain successful for {domain_entry.name}, ID: {domain_entry.id}, Company ID: {domain_entry.company_id}")
    except Exception as e:
        print(f"[TEST_SEO_SERVICE_INTEGRATION] Error in get_or_create_domain: {e}")
        pytest.fail(f"get_or_create_domain failed: {e}", pytrace=True)

    # Add an assertion to check if SEOService can process this domain
    # This part depends on what SEOService.some_method(domain_name) would do.
    # For now, we've tested the domain creation part which was failing.
    # Example: Check if a report can be initiated for this domain (if SEOService has such a method)
    print(f"[TEST_SEO_SERVICE_INTEGRATION] SEOService.get_domain_by_name for {normalized_test_domain}")
    fetched_domain_from_repo = await seo_service.domain_repo.get_by_domain(normalized_test_domain)
    assert fetched_domain_from_repo is not None, "DomainRepository could not fetch the domain by name"
    assert fetched_domain_from_repo.id == domain_entry.id, "Fetched domain ID mismatch"
    assert fetched_domain_from_repo.company_id == test_company.id, "Fetched domain company_id mismatch"

    # Mock external API calls within SEOService methods if they are part of this test's scope
    # For now, focusing on initialization and basic DB interaction

    # Test: Adding a domain through SEOService (if such a method exists and is intended for integration testing)
    # print(f"[TEST_SEO_SERVICE_INTEGRATION] Testing add_domain method with {test_domain_name}")
    # try:
    #     added_domain = await seo_service.add_domain(test_domain_name)
    #     assert added_domain is not None
    #     assert added_domain.name == normalized_test_domain
    #     # Verify it's in the DB
    #     fetched_domain = await seo_service.domain_repo.get_domain_by_name(normalized_test_domain)
    #     assert fetched_domain is not None
    #     assert fetched_domain.id == added_domain.id
    #     print(f"[TEST_SEO_SERVICE_INTEGRATION] add_domain successful for {added_domain.name}")
    # except Exception as e:
    #     print(f"[TEST_SEO_SERVICE_INTEGRATION] Error in seo_service.add_domain: {e}")
    #     pytest.fail(f"seo_service.add_domain failed: {e}", pytrace=True)

    # Test: Fetching domain data using the domain repository
    print(f"[TEST_SEO_SERVICE_INTEGRATION] Testing domain repository get_by_domain method with {test_domain_name}")
    try:
        domain_data = await seo_service.domain_repo.get_by_domain(normalized_test_domain)
        assert domain_data is not None, f"Could not find domain {normalized_test_domain} in repository"
        assert domain_data.name == normalized_test_domain, f"Domain name mismatch: expected {normalized_test_domain}, got {domain_data.name}"
        assert domain_data.id == domain_entry.id, f"Domain ID mismatch: expected {domain_entry.id}, got {domain_data.id}"
        assert domain_data.company_id == test_company.id, f"Company ID mismatch: expected {test_company.id}, got {domain_data.company_id}"
        print(f"[TEST_SEO_SERVICE_INTEGRATION] Successfully retrieved domain: {domain_data.name}, ID: {domain_data.id}, Company ID: {domain_data.company_id}")
    except Exception as e:
        print(f"[TEST_SEO_SERVICE_INTEGRATION] Error in domain_repo.get_by_domain: {e}")
        pytest.fail(f"domain_repo.get_by_domain failed: {e}", pytrace=True)

    # Example: Test a method that might use an external service (mocked)
    # For instance, if analyze_domain was to be tested without external calls:
    # with patch.object(seo_service.serp_service, 'get_serp_data', AsyncMock(return_value={"organic_keywords": 100})) as mock_serp,
    #      patch.object(seo_service.gsc_service, 'get_gsc_data', AsyncMock(return_value={"clicks": 500})) as mock_gsc,
    #      patch.object(seo_service.psi_service, 'get_psi_data', AsyncMock(return_value={"performance_score": 80})) as mock_psi:
        
    #     print(f"[TEST_SEO_SERVICE_INTEGRATION] Testing analyze_domain method with {test_domain_name}")
    #     try:
    #         analysis_result = await seo_service.analyze_domain(test_domain_name)
    #         assert analysis_result is not None
    #         # Add more specific assertions based on expected merged/analyzed data
    #         assert "serp_data" in analysis_result
    #         assert "gsc_data" in analysis_result
    #         assert "psi_data" in analysis_result
    #         print(f"[TEST_SEO_SERVICE_INTEGRATION] analyze_domain successful for {test_domain_name}")
            
    #         # Verify mocks were called
    #         mock_serp.assert_called_once_with(test_domain_name)
    #         mock_gsc.assert_called_once_with(test_domain_name)
    #         mock_psi.assert_called_once_with(test_domain_name)
            
    #     except Exception as e:
    #         print(f"[TEST_SEO_SERVICE_INTEGRATION] Error in seo_service.analyze_domain: {e}")
    #         pytest.fail(f"seo_service.analyze_domain failed: {e}", pytrace=True)

    # Test a scenario with an invalid domain to ensure graceful handling
    invalid_domain = "not_a_valid_domain_}"
    print(f"[TEST_SEO_SERVICE_INTEGRATION] Testing with invalid domain: {invalid_domain}")
    try:
        # Try to get the domain directly from the repository
        domain_data = await seo_service.domain_repo.get_by_domain(invalid_domain)
        # The domain shouldn't exist in the database
        assert domain_data is None, f"Expected None for invalid domain '{invalid_domain}', but got {domain_data}"
        print(f"[TEST_SEO_SERVICE_INTEGRATION] Successfully handled invalid domain: {invalid_domain}")
    except Exception as e:
        # Log and fail the test if there's an unexpected error
        print(f"[TEST_SEO_SERVICE_INTEGRATION] Unexpected error for invalid domain {invalid_domain}: {e}")
        pytest.fail(f"Processing invalid domain {invalid_domain} did not behave as expected: {e}", pytrace=True)


    # Test that an unknown domain returns None from the repository
    unknown_domain = "unknown-domain-does-not-exist.com"
    print(f"[TEST_SEO_SERVICE_INTEGRATION] Testing repository with unknown domain: {unknown_domain}")
    try:
        # Try to get the domain directly from the repository
        domain_data = await seo_service.domain_repo.get_by_domain(unknown_domain)
        # The domain shouldn't exist in the database
        assert domain_data is None, f"Expected None for unknown domain '{unknown_domain}', but got {domain_data}"
        print(f"[TEST_SEO_SERVICE_INTEGRATION] Successfully handled unknown domain: {unknown_domain}")
    except Exception as e:
        # Log and fail the test if there's an unexpected error
        print(f"[TEST_SEO_SERVICE_INTEGRATION] Error in domain_repo.get_by_domain with unknown domain: {e}")
        pytest.fail(f"domain_repo.get_by_domain with unknown domain failed: {e}", pytrace=True)

    print("[TEST_SEO_SERVICE_INTEGRATION] Test completed successfully.")


# Example of how you might test specific data processing if SEOService had such methods
# @pytest.mark.asyncio
# async def test_seo_service_process_data_logic(db_session: AsyncSession):
#     seo_service = SEOService(db=db_session)
#     # Mock underlying service calls if SEOService.process_some_data itself calls other services
#     # For example, if it calls self.serp_service.get_raw_data(...)
#     with patch.object(seo_service.serp_service, 'get_raw_data', AsyncMock(return_value={"key": "value"})) as mock_raw_data:
#         processed_data = await seo_service.process_some_data("example.com")
#         assert processed_data["processed_key"] == "PROCESSED_VALUE"
#         mock_raw_data.assert_called_once_with("example.com")

# Remember to add tests for failure cases, edge cases, and specific business logic paths
# within SEOService as its functionality expands.
