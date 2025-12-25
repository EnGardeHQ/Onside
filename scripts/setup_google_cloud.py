"""
Google Cloud Setup Script for OnSide SEO Service

This script automates the creation of a Google Cloud service account
and sets up the necessary permissions for Google Search Console and Analytics.
"""
import os
import json
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
SERVICE_ACCOUNT_NAME = "onside-seo-service"
SERVICE_ACCOUNT_DISPLAY_NAME = "OnSide SEO Service Account"
SERVICE_ACCOUNT_DESCRIPTION = "Service account for OnSide SEO Service"
SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly"
]
PROJECT_ID = "high-hue-459604-i1"  # From your existing service account email
SERVICE_ACCOUNT_EMAIL = f"{SERVICE_ACCOUNT_NAME}@{PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE_PATH = "config/secrets/onside-seo-service-account.json"
CREDENTIALS_FILE = "config/secrets/credentials.json"
TOKEN_FILE = "config/secrets/token.pickle"

class GoogleCloudSetup:
    def __init__(self):
        self.credentials = None
        self.service = None
        self.iam_service = None
        self.project_id = PROJECT_ID
        
    def get_oauth2_credentials(self) -> Credentials:
        """Gets OAuth2 credentials for the service account."""
        creds = None
        
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"Error: OAuth2 credentials not found at {CREDENTS_FILE}")
                    print("Please download your OAuth2 credentials from Google Cloud Console")
                    print("1. Go to https://console.cloud.google.com/apis/credentials")
                    print("2. Click 'Create Credentials' > 'OAuth client ID'")
                    print("3. Select 'Desktop app' as the application type")
                    print(f"4. Save the JSON file as {CREDENTIALS_FILE}")
                    sys.exit(1)
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE,
                    ["https://www.googleapis.com/auth/cloud-platform"]
                )
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)
        
        return creds
    
    def create_service_account(self) -> Dict[str, Any]:
        """Creates a service account."""
        try:
            service_account = self.iam_service.projects().serviceAccounts().create(
                name=f"projects/{self.project_id}",
                body={
                    "accountId": SERVICE_ACCOUNT_NAME,
                    "serviceAccount": {
                        "displayName": SERVICE_ACCOUNT_DISPLAY_NAME,
                        "description": SERVICE_ACCOUNT_DESCRIPTION
                    }
                }
            ).execute()
            print(f"✅ Created service account: {service_account['email']}")
            return service_account
        except HttpError as error:
            if error.resp.status == 409:
                print(f"ℹ️  Service account {SERVICE_ACCOUNT_NAME} already exists")
                return {"email": SERVICE_ACCOUNT_EMAIL}
            print(f"❌ Error creating service account: {error}")
            raise
    
    def create_service_account_key(self, service_account_email: str) -> Dict[str, Any]:
        """Creates a key for a service account."""
        try:
            key = self.iam_service.projects().serviceAccounts().keys().create(
                name=f"projects/-/serviceAccounts/{service_account_email}",
                body={}
            ).execute()
            print("✅ Created service account key")
            return key
        except HttpError as error:
            print(f"❌ Error creating service account key: {error}")
            raise
    
    def enable_apis(self) -> None:
        """Enables necessary APIs for the project."""
        service = build("serviceusage", "v1", credentials=self.credentials)
        services = [
            "searchconsole.googleapis.com",
            "analyticsdata.googleapis.com",
            "analyticsadmin.googleapis.com"
        ]
        
        for service_name in services:
            try:
                service.services().enable(
                    name=f"projects/{self.project_id}/services/{service_name}"
                ).execute()
                print(f"✅ Enabled {service_name}")
            except HttpError as e:
                print(f"⚠️  Error enabling {service_name}: {e}")
    
    def setup(self) -> None:
        """Main setup function."""
        print("🚀 Starting Google Cloud setup for OnSide SEO Service")
        print("=" * 50)
        
        # Create the secrets directory if it doesn't exist
        os.makedirs("config/secrets", exist_ok=True)
        
        # Check if we already have a service account key
        if os.path.exists(KEY_FILE_PATH):
            print(f"ℹ️  Service account key already exists at {KEY_FILE_PATH}")
            print("   Delete it if you want to generate a new key.")
            return
        
        try:
            # Get OAuth2 credentials
            print("\n🔑 Getting OAuth2 credentials...")
            self.credentials = self.get_oauth2_credentials()
            
            # Create IAM service
            print("\n🔧 Setting up IAM service...")
            self.iam_service = build("iam", "v1", credentials=self.credentials)
            
            # Create service account
            print("\n👤 Creating service account...")
            service_account = self.create_service_account()
            
            # Create and save key
            print("\n🔑 Creating service account key...")
            key = self.create_service_account_key(service_account["email"])
            
            # Save the key to a file
            key_data = key["privateKeyData"]
            key_json = json.loads(key_data)
            
            with open(KEY_FILE_PATH, "w") as f:
                json.dump(key_json, f, indent=2)
            
            # Set secure permissions on the key file
            os.chmod(KEY_FILE_PATH, 0o600)
            
            print(f"\n✅ Service account key saved to {KEY_FILE_PATH}")
            
            # Enable necessary APIs
            print("\n⚙️  Enabling necessary APIs...")
            self.enable_apis()
            
            # Print next steps
            print("\n" + "=" * 50)
            print("🎉 Google Cloud setup completed successfully!")
            print("\nNext steps:")
            print(f"1. Add {service_account['email']} as an owner to your Google Search Console properties")
            print("   - Go to https://search.google.com/search-console")
            print("   - Select your property")
            print("   - Click on 'Settings' (gear icon) > 'Users and permissions'")
            print(f"   - Add {service_account['email']} with 'Owner' permissions")
            print("\n2. Add the service account to your Google Analytics 4 properties")
            print("   - Go to https://analytics.google.com/")
            print("   - Click on 'Admin' (gear icon)")
            print("   - Under 'Account' or 'Property', click 'Access Management'")
            print(f"   - Add {service_account['email']} with 'Viewer' or 'Editor' role")
            
            print("\n3. Update your .env file with the following:")
            print(f"   GOOGLE_SERVICE_ACCOUNT_EMAIL={service_account['email']}")
            print(f"   GOOGLE_SERVICE_ACCOUNT_KEY_PATH={os.path.abspath(KEY_FILE_PATH)}")
            print(f"   SEARCH_CONSOLE_PROPERTY=sc-domain:yourdomain.com  # Replace with your domain")
            print(f"   GA4_PROPERTY_ID=G-XXXXXXXXXX  # Replace with your GA4 property ID")
            
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            # Clean up if there was an error
            if os.path.exists(KEY_FILE_PATH):
                os.remove(KEY_FILE_PATH)
                print(f"Removed partially created key file: {KEY_FILE_PATH}")
            sys.exit(1)

if __name__ == "__main__":
    setup = GoogleCloudSetup()
    setup.setup()
