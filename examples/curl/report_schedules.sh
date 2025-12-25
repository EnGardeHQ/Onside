#!/bin/bash

# Capilytics API - cURL Report Schedules Examples

BASE_URL="${CAPILYTICS_API_URL:-http://localhost:8000/api/v1}"

# Load token from file or login
if [ -f .token ]; then
  TOKEN=$(cat .token)
else
  echo "Token not found. Please run authentication.sh first."
  exit 1
fi

echo "=== Capilytics API Report Schedules Examples ==="
echo

# Example 1: Create report schedule
echo "1. Creating weekly report schedule..."
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/report-schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "name": "Weekly Competitor Report",
    "description": "Automated weekly competitor analysis",
    "report_type": "competitor_analysis",
    "cron_expression": "0 9 * * MON",
    "parameters": {
      "competitors": [1, 2, 3],
      "metrics": ["traffic", "engagement", "seo"]
    },
    "email_recipients": ["team@company.com"],
    "notify_on_completion": true
  }')

SCHEDULE_ID=$(echo $CREATE_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo "Created schedule ID: $SCHEDULE_ID"
echo "Response: $CREATE_RESPONSE"
echo

# Example 2: List report schedules
echo "2. Listing active report schedules..."
curl -s -X GET "$BASE_URL/report-schedules?is_active=true&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo

# Example 3: Get schedule details
echo "3. Getting schedule details..."
curl -s -X GET "$BASE_URL/report-schedules/$SCHEDULE_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo

# Example 4: Update schedule
echo "4. Updating schedule..."
UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/report-schedules/$SCHEDULE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Weekly Report",
    "cron_expression": "0 10 * * MON"
  }')

echo "Response: $UPDATE_RESPONSE"
echo

# Example 5: Pause schedule
echo "5. Pausing schedule..."
curl -s -X POST "$BASE_URL/report-schedules/$SCHEDULE_ID/pause" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo

# Example 6: Resume schedule
echo "6. Resuming schedule..."
curl -s -X POST "$BASE_URL/report-schedules/$SCHEDULE_ID/resume" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo

# Example 7: Get execution history
echo "7. Getting execution history..."
curl -s -X GET "$BASE_URL/report-schedules/$SCHEDULE_ID/executions?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo

# Example 8: Get statistics
echo "8. Getting execution statistics..."
curl -s -X GET "$BASE_URL/report-schedules/$SCHEDULE_ID/stats" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo

# Example 9: Delete schedule
echo "9. Deleting schedule..."
curl -s -X DELETE "$BASE_URL/report-schedules/$SCHEDULE_ID" \
  -H "Authorization: Bearer $TOKEN"

echo "Schedule deleted"
