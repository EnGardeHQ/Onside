#!/bin/bash

# Capilytics API - cURL SEO Services Examples

BASE_URL="${CAPILYTICS_API_URL:-http://localhost:8000/api/v1}"

# Load token from file or login
if [ -f .token ]; then
  TOKEN=$(cat .token)
else
  echo "Token not found. Please run authentication.sh first."
  exit 1
fi

echo "=== Capilytics API SEO Services Examples ==="
echo

# Example 1: Google Custom Search
echo "1. Performing Google search..."
curl -s -X POST "$BASE_URL/seo/google-search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "competitive intelligence tools",
    "max_results": 10,
    "language": "en",
    "date_restrict": "d7"
  }' | jq '.'
echo

# Example 2: Track brand mentions
echo "2. Tracking brand mentions..."
curl -s -X POST "$BASE_URL/seo/brand-mentions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "Capilytics",
    "keywords": ["analytics", "competitive intelligence"],
    "competitors": ["CompetitorA", "CompetitorB"],
    "date_restrict": "w1",
    "max_results": 50
  }' | jq '.'
echo

# Example 3: Analyze content performance
echo "3. Analyzing content performance..."
curl -s -X POST "$BASE_URL/seo/content-performance" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://mycompany.com/blog/article",
    "competitors": ["https://competitor1.com", "https://competitor2.com"],
    "metrics": ["ranking", "backlinks", "social_shares"]
  }' | jq '.'
echo

# Example 4: YouTube video search
echo "4. Searching YouTube videos..."
curl -s -X POST "$BASE_URL/seo/youtube/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "competitive analysis tutorial",
    "max_results": 5,
    "order": "relevance",
    "video_duration": "medium"
  }' | jq '.'
echo

# Example 5: Get YouTube channel stats
echo "5. Getting YouTube channel statistics..."
CHANNEL_ID="UCabc123xyz"
curl -s -X GET "$BASE_URL/seo/youtube/channel/$CHANNEL_ID/stats" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo

# Example 6: Get YouTube video analytics
echo "6. Getting video analytics..."
VIDEO_ID="abc123xyz"
curl -s -X GET "$BASE_URL/seo/youtube/video/$VIDEO_ID/analytics" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo

# Example 7: Track competitor videos
echo "7. Tracking competitor videos..."
COMPETITOR_ID=1
curl -s -X POST "$BASE_URL/seo/youtube/competitor/$COMPETITOR_ID/videos" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "UCcompetitor123",
    "max_videos": 20,
    "published_after": "2025-01-01T00:00:00Z"
  }' | jq '.'
echo
