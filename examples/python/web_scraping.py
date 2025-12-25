"""
Capilytics API - Python Web Scraping Examples
"""

import requests
import os
import time
from authentication import CapilyticsAuthClient

BASE_URL = os.getenv('CAPILYTICS_API_URL', 'http://localhost:8000/api/v1')


class WebScrapingClient:
    """Client for web scraping operations"""

    def __init__(self, auth_client):
        self.auth_client = auth_client
        self.base_url = auth_client.base_url

    def scrape_url(self, url, company_id=None, competitor_id=None,
                   capture_screenshot=True, wait_for_selector=None, timeout=30000):
        """Initiate scraping for a URL"""
        response = requests.post(
            f'{self.base_url}/scraping/scrape',
            headers=self.auth_client.get_headers(),
            json={
                'url': url,
                'company_id': company_id,
                'competitor_id': competitor_id,
                'capture_screenshot': capture_screenshot,
                'wait_for_selector': wait_for_selector,
                'timeout': timeout
            }
        )
        response.raise_for_status()
        return response.json()

    def list_content(self, company_id=None, competitor_id=None, domain=None,
                     page=1, page_size=20):
        """List scraped content"""
        params = {'page': page, 'page_size': page_size}

        if company_id:
            params['company_id'] = company_id
        if competitor_id:
            params['competitor_id'] = competitor_id
        if domain:
            params['domain'] = domain

        response = requests.get(
            f'{self.base_url}/scraping/content',
            headers=self.auth_client.get_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_content(self, content_id):
        """Get scraped content details including full HTML/text"""
        response = requests.get(
            f'{self.base_url}/scraping/content/{content_id}',
            headers=self.auth_client.get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_versions(self, content_id):
        """Get version history for content"""
        response = requests.get(
            f'{self.base_url}/scraping/content/{content_id}/versions',
            headers=self.auth_client.get_headers()
        )
        response.raise_for_status()
        return response.json()

    def compare_versions(self, content_id, compare_to_id):
        """Compare two versions of content"""
        response = requests.get(
            f'{self.base_url}/scraping/content/{content_id}/diff',
            headers=self.auth_client.get_headers(),
            params={'compare_to': compare_to_id}
        )
        response.raise_for_status()
        return response.json()

    def create_schedule(self, schedule_data):
        """Create a scraping schedule"""
        response = requests.post(
            f'{self.base_url}/scraping/schedules',
            headers=self.auth_client.get_headers(),
            json=schedule_data
        )
        response.raise_for_status()
        return response.json()

    def list_schedules(self, company_id=None, is_active=None, page=1, page_size=20):
        """List scraping schedules"""
        params = {'page': page, 'page_size': page_size}

        if company_id:
            params['company_id'] = company_id
        if is_active is not None:
            params['is_active'] = is_active

        response = requests.get(
            f'{self.base_url}/scraping/schedules',
            headers=self.auth_client.get_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()

    def delete_schedule(self, schedule_id):
        """Delete a scraping schedule"""
        response = requests.delete(
            f'{self.base_url}/scraping/schedules/{schedule_id}',
            headers=self.auth_client.get_headers()
        )
        response.raise_for_status()
        return True


# Example usage
if __name__ == '__main__':
    # Authenticate
    auth_client = CapilyticsAuthClient()
    auth_client.login(
        email=os.getenv('CAPILYTICS_EMAIL', 'user@example.com'),
        password=os.getenv('CAPILYTICS_PASSWORD', 'password')
    )

    # Initialize scraping client
    scraper = WebScrapingClient(auth_client)

    # Example 1: Scrape a competitor website
    print("Initiating web scraping...")
    result = scraper.scrape_url(
        url='https://competitor.com',
        company_id=1,
        competitor_id=1,
        capture_screenshot=True,
        wait_for_selector='#main-content'
    )
    print(f"Scraping initiated: {result['status']}")

    # Wait for scraping to complete
    print("Waiting for scraping to complete...")
    time.sleep(5)

    # Example 2: List scraped content
    print("\nListing scraped content...")
    content_list = scraper.list_content(competitor_id=1, page_size=5)
    print(f"Found {content_list['total']} scraped pages")

    if content_list['content']:
        latest_content = content_list['content'][0]
        print(f"\nLatest scraped page:")
        print(f"  URL: {latest_content['url']}")
        print(f"  Title: {latest_content['title']}")
        print(f"  Version: {latest_content['version']}")
        print(f"  Scraped: {latest_content['created_at']}")

        # Example 3: Get full content details
        print("\nGetting full content details...")
        details = scraper.get_content(latest_content['id'])
        print(f"Text content length: {len(details['text_content'])} characters")
        print(f"HTML content length: {len(details['html_content'])} characters")
        print(f"Meta description: {details.get('meta_description', 'N/A')}")

        # Example 4: Get version history
        print("\nGetting version history...")
        versions = scraper.get_versions(latest_content['id'])
        print(f"Found {len(versions)} versions")
        for v in versions[:3]:
            print(f"  - Version {v['version']}: {v['created_at']} "
                  f"(changes: {v['has_changes']})")

        # Example 5: Compare versions
        if len(versions) >= 2:
            print("\nComparing latest two versions...")
            diff = scraper.compare_versions(
                content_id=versions[0]['id'],
                compare_to_id=versions[1]['id']
            )
            print(f"Has changed: {diff['has_changed']}")
            if diff['has_changed']:
                print(f"Change percentage: {diff['change_percentage']:.2f}%")
                if diff['diff_summary']:
                    print(f"Summary: {diff['diff_summary']}")

    # Example 6: Create daily scraping schedule
    print("\nCreating daily scraping schedule...")
    schedule = scraper.create_schedule({
        'name': 'Daily Homepage Monitor',
        'url': 'https://competitor.com',
        'company_id': 1,
        'competitor_id': 1,
        'cron_expression': '0 8 * * *',  # Daily at 8 AM
        'capture_screenshot': True,
        'scraping_config': {
            'wait_for_selector': '#main-content',
            'timeout': 30000
        }
    })
    print(f"Created schedule ID: {schedule['id']}")

    # Example 7: List scraping schedules
    print("\nListing active scraping schedules...")
    schedules = scraper.list_schedules(is_active=True)
    print(f"Found {schedules['total']} active schedules")
    for s in schedules['schedules']:
        print(f"  - {s['name']}: {s['url']}")

    # Clean up: Delete schedule
    print(f"\nDeleting schedule {schedule['id']}...")
    scraper.delete_schedule(schedule['id'])
    print("Schedule deleted")
