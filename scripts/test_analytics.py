"""
Test Google Analytics 4 Integration

This script tests the connection to Google Analytics Data API using the service account.
"""
import os
import json
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SERVICE_ACCOUNT_KEY_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_PATH")
PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")

def get_analytics_client():
    """Create and return an authorized GA4 client."""
    if not SERVICE_ACCOUNT_KEY_PATH or not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
        raise FileNotFoundError(
            f"Service account key file not found at {SERVICE_ACCOUNT_KEY_PATH}. "
            "Please set GOOGLE_SERVICE_ACCOUNT_KEY_PATH in your .env file."
        )
    
    if not PROPERTY_ID:
        raise ValueError(
            "GA4_PROPERTY_ID not set in .env file. "
            "Please set it to your GA4 property ID (starts with 'G-')."
        )
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_KEY_PATH,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )
        return BetaAnalyticsDataClient(credentials=credentials)
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Analytics: {str(e)}")

def test_analytics_connection(client):
    """Test connection to GA4 and retrieve basic metrics."""
    try:
        request = RunReportRequest(
            property=f"properties/{PROPERTY_ID}",
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="screenPageViews")
            ],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            limit=5
        )
        
        response = client.run_report(request)
        return response
    except Exception as e:
        raise Exception(f"Failed to fetch analytics data: {str(e)}")

def main():
    print("📊 Testing Google Analytics 4 Integration")
    print("=" * 50)
    
    try:
        # Create client
        print("\n🔑 Authenticating with Google Analytics 4...")
        client = get_analytics_client()
        print("✅ Successfully authenticated")
        
        # Test connection
        print(f"\n📈 Fetching analytics data for property {PROPERTY_ID}...")
        response = test_analytics_connection(client)
        
        # Print results
        print(f"\n📊 Report result:")
        print(f"Date range: {response.date_ranges[0].start_date} to {response.date_ranges[0].end_date}")
        print(f"\nDimensions:")
        for dim in response.dimension_headers:
            print(f"- {dim.name}")
        
        print("\nMetrics:")
        for metric in response.metric_headers:
            print(f"- {metric.name}")
        
        if response.row_count > 0:
            print(f"\nSample data (showing {min(3, response.row_count)} of {response.row_count} rows):")
            for i, row in enumerate(response.rows[:3]):
                print(f"\nRow {i+1}:")
                for j, dim_value in enumerate(row.dimension_values):
                    print(f"  {response.dimension_headers[j].name}: {dim_value.value}")
                for j, metric_value in enumerate(row.metric_values):
                    print(f"  {response.metric_headers[j].name}: {metric_value.value}")
        else:
            print("\nℹ️  No data available for the specified date range")
        
        print("\n✅ Google Analytics 4 integration test completed")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
