# OnSide SEO Service Setup Guide

This guide will walk you through setting up the OnSide SEO Service, including Google Search Console integration, Google Analytics 4 setup, and database configuration.

## Prerequisites

1. Python 3.8+
2. PostgreSQL 13+
3. Google Cloud Project with billing enabled
4. Owner or Editor permissions on the Google Cloud Project
5. Access to Google Search Console and Google Analytics 4

## Setup Instructions

### 1. Database Setup

1. **Create the database** (if not already created):
   ```bash
   createdb onside
   ```

2. **Run the database migrations**:
   ```bash
   python scripts/setup_database.py
   ```

3. **Set up SEO database tables**:
   ```bash
   python scripts/setup_seo_database.py
   ```

4. **Verify the database setup**:
   ```bash
   python scripts/test_seo_database.py
   ```

### 2. Google Cloud Setup

1. **Install required Python packages**:
   ```bash
   pip install -r scripts/requirements.txt
   ```

2. **Set up OAuth 2.0 credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Name it "OnSide SEO Service"
   - Download the JSON file and save it as `config/secrets/credentials.json`

3. **Run the Google Cloud setup script**:
   ```bash
   python scripts/setup_google_cloud.py
   ```
   - This will:
     1. Create a service account
     2. Generate and save a service account key
     3. Enable necessary APIs

4. **Grant permissions**:
   - **Google Search Console**:
     1. Go to [Google Search Console](https://search.google.com/search-console)
     2. Select your property
     3. Click on "Settings" (gear icon) > "Users and permissions"
     4. Add the service account email with "Owner" permissions
   
   - **Google Analytics 4**:
     1. Go to [Google Analytics](https://analytics.google.com/)
     2. Click on "Admin" (gear icon)
     3. Under "Account" or "Property", click "Access Management"
     4. Add the service account email with "Viewer" or "Editor" role

### 3. Environment Configuration

Create or update your `.env` file with the following variables:

```
# Database
DATABASE_URL=postgresql+asyncpg://tobymorning@localhost:5432/onside

# Google Cloud
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project-id.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=config/secrets/onside-seo-service-account.json

# Google Search Console
SEARCH_CONSOLE_PROPERTY=sc-domain:yourdomain.com  # or http(s)://yourdomain.com

# Google Analytics 4
GA4_PROPERTY_ID=G-XXXXXXXXXX
```

### 4. Testing the Integration

1. **Test Google Search Console integration**:
   ```bash
   python scripts/test_search_console.py
   ```

2. **Test Google Analytics 4 integration**:
   ```bash
   python scripts/test_analytics.py
   ```

3. **Test database integration**:
   ```bash
   python scripts/test_seo_database.py
   ```

## Troubleshooting

### Service Account Permissions
- If you get permission errors, make sure the service account has been added to both Search Console and Analytics with the correct permissions.
- It may take a few minutes for permissions to propagate.

### Database Connection Issues
- Ensure PostgreSQL is running and the database exists
- Verify the database user has the correct permissions
- Check the connection string in your `.env` file

### API Quota Limits
- Google APIs have quota limits. If you hit limits, you may need to:
  - Request higher quotas in Google Cloud Console
  - Implement retry logic with exponential backoff
  - Cache responses when possible

## Next Steps

1. **Implement the main SEO service** using the provided database schema
2. **Set up scheduled jobs** for regular data collection
3. **Create API endpoints** for accessing the SEO data
4. **Build dashboards** to visualize the data

## Security Notes

- Never commit the `config/secrets` directory to version control
- Use environment variables for all sensitive information
- Rotate service account keys regularly
- Follow the principle of least privilege when granting permissions
