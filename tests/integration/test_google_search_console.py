import os
import pytest
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SERVICE_ACCOUNT_EMAIL = os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL')
SERVICE_ACCOUNT_KEY_PATH = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')

@pytest.fixture(scope='module')
def search_console_service():
    """Create an authenticated Google Search Console service."""
    if not all([SERVICE_ACCOUNT_EMAIL, SERVICE_ACCOUNT_KEY_PATH]):
        pytest.skip("Missing Google Search Console credentials")
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_KEY_PATH,
            scopes=['https://www.googleapis.com/auth/webmasters.readonly'],
            subject=None  # Use service account email as subject
        )
        service = build('searchconsole', 'v1', credentials=credentials)
        return service
    except Exception as e:
        pytest.skip(f"Failed to create Search Console service: {str(e)}")

def test_search_console_connection(search_console_service):
    """Test that we can connect to Google Search Console API."""
    try:
        # Try to list sites to verify authentication
        sites = search_console_service.sites().list().execute()
        assert 'siteEntry' in sites, "Failed to fetch site list"
        print(f"Found {len(sites.get('siteEntry', []))} sites in Search Console")
        
        # Print the list of sites for verification
        for site in sites.get('siteEntry', []):
            print(f"Site: {site.get('siteUrl')} - Permission: {site.get('permissionLevel')}")
            
    except Exception as e:
        pytest.fail(f"Failed to connect to Search Console: {str(e)}")

def test_get_search_analytics(search_console_service):
    """Test fetching search analytics data."""
    try:
        # Use the first verified site for testing
        sites = search_console_service.sites().list().execute()
        verified_sites = [s for s in sites.get('siteEntry', []) 
                         if s.get('permissionLevel') == 'siteOwner']
        
        if not verified_sites:
            pytest.skip("No verified sites found in Search Console")
            
        site_url = verified_sites[0]['siteUrl']
        print(f"\nTesting search analytics for: {site_url}")
        
        # Prepare the request
        request = {
            'startDate': '2024-04-21',  # 30 days ago
            'endDate': '2024-05-21',    # Today
            'dimensions': ['query', 'page'],
            'rowLimit': 10
        }
        
        # Execute the request
        response = search_console_service.searchanalytics().query(
            siteUrl=site_url,
            body=request
        ).execute()
        
        # Check and print results
        rows = response.get('rows', [])
        print(f"Found {len(rows)} rows of search analytics data")
        
        if rows:
            print("\nSample data:")
            for i, row in enumerate(rows[:3]):  # Print first 3 rows
                keys = row.get('keys', [])
                clicks = row.get('clicks', 0)
                impressions = row.get('impressions', 0)
                ctr = row.get('ctr', 0) * 100
                position = row.get('position', 0)
                
                print(f"\nRow {i+1}:")
                print(f"  Query: {keys[0] if len(keys) > 0 else 'N/A'}")
                print(f"  Page: {keys[1] if len(keys) > 1 else 'N/A'}")
                print(f"  Clicks: {clicks}")
                print(f"  Impressions: {impressions}")
                print(f"  CTR: {ctr:.2f}%")
                print(f"  Position: {position:.1f}")
        
        assert 'rows' in response, "No data returned from Search Analytics API"
        
    except Exception as e:
        pytest.fail(f"Failed to fetch search analytics: {str(e)}")
