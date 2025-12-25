# Google Cloud Setup Scripts

This directory contains scripts to set up and configure Google Cloud services for the OnSide SEO Service.

## Prerequisites

1. Python 3.8+
2. Google Cloud SDK installed and configured
3. A Google Cloud Project with billing enabled
4. Owner or Editor permissions on the Google Cloud Project

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements-setup.txt
   ```

2. **Enable Required APIs**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Select your project
   - Enable the following APIs:
     - Google Search Console API
     - Google Analytics Data API
     - Google Analytics Admin API
     - Identity and Access Management (IAM) API
     - Service Usage API

3. **Create OAuth 2.0 Credentials**
   - Go to [Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Name it "OnSide SEO Service"
   - Download the JSON file and save it as `config/secrets/credentials.json`

4. **Run the Setup Script**
   ```bash
   python setup_google_cloud.py
   ```
   - This will:
     1. Create a new service account
     2. Generate and save a service account key
     3. Enable necessary APIs

5. **Grant Permissions**
   - Add the service account email to your Google Search Console properties as an "Owner"
   - Add the service account email to your Google Analytics 4 properties as a "Viewer" or "Editor"

## Environment Variables

After running the setup script, update your `.env` file with the following variables:

```
# Google Cloud
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project-id.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=config/secrets/onside-seo-service-account.json

# Google Search Console
SEARCH_CONSOLE_PROPERTY=sc-domain:yourdomain.com  # or http(s)://yourdomain.com

# Google Analytics 4
GA4_PROPERTY_ID=G-XXXXXXXXXX
```

## Security Notes

- Never commit the `config/secrets` directory to version control
- Add `config/secrets/` to your `.gitignore` file
- Rotate service account keys regularly
- Follow the principle of least privilege when granting permissions
