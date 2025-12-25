# cURL Examples for Capilytics API

This directory contains bash scripts with cURL examples for the Capilytics API.

## Prerequisites

- bash shell
- curl (installed by default on most systems)
- jq (for JSON formatting, optional but recommended)

Install jq:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# CentOS/RHEL
sudo yum install jq
```

## Usage

1. **Make scripts executable:**
```bash
chmod +x *.sh
```

2. **Set environment variables (optional):**
```bash
export CAPILYTICS_API_URL="http://localhost:8000/api/v1"
```

3. **Run authentication first:**
```bash
./authentication.sh
```

This will save your authentication token to `.token` file for use by other scripts.

4. **Run other examples:**
```bash
./report_schedules.sh
./seo_services.sh
```

## Available Examples

- **authentication.sh** - User registration, login, logout
- **report_schedules.sh** - Create, update, manage report schedules
- **seo_services.sh** - Google search, YouTube analytics, brand mentions

## Direct cURL Commands

### Quick Authentication
```bash
# Login and save token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo $TOKEN
```

### Use Token in Requests
```bash
# List report schedules
curl -X GET "http://localhost:8000/api/v1/report-schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

## Notes

- Token expires after 24 hours
- Re-run `authentication.sh` to refresh your token
- The `.token` file is gitignored for security
