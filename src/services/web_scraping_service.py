"""Web scraping service with Playwright for comprehensive content extraction.

This module provides advanced web scraping capabilities including:
- HTML content extraction
- Screenshot capture
- Version tracking and diff comparison
- Change detection
- Storage integration with MinIO
"""
import logging
import hashlib
import difflib
from typing import Dict, Optional, Any, List
from datetime import datetime
from urllib.parse import urlparse
import asyncio

from playwright.async_api import async_playwright, Page, Browser
from sqlalchemy.orm import Session

from src.models.scraped_content import ScrapedContent, ContentChange
from src.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class WebScrapingError(Exception):
    """Exception raised for web scraping errors."""
    pass


class WebScrapingService:
    """Service for web scraping with Playwright and content tracking.

    Provides comprehensive web scraping with screenshot capture,
    content versioning, and change detection.
    """

    def __init__(self, storage_service: Optional[StorageService] = None):
        """Initialize the web scraping service.

        Args:
            storage_service: Storage service for saving screenshots
        """
        self.storage_service = storage_service or StorageService()
        self.browser: Optional[Browser] = None

    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

    async def scrape_url(
        self,
        url: str,
        db: Session,
        company_id: Optional[int] = None,
        competitor_id: Optional[int] = None,
        capture_screenshot: bool = True,
        wait_for_selector: Optional[str] = None,
        timeout: int = 30000
    ) -> ScrapedContent:
        """Scrape a URL and store content with versioning.

        Args:
            url: URL to scrape
            db: Database session
            company_id: Optional company ID
            competitor_id: Optional competitor ID
            capture_screenshot: Whether to capture screenshot
            wait_for_selector: Optional CSS selector to wait for
            timeout: Page load timeout in milliseconds

        Returns:
            ScrapedContent: Scraped content record

        Raises:
            WebScrapingError: If scraping fails
        """
        start_time = datetime.utcnow()

        try:
            await self._ensure_browser()

            # Create new browser page
            page = await self.browser.new_page()

            try:
                # Navigate to URL
                response = await page.goto(url, timeout=timeout, wait_until='networkidle')
                status_code = response.status if response else None

                # Wait for specific selector if provided
                if wait_for_selector:
                    await page.wait_for_selector(wait_for_selector, timeout=5000)

                # Extract content
                html_content = await page.content()
                title = await page.title()

                # Extract text content (remove scripts and styles)
                text_content = await page.evaluate('''() => {
                    const clone = document.cloneNode(true);
                    clone.querySelectorAll('script, style, noscript').forEach(el => el.remove());
                    return clone.body ? clone.body.innerText : '';
                }''')

                # Extract meta tags
                meta_description = await page.evaluate('''() => {
                    const meta = document.querySelector('meta[name="description"]');
                    return meta ? meta.getAttribute('content') : null;
                }''')

                meta_keywords = await page.evaluate('''() => {
                    const meta = document.querySelector('meta[name="keywords"]');
                    return meta ? meta.getAttribute('content') : null;
                }''')

                # Extract domain
                parsed_url = urlparse(url)
                domain = parsed_url.netloc

                # Check for existing versions
                latest_version = (
                    db.query(ScrapedContent)
                    .filter(ScrapedContent.url == url)
                    .order_by(ScrapedContent.version.desc())
                    .first()
                )

                version = (latest_version.version + 1) if latest_version else 1

                # Create scraped content record
                scraped = ScrapedContent(
                    url=url,
                    domain=domain,
                    company_id=company_id,
                    competitor_id=competitor_id,
                    version=version,
                    html_content=html_content,
                    text_content=text_content,
                    title=title,
                    meta_description=meta_description,
                    meta_keywords=meta_keywords,
                    status_code=status_code,
                    scrape_duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )

                # Calculate content hash
                scraped.update_hash()

                # Capture screenshot if requested
                if capture_screenshot:
                    screenshot_data = await page.screenshot(full_page=True)

                    # Upload to MinIO
                    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                    screenshot_filename = f"screenshots/{domain}/{timestamp}_{version}.png"

                    await self.storage_service.upload_file(
                        file_data=screenshot_data,
                        filename=screenshot_filename,
                        content_type='image/png'
                    )

                    scraped.screenshot_path = screenshot_filename
                    scraped.screenshot_url = f"/storage/{screenshot_filename}"

                # Add to database
                db.add(scraped)
                db.commit()
                db.refresh(scraped)

                # Check for changes if there's a previous version
                if latest_version:
                    await self._detect_changes(db, latest_version, scraped)

                logger.info(f"Successfully scraped {url} (version {version})")
                return scraped

            finally:
                await page.close()

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {str(e)}")

            # Create error record
            parsed_url = urlparse(url)
            error_scraped = ScrapedContent(
                url=url,
                domain=parsed_url.netloc,
                company_id=company_id,
                competitor_id=competitor_id,
                version=1,
                error_message=str(e),
                scrape_duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )

            db.add(error_scraped)
            db.commit()

            raise WebScrapingError(f"Scraping failed for {url}: {str(e)}")

    async def _detect_changes(
        self,
        db: Session,
        old_version: ScrapedContent,
        new_version: ScrapedContent
    ) -> Optional[ContentChange]:
        """Detect and record changes between content versions.

        Args:
            db: Database session
            old_version: Previous version
            new_version: New version

        Returns:
            ContentChange if changes detected, None otherwise
        """
        if not old_version.has_changed(new_version):
            logger.info(f"No content changes detected for {new_version.url}")
            return None

        # Calculate text diff
        old_text = old_version.text_content or ""
        new_text = new_version.text_content or ""

        # Calculate change percentage
        differ = difflib.SequenceMatcher(None, old_text, new_text)
        similarity = differ.ratio()
        change_percentage = (1 - similarity) * 100

        # Get detailed diff
        diff = list(difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            lineterm='',
            n=0  # No context lines
        ))

        # Count additions and deletions
        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        # Determine change type
        if abs(len(new_text) - len(old_text)) > len(old_text) * 0.5:
            change_type = "major"
        elif change_percentage > 20:
            change_type = "significant"
        else:
            change_type = "minor"

        # Create change record
        change = ContentChange(
            url=new_version.url,
            old_version_id=old_version.id,
            new_version_id=new_version.id,
            change_type=change_type,
            change_percentage=round(change_percentage, 2),
            change_summary=f"{additions} additions, {deletions} deletions",
            diff_data={
                'additions': additions,
                'deletions': deletions,
                'similarity': round(similarity, 4),
                'old_length': len(old_text),
                'new_length': len(new_text),
                'sample_diff': diff[:50]  # Store first 50 diff lines
            }
        )

        db.add(change)
        db.commit()

        logger.info(
            f"Change detected for {new_version.url}: "
            f"{change_percentage:.2f}% change ({change_type})"
        )

        return change

    async def scrape_multiple(
        self,
        urls: List[str],
        db: Session,
        **kwargs
    ) -> List[ScrapedContent]:
        """Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            db: Database session
            **kwargs: Additional arguments for scrape_url

        Returns:
            List of ScrapedContent records
        """
        tasks = [self.scrape_url(url, db, **kwargs) for url in urls]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        scraped_contents = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scrape {urls[i]}: {str(result)}")
            else:
                scraped_contents.append(result)

        return scraped_contents

    async def get_content_history(
        self,
        db: Session,
        url: str,
        limit: int = 10
    ) -> List[ScrapedContent]:
        """Get scraping history for a URL.

        Args:
            db: Database session
            url: URL to get history for
            limit: Maximum number of versions to return

        Returns:
            List of ScrapedContent records
        """
        return (
            db.query(ScrapedContent)
            .filter(ScrapedContent.url == url)
            .order_by(ScrapedContent.created_at.desc())
            .limit(limit)
            .all()
        )

    async def get_changes_for_url(
        self,
        db: Session,
        url: str,
        limit: int = 10
    ) -> List[ContentChange]:
        """Get change history for a URL.

        Args:
            db: Database session
            url: URL to get changes for
            limit: Maximum number of changes to return

        Returns:
            List of ContentChange records
        """
        return (
            db.query(ContentChange)
            .filter(ContentChange.url == url)
            .order_by(ContentChange.detected_at.desc())
            .limit(limit)
            .all()
        )

    async def compare_versions(
        self,
        db: Session,
        version_id_1: int,
        version_id_2: int
    ) -> Dict[str, Any]:
        """Compare two versions of scraped content.

        Args:
            db: Database session
            version_id_1: ID of first version
            version_id_2: ID of second version

        Returns:
            Dict containing comparison results
        """
        v1 = db.query(ScrapedContent).filter(ScrapedContent.id == version_id_1).first()
        v2 = db.query(ScrapedContent).filter(ScrapedContent.id == version_id_2).first()

        if not v1 or not v2:
            raise WebScrapingError("One or both versions not found")

        if v1.url != v2.url:
            raise WebScrapingError("Versions are for different URLs")

        # Calculate diff
        text1 = v1.text_content or ""
        text2 = v2.text_content or ""

        differ = difflib.SequenceMatcher(None, text1, text2)
        similarity = differ.ratio()

        # Get HTML diff
        html_differ = difflib.HtmlDiff()
        html_diff = html_differ.make_file(
            text1.splitlines(),
            text2.splitlines(),
            fromdesc=f"Version {v1.version} ({v1.created_at.isoformat()})",
            todesc=f"Version {v2.version} ({v2.created_at.isoformat()})"
        )

        return {
            'url': v1.url,
            'version1': {
                'id': v1.id,
                'version': v1.version,
                'created_at': v1.created_at.isoformat(),
                'content_hash': v1.content_hash,
                'length': len(text1)
            },
            'version2': {
                'id': v2.id,
                'version': v2.version,
                'created_at': v2.created_at.isoformat(),
                'content_hash': v2.content_hash,
                'length': len(text2)
            },
            'similarity': round(similarity, 4),
            'change_percentage': round((1 - similarity) * 100, 2),
            'html_diff': html_diff
        }

    async def close(self):
        """Close browser and cleanup resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
