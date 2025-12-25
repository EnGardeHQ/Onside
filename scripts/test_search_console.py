"""
Test Google Search Console Integration

This script tests the connection to Google Search Console API using the service account.
"""
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SERVICE_ACCOUNT_KEY_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_PATH")
SERVICE_ACCOUNT_EMAIL = os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL")
PROPERTY_URL = os.getenv("SEARCH_CONSOLE_PROPERTY")

def authenticate():
    """Authenticate with Google Search Console API."""
    if not SERVICE_ACCOUNT_KEY_PATH or not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
        raise FileNotFoundError(
            f"Service account key file not found at {SERVICE_ACCOUNT_KEY_PATH}. "
            "Please set GOOGLE_SERVICE_ACCOUNT_KEY_PATH in your .env file."
        )
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_KEY_PATH,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
        )
        return build('searchconsole', 'v1', credentials=credentials)
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Search Console: {str(e)}")

def list_sites(service):
    """List all sites in Google Search Console."""
    try:
        sites = service.sites().list().execute()
        return sites.get('siteEntry', [])
    except HttpError as e:
        raise Exception(f"Failed to list sites: {e}")

def get_search_analytics(service, site_url):
    """Get search analytics data for a site."""
    try:
        request = {
            'startDate': '2024-04-21',  # 30 days ago
            'endDate': '2024-05-21',    # Today
            'dimensions': ['query', 'page'],
            'rowLimit': 10
        }
        
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request
        ).execute()
        
        return response.get('rows', [])
    except HttpError as e:
        raise Exception(f"Failed to get search analytics: {e}")

def main():
    print("🔍 Testing Google Search Console Integration")
    print("=" * 50)
    
    try:
        # Authenticate
        print("\n🔑 Authenticating with Google Search Console...")
        service = authenticate()
        print("✅ Successfully authenticated")
        
        # List sites
        print("\n🌐 Listing available sites...")
        sites = list_sites(service)
        
        if not sites:
            print("ℹ️  No sites found in Google Search Console")
            return
        
        print("\nAvailable sites:")
        for i, site in enumerate(sites, 1):
            print(f"{i}. {site['siteUrl']} ({site.get('permissionLevel', 'Unknown permission')})")
        
        # Test search analytics
        test_site = None
        if PROPERTY_URL:
            test_site = next((s for s in sites if s['siteUrl'] == PROPERTY_URL), None)
            if test_site:
                print(f"\n🔎 Testing search analytics for {PROPERTY_URL}...")
                try:
                    analytics = get_search_analytics(service, test_site['siteUrl'])
                    if analytics:
                        print(f"✅ Successfully retrieved {len(analytics)} rows of search analytics data")
                        print("\nSample data:")
                        for i, row in enumerate(analytics[:3]):  # Show first 3 rows
                            keys = row.get('keys', ['N/A', 'N/A'])
                            print(f"\nRow {i+1}:")
                            print(f"  Query: {keys[0]}")
                            print(f"  Page: {keys[1]}")
                            print(f"  Clicks: {row.get('clicks', 0)}")
                            print(f"  Impressions: {row.get('impressions', 0)}")
                            print(f"  CTR: {row.get('ctr', 0) * 100:.2f}%")
                            print(f"  Position: {row.get('position', 0):.1f}")
                    else:
                        print("ℹ️  No search analytics data available for this property")
                except Exception as e:
                    print(f"⚠️  Error getting search analytics: {e}")
            else:
                print(f"ℹ️  Property {PROPERTY_URL} not found in your Search Console")
        else:
            print("\nℹ️  SEARCH_CONSOLE_PROPERTY not set in .env file")
        
        print("\n✅ Google Search Console integration test completed")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
