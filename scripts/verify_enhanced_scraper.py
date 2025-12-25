#!/usr/bin/env python3
"""Verification script for Enhanced Web Scraping Service.

This script verifies that the enhanced web scraping service is properly
installed and configured.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def verify_installation():
    """Verify that the enhanced scraper is properly installed."""
    print("=" * 60)
    print("Enhanced Web Scraping Service - Verification")
    print("=" * 60)
    print()

    # 1. Verify imports
    print("1. Verifying imports...")
    try:
        from src.services.web_scraping import (
            EnhancedWebScrapingService,
            ScrapingConfig,
            ScrapedPage,
            CompetitorProfile,
            BacklinkData,
            ContentAnalysis,
            CircuitBreakerError,
            ScrapingError,
        )
        print("   ✓ All imports successful")
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False

    # 2. Verify configuration
    print("\n2. Verifying configuration...")
    try:
        from src.config.scraping_config import get_scraping_config, SCRAPING_CONFIG_OPTIONS
        config = get_scraping_config()
        print(f"   ✓ Configuration loaded")
        print(f"   - Max concurrent: {config.max_concurrent}")
        print(f"   - Throttle delay: {config.throttle_delay}s")
        print(f"   - NLP enabled: {config.enable_nlp}")
        print(f"   - Total config options: {len(SCRAPING_CONFIG_OPTIONS)}")
    except Exception as e:
        print(f"   ✗ Configuration failed: {e}")
        return False

    # 3. Verify service initialization
    print("\n3. Verifying service initialization...")
    try:
        config = ScrapingConfig(
            default_timeout=5,
            max_retries=1,
            respect_robots_txt=False,
            throttle_delay=0.1,
        )
        scraper = EnhancedWebScrapingService(config=config)
        print("   ✓ Service initialized successfully")
        await scraper.close()
    except Exception as e:
        print(f"   ✗ Service initialization failed: {e}")
        return False

    # 4. Verify integration with SEO Agent
    print("\n4. Verifying SEO Agent integration...")
    try:
        from src.agents.seo_content_walker import SEOContentWalkerAgent
        print("   ✓ SEO Agent can be imported")
        # Check that agent has enhanced scraper methods
        assert hasattr(SEOContentWalkerAgent, 'scrape_competitor_profiles')
        assert hasattr(SEOContentWalkerAgent, 'analyze_competitor_content')
        assert hasattr(SEOContentWalkerAgent, 'discover_competitor_backlinks')
        print("   ✓ Enhanced scraper methods present in SEO Agent")
    except Exception as e:
        print(f"   ✗ SEO Agent integration failed: {e}")
        return False

    # 5. Verify dependencies
    print("\n5. Verifying dependencies...")
    dependencies = {
        'aiohttp': 'aiohttp',
        'beautifulsoup4': 'bs4',
        'playwright': 'playwright',
        'tenacity': 'tenacity',
        'textblob': 'textblob',
        'nltk': 'nltk',
        'scikit-learn': 'sklearn',
    }

    missing_deps = []
    for dep_name, import_name in dependencies.items():
        try:
            __import__(import_name)
            print(f"   ✓ {dep_name}")
        except ImportError:
            print(f"   ✗ {dep_name} (MISSING)")
            missing_deps.append(dep_name)

    if missing_deps:
        print(f"\n   WARNING: {len(missing_deps)} dependencies missing: {', '.join(missing_deps)}")
        print("   Install with: pip install -r requirements.txt")

    # 6. Verify test suite
    print("\n6. Verifying test suite...")
    try:
        test_file = Path(__file__).parent.parent / "tests" / "services" / "test_enhanced_web_scraper.py"
        if test_file.exists():
            lines = len(test_file.read_text().splitlines())
            print(f"   ✓ Test file exists ({lines} lines)")
        else:
            print("   ✗ Test file not found")
            return False
    except Exception as e:
        print(f"   ✗ Test verification failed: {e}")

    # 7. Quick functional test
    print("\n7. Running quick functional test...")
    try:
        config = ScrapingConfig(
            default_timeout=5,
            max_retries=1,
            respect_robots_txt=False,
            throttle_delay=0.1,
            enable_nlp=False,  # Disable NLP for speed
        )

        async with EnhancedWebScrapingService(config=config) as scraper:
            # Test circuit breaker
            scraper._record_failure("test-domain.com")
            assert scraper.circuit_breakers["test-domain.com"].failure_count == 1

            scraper._record_success("test-domain.com")
            assert scraper.circuit_breakers["test-domain.com"].failure_count == 0

            print("   ✓ Circuit breaker works correctly")

            # Test user agent rotation
            ua1 = scraper._get_random_user_agent()
            assert isinstance(ua1, str)
            assert len(ua1) > 0
            print("   ✓ User agent rotation works")

            # Test content extraction helpers
            from src.services.web_scraping.enhanced_scraper import ScrapedPage
            test_page = ScrapedPage(
                url="https://test.com",
                html="",
                text="Test content with info@test.com and (555) 123-4567",
                title="Test",
                meta_description="",
                meta_keywords="",
                headings={},
                links=["https://twitter.com/test", "https://linkedin.com/company/test"],
                images=[],
                status_code=200,
                response_time_ms=100,
            )

            contact = scraper._extract_contact_info(test_page)
            assert 'email' in contact
            assert contact['email'] == 'info@test.com'
            print("   ✓ Contact extraction works")

            social = scraper._extract_social_links(test_page)
            assert 'twitter' in social
            assert 'linkedin' in social
            print("   ✓ Social link extraction works")

            # Test syllable counting
            syllables = scraper._count_syllables("testing")
            assert syllables >= 1
            print("   ✓ Syllable counting works")

            # Test keyword density
            density = scraper._calculate_keyword_density("python python code", top_n=5)
            assert 'python' in density
            print("   ✓ Keyword density calculation works")

    except Exception as e:
        print(f"   ✗ Functional test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✓ All verifications passed!")
    print("=" * 60)
    print("\nEnhanced Web Scraping Service is ready to use.")
    print("\nQuick start:")
    print("  from src.services.web_scraping import EnhancedWebScrapingService")
    print("  scraper = EnhancedWebScrapingService()")
    print("  page = await scraper.scrape_with_javascript('https://example.com')")
    print("\nFor more information, see:")
    print("  - /Users/cope/EnGardeHQ/Onside/src/services/web_scraping/README.md")
    print("  - /Users/cope/EnGardeHQ/ENHANCED_WEB_SCRAPING_IMPLEMENTATION.md")
    print()

    return True


if __name__ == "__main__":
    success = asyncio.run(verify_installation())
    sys.exit(0 if success else 1)
