# Capilytics API Examples

This directory contains code examples in multiple programming languages for interacting with the Capilytics API.

## Directory Structure

```
examples/
├── python/              # Python examples
│   ├── authentication.py
│   ├── report_schedules.py
│   └── web_scraping.py
├── javascript/          # JavaScript/Node.js examples
│   ├── authentication.js
│   ├── seo_services.js
│   └── package.json
└── curl/               # Bash/cURL examples
    ├── authentication.sh
    ├── report_schedules.sh
    ├── seo_services.sh
    └── README.md
```

## Quick Start

### Python Examples

**Requirements:**
```bash
pip install requests python-dotenv
```

**Usage:**
```bash
cd python/
python authentication.py
python report_schedules.py
python web_scraping.py
```

### JavaScript Examples

**Requirements:**
```bash
cd javascript/
npm install
```

**Usage:**
```bash
node authentication.js
node seo_services.js
```

### cURL Examples

**Requirements:**
- bash
- curl
- jq (optional, for JSON formatting)

**Usage:**
```bash
cd curl/
chmod +x *.sh
./authentication.sh
./report_schedules.sh
./seo_services.sh
```

## Environment Variables

Set these environment variables for all examples:

```bash
export CAPILYTICS_API_URL="http://localhost:8000/api/v1"
export CAPILYTICS_EMAIL="user@example.com"
export CAPILYTICS_PASSWORD="SecurePassword123!"
```

Or create a `.env` file in the root directory:

```env
CAPILYTICS_API_URL=http://localhost:8000/api/v1
CAPILYTICS_EMAIL=user@example.com
CAPILYTICS_PASSWORD=SecurePassword123!
```

## Available Examples

### Authentication
- User registration
- Login and token management
- User profile retrieval
- Logout

### Report Schedules
- Create automated report schedules
- List and filter schedules
- Update schedule configuration
- Pause/resume schedules
- View execution history and statistics

### Web Scraping
- Initiate website scraping
- List scraped content
- View content versions
- Compare content changes
- Create scraping schedules

### SEO Services
- Google Custom Search
- Brand mention tracking
- Content performance analysis
- YouTube video search
- Channel and video analytics

## Code Examples

### Python: Quick Authentication

```python
from authentication import CapilyticsAuthClient

# Login
client = CapilyticsAuthClient()
client.login('user@example.com', 'password')

# Check authentication
if client.is_authenticated():
    print("Successfully authenticated!")

# Use headers in requests
headers = client.get_headers()
```

### JavaScript: Quick Authentication

```javascript
const CapilyticsAuthClient = require('./authentication');

async function main() {
  const client = new CapilyticsAuthClient();
  await client.login('user@example.com', 'password');

  if (client.isAuthenticated()) {
    console.log('Successfully authenticated!');
  }

  const headers = client.getHeaders();
}
```

### cURL: Quick Authentication

```bash
# Login and save token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Use token in requests
curl -X GET http://localhost:8000/api/v1/report-schedules \
  -H "Authorization: Bearer $TOKEN"
```

## Additional Resources

- **API Reference:** [API_REFERENCE.md](../API_REFERENCE.md)
- **Usage Guide:** [API_USAGE_GUIDE.md](../API_USAGE_GUIDE.md)
- **Postman Collection:** [POSTMAN_COLLECTION.json](../POSTMAN_COLLECTION.json)

## Support

For questions or issues, please contact: support@capilytics.com
