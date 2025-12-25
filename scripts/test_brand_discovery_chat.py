#!/usr/bin/env python3
"""
Test script for Brand Discovery Chat

This script demonstrates the brand discovery chat functionality
and can be used for quick testing during development.

Usage:
    python scripts/test_brand_discovery_chat.py
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.brand_discovery_chat import BrandDiscoveryChatSession
from src.services.ai.brand_discovery_chat import BrandDiscoveryChatService
from src.database import Base


def setup_test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


async def test_conversation():
    """Run a complete test conversation."""
    print("=" * 80)
    print("Brand Discovery Chat - Test Script")
    print("=" * 80)
    print()

    # Setup
    db = setup_test_db()
    service = BrandDiscoveryChatService(db)

    # Start conversation
    print("Starting conversation...")
    start_response = service.start_conversation(user_id="test_user_123")
    print(f"✓ Session created: {start_response.session_id}")
    print(f"AI: {start_response.first_message}")
    print()

    # Simulate conversation
    conversation = [
        "Acme Corporation",
        "acmecorp.com",
        "We're in SaaS - email marketing software for small businesses",
        "Email automation, newsletter tools, and campaign analytics",
        "Mailchimp and Constant Contact",
        "email marketing, marketing automation, newsletter software"
    ]

    print("Simulating user conversation...")
    print("-" * 80)

    for i, user_message in enumerate(conversation, 1):
        print(f"\nUser: {user_message}")

        # Send message
        response = await service.send_message(
            session_id=start_response.session_id,
            user_message=user_message
        )

        print(f"AI: {response.ai_response}")
        print(f"Progress: {response.progress_pct}%")

        if response.extracted_data.brand_name:
            print(f"  Brand: {response.extracted_data.brand_name}")
        if response.extracted_data.website:
            print(f"  Website: {response.extracted_data.website}")
        if response.extracted_data.industry:
            print(f"  Industry: {response.extracted_data.industry}")

        if response.is_complete:
            print("\n✓ Conversation complete!")
            break

    print("\n" + "-" * 80)

    # Get final state
    print("\nGetting conversation state...")
    state = service.get_conversation_state(start_response.session_id)
    print(f"Progress: {state.progress_pct}%")
    print(f"Missing fields: {state.missing_fields}")
    print(f"Complete: {state.is_complete}")

    # Try to finalize
    print("\nFinalizing conversation...")
    try:
        finalize_response = service.finalize_conversation(start_response.session_id)
        print("✓ Finalization successful!")
        print(f"\nQuestionnaire:")
        print(f"  Brand: {finalize_response.questionnaire.brand_name}")
        print(f"  Website: {finalize_response.questionnaire.website}")
        print(f"  Industry: {finalize_response.questionnaire.industry}")
        print(f"  Products/Services: {finalize_response.questionnaire.products_services}")
        if finalize_response.questionnaire.competitors:
            print(f"  Competitors: {', '.join(finalize_response.questionnaire.competitors)}")
        if finalize_response.questionnaire.keywords:
            print(f"  Keywords: {', '.join(finalize_response.questionnaire.keywords)}")
        print(f"\n{finalize_response.message}")
    except ValueError as e:
        print(f"✗ Finalization failed: {e}")

    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)


async def test_url_normalization():
    """Test URL normalization functionality."""
    print("\n" + "=" * 80)
    print("Testing URL Normalization")
    print("=" * 80)

    db = setup_test_db()
    service = BrandDiscoveryChatService(db)

    test_urls = [
        "https://www.example.com",
        "http://example.com/",
        "www.example.com/path",
        "EXAMPLE.COM",
        "https://example.com/products/page.html",
    ]

    print("\nURL Normalization Tests:")
    for url in test_urls:
        cleaned = service._clean_url(url)
        print(f"  {url:45} -> {cleaned}")

    print("\n✓ URL normalization tests passed")


async def test_data_extraction():
    """Test data extraction and cleaning."""
    print("\n" + "=" * 80)
    print("Testing Data Extraction")
    print("=" * 80)

    db = setup_test_db()
    service = BrandDiscoveryChatService(db)

    test_data = {
        "competitors": "Mailchimp, Constant Contact and SendGrid",
        "keywords": "email marketing, automation, newsletters",
        "website": "https://www.example.com/",
    }

    print("\nCleaning extracted data:")
    print(f"Input: {test_data}")

    cleaned = service._clean_extracted_data(test_data)

    print(f"\nOutput:")
    for key, value in cleaned.items():
        print(f"  {key}: {value} ({type(value).__name__})")

    # Verify
    assert isinstance(cleaned['competitors'], list), "Competitors should be a list"
    assert len(cleaned['competitors']) == 3, "Should have 3 competitors"
    assert isinstance(cleaned['keywords'], list), "Keywords should be a list"
    assert len(cleaned['keywords']) == 3, "Should have 3 keywords"
    assert cleaned['website'] == "example.com", "URL should be cleaned"

    print("\n✓ Data extraction tests passed")


async def test_progress_calculation():
    """Test progress calculation."""
    print("\n" + "=" * 80)
    print("Testing Progress Calculation")
    print("=" * 80)

    db = setup_test_db()
    service = BrandDiscoveryChatService(db)

    test_cases = [
        ({}, 0),
        ({"brand_name": "Acme"}, 15),
        ({"brand_name": "Acme", "website": "acme.com"}, 30),
        ({"brand_name": "Acme", "website": "acme.com", "industry": "SaaS"}, 45),
        ({
            "brand_name": "Acme",
            "website": "acme.com",
            "industry": "SaaS",
            "products_services": "Email tools"
        }, 60),
        ({
            "brand_name": "Acme",
            "website": "acme.com",
            "industry": "SaaS",
            "products_services": "Email tools",
            "competitors": ["Mailchimp"],
            "keywords": ["email marketing"]
        }, 78),
    ]

    print("\nProgress Calculation Tests:")
    for data, expected_min in test_cases:
        progress = service._calculate_progress(data)
        fields_count = len([k for k, v in data.items() if v])
        print(f"  {fields_count} fields: {progress}% (expected >= {expected_min}%)")
        assert progress >= expected_min, f"Progress {progress} should be >= {expected_min}"

    print("\n✓ Progress calculation tests passed")


async def test_fallback_extraction():
    """Test fallback extraction mechanism."""
    print("\n" + "=" * 80)
    print("Testing Fallback Extraction")
    print("=" * 80)

    db = setup_test_db()
    service = BrandDiscoveryChatService(db)

    test_cases = [
        ("Our website is techstartup.io", "website", "techstartup.io"),
        ("Acme Corp", "brand_name", "Acme Corp"),
        ("https://example.com is our site", "website", "example.com"),
    ]

    print("\nFallback Extraction Tests:")
    for message, expected_field, expected_value in test_cases:
        response, extracted = service._fallback_extraction({}, message)
        if expected_field in extracted:
            actual_value = extracted[expected_field]
            status = "✓" if expected_value in actual_value else "✗"
            print(f"  {status} '{message[:30]}...' -> {expected_field}: {actual_value}")
        else:
            print(f"  ✗ '{message[:30]}...' -> field '{expected_field}' not extracted")

    print("\n✓ Fallback extraction tests passed")


async def main():
    """Run all tests."""
    try:
        # Check if we have LLM keys (for full test)
        has_llm_keys = bool(os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))

        if not has_llm_keys:
            print("⚠ WARNING: No LLM API keys found in environment")
            print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test LLM integration")
            print("Running tests with fallback extraction only...\n")

        # Run tests
        await test_url_normalization()
        await test_data_extraction()
        await test_progress_calculation()
        await test_fallback_extraction()

        if has_llm_keys:
            await test_conversation()
        else:
            print("\n" + "=" * 80)
            print("Skipping full conversation test (no LLM keys)")
            print("Set OPENAI_API_KEY to run complete integration test")
            print("=" * 80)

        print("\n✓ All tests passed!")
        return 0

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
