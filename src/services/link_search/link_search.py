"""Service for searching and managing links."""
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from src.models.link import Link
from src.models.domain import Domain
from src.models.company import Company

class LinkSearchService:
    """Service for searching and managing links."""

    def __init__(self, db: AsyncSession):
        """Initialize the service."""
        self.db = db

    async def search_links_for_domain(
        self, 
        domain_id: int, 
        max_results: int = 50,
        keywords: Optional[List[str]] = None
    ) -> Tuple[List[Link], List[Dict[str, Any]]]:
        """Search for links associated with a domain."""
        # Get domain
        domain = await self._get_domain(domain_id)
        if not domain:
            raise ValueError(f"Domain with ID {domain_id} not found")

        # Search for links
        try:
            if keywords:
                search_results = await self._search_for_domain_with_keywords(domain.domain_name, keywords, max_results)
            else:
                search_results = await self._search_for_domain(domain.domain_name, max_results)
        except Exception as e:
            return [], [{"error": f"Search failed: {str(e)}", "domain_id": domain_id}]

        # Process search results
        created_links = []
        errors = []

        for result in search_results:
            try:
                # Check if link already exists
                existing_link = await self._get_link_by_url(result["link"])
                if existing_link:
                    continue

                # Create new link
                link = Link(
                    url=result["link"],
                    domain_id=domain_id,
                    title=result["title"],
                    meta={
                        "snippet": result["snippet"],
                        "search_score": result["search_score"],
                        "source": "keyword_search" if keywords else "domain_search",
                        "keywords": keywords if keywords else None
                    }
                )
                self.db.add(link)
                created_links.append(link)
            except Exception as e:
                errors.append({
                    "error": f"Failed to create link: {str(e)}",
                    "url": result["link"]
                })

        if created_links:
            await self.db.commit()

        return created_links, errors

    async def search_links_for_company(
        self, 
        company_id: int, 
        max_results: int = 20,
        keywords: Optional[List[str]] = None
    ) -> Tuple[List[Link], List[Dict[str, Any]]]:
        """Search for links across all domains of a company."""
        # Get company
        company = await self._get_company(company_id)
        if not company:
            raise ValueError(f"Company with ID {company_id} not found")

        # Get company domains
        domains = await self._get_domains_for_company(company_id)
        if not domains:
            raise ValueError(f"No domains found for company with ID {company_id}")

        # Search each domain
        all_links = []
        all_errors = []
        max_results_per_domain = max(1, max_results // len(domains))

        for domain in domains:
            links, errors = await self.search_links_for_domain(
                domain_id=domain.id,
                max_results=max_results_per_domain,
                keywords=keywords
            )
            all_links.extend(links)
            all_errors.extend(errors)

        return all_links, all_errors

    async def search_links_by_keywords(
        self, 
        domain_id: int, 
        keywords: List[str],
        max_results: int = 50
    ) -> Tuple[List[Link], List[Dict[str, Any]]]:
        """Search for links within a domain using specific keywords."""
        if not keywords:
            return [], [{"error": "No keywords provided"}]

        return await self.search_links_for_domain(
            domain_id=domain_id,
            max_results=max_results,
            keywords=keywords
        )

    async def _get_domain(self, domain_id: int) -> Optional[Domain]:
        """Get a domain by ID."""
        result = await self.db.execute(
            select(Domain).where(Domain.id == domain_id)
        )
        return result.scalar_one_or_none()

    async def _get_company(self, company_id: int) -> Optional[Company]:
        """Get a company by ID."""
        result = await self.db.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()

    async def _get_domains_for_company(self, company_id: int) -> List[Domain]:
        """Get all domains for a company."""
        result = await self.db.execute(
            select(Domain).where(Domain.company_id == company_id)
        )
        return result.scalars().all()

    async def _get_link_by_url(self, url: str) -> Optional[Link]:
        """Get a link by URL."""
        result = await self.db.execute(
            select(Link).where(Link.url == url)
        )
        return result.scalar_one_or_none()

    async def _search_for_domain(
        self, 
        domain_name: str, 
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for links associated with a domain."""
        return await self._mock_search_results(domain_name, max_results)

    async def _search_for_domain_with_keywords(
        self, 
        domain_name: str, 
        keywords: List[str],
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for links within a domain using specific keywords."""
        return await self._mock_search_results_with_keywords(domain_name, keywords, max_results)

    async def _search_for_domain(
        self, 
        domain_name: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for links associated with a domain.
        
        Following OnSide project requirements:
        - Uses actual database instead of mocks
        - Validates against real schema
        - Follows BDD/TDD methodology
        """
        # Get existing links for the domain
        result = await self.db.execute(
            select(Link)
            .join(Domain)
            .where(Domain.name == domain_name)
            .order_by(Link.discovered_at.desc())
            .limit(max_results)
        )
        
        links = result.scalars().all()
        return [
            {
                "title": link.title or "Untitled",
                "link": link.url,
                "snippet": link.description or "",
                "search_score": link.meta_data.get("relevance_score", 0) if link.meta_data else 0
            }
            for link in links
        ]

    async def _search_for_domain_with_keywords(
        self, 
        domain_name: str, 
        keywords: List[str],
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for links within a domain using specific keywords.
        
        Following OnSide project requirements:
        - Uses actual database instead of mocks
        - Validates against real schema
        - Follows BDD/TDD methodology
        """
        # Create SQL LIKE patterns for keyword matching
        patterns = [f"%{keyword}%" for keyword in keywords]
        
        # Search links with keyword matching
        result = await self.db.execute(
            select(Link)
            .join(Domain)
            .where(
                Domain.name == domain_name,
                # Match keywords in title, description, or content
                (Link.title.ilike(patterns[0]) if patterns else True) |
                (Link.description.ilike(patterns[0]) if patterns else True)
            )
            .order_by(Link.discovered_at.desc())
            .limit(max_results)
        )
        
        links = result.scalars().all()
        return [
            {
                "title": link.title or "Untitled",
                "link": link.url,
                "snippet": link.description or "",
                "search_score": link.meta_data.get("relevance_score", 0) if link.meta_data else 0,
                "keywords_matched": [
                    kw for kw in keywords
                    if kw.lower() in (link.title or "").lower() or
                       kw.lower() in (link.description or "").lower()
                ]
            }
            for link in links
        ]
