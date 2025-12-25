# Quick Reference: Backend Enhancements

**Quick Start Guide for Developers**

---

## 📁 New Files

```
/Users/cope/EnGardeHQ/Onside/
├── src/
│   ├── services/
│   │   ├── serp_analyzer.py                     # SERP API Integration (685 lines)
│   │   └── engarde_integration/
│   │       ├── __init__.py
│   │       └── data_transformer.py              # Data Transformation (820 lines)
│   └── api/v1/
│       └── websockets.py                         # WebSocket Progress (415 lines)
└── requirements.txt                              # +2 dependencies
```

---

## 🚀 Quick Setup

```bash
# 1. Install dependencies
pip install serpapi==0.1.5 websockets==12.0

# 2. Set environment variable
echo "SERPAPI_KEY=your_key_here" >> .env

# 3. Restart API server
docker-compose restart api
```

---

## 🔑 Environment Variables

```bash
# Required for production
SERPAPI_KEY=your_serpapi_key_here

# Optional (defaults)
SERP_RATE_LIMIT_REQUESTS=5
SERP_RATE_LIMIT_WINDOW=1.0
CACHE_TTL_SERP_RESULTS=86400
```

---

## 📡 API Endpoints

### WebSocket
```
WS /api/v1/ws/brand-analysis/{job_id}
GET /api/v1/ws/health
```

### Existing (Enhanced)
```
POST /api/v1/engarde/brand-analysis/initiate
GET /api/v1/engarde/brand-analysis/{job_id}/status
GET /api/v1/engarde/brand-analysis/{job_id}/results
POST /api/v1/engarde/brand-analysis/{job_id}/confirm
```

---

## 💻 Code Examples

### 1. SERP Analysis
```python
from src.services.serp_analyzer import SerpAnalyzer

async with SerpAnalyzer() as analyzer:
    serp = await analyzer.get_serp_results("keyword")
    difficulty = analyzer.calculate_keyword_difficulty(serp)
    domains = analyzer.extract_domains_from_serp(serp)
    features = analyzer.identify_serp_features(serp)
```

### 2. WebSocket Progress (JS)
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/brand-analysis/job-id');
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'progress') {
        console.log(`${msg.progress}% - ${msg.current_step}`);
    }
};
```

### 3. Data Transformation
```python
from src.services.engarde_integration.data_transformer import EnGardeDataTransformer

transformer = EnGardeDataTransformer()
engarde_keywords = transformer.transform_keywords(onside_keywords)
validation = transformer.validate_transformed_data(engarde_keywords)
```

---

## 🔄 Integration Flow

```
1. User initiates brand analysis
   ↓
2. POST /api/v1/engarde/brand-analysis/initiate
   → Returns job_id
   ↓
3. Frontend connects to WebSocket
   WS /api/v1/ws/brand-analysis/{job_id}
   ↓
4. Backend runs SEOContentWalkerAgent.analyze_brand()
   ├─ Crawls website
   ├─ Extracts keywords
   ├─ Analyzes SERP (SerpAnalyzer)
   ├─ Identifies competitors
   └─ Generates content opportunities
   ↓
5. Real-time WebSocket progress updates
   ├─ broadcast_progress()
   ├─ broadcast_step_complete()
   └─ broadcast_completion()
   ↓
6. GET /api/v1/engarde/brand-analysis/{job_id}/results
   ↓
7. Transform data (EnGardeDataTransformer)
   ↓
8. POST /api/v1/engarde/brand-analysis/{job_id}/confirm
```

---

## 📊 WebSocket Message Types

### Progress
```json
{"type": "progress", "progress": 45, "current_step": "Analyzing..."}
```

### Step Complete
```json
{"type": "step_complete", "step_name": "SERP Analysis", "step_number": 3}
```

### Completion
```json
{"type": "completed", "success": true, "summary": {...}}
```

### Error
```json
{"type": "error", "error": "Message", "error_code": "CODE"}
```

---

## 🧪 Testing

### Manual Test SERP
```bash
python -c "
import asyncio
from src.services.serp_analyzer import quick_serp_analysis
result = asyncio.run(quick_serp_analysis('test keyword'))
print(result)
"
```

### Manual Test WebSocket
```bash
# Install wscat: npm install -g wscat
wscat -c ws://localhost:8000/api/v1/ws/brand-analysis/test-job-id
```

### Manual Test Transformation
```python
from src.services.engarde_integration.data_transformer import *

# Test keyword schema
keyword = OnsideKeywordSchema(
    keyword="test",
    source="website_content",
    relevance_score=0.85
)
transformer = EnGardeDataTransformer()
result = transformer.transform_keywords([keyword])
print(result[0].dict())
```

---

## 🐛 Troubleshooting

### SERP API not working
```bash
# Check API key
echo $SERPAPI_KEY

# Test API directly
curl "https://serpapi.com/search?q=test&api_key=$SERPAPI_KEY"

# Check logs
docker logs onside-api | grep -i serp
```

### WebSocket connection fails
```bash
# Check if endpoint registered
curl http://localhost:8000/api/v1/ws/health

# Check job exists
curl http://localhost:8000/api/v1/engarde/brand-analysis/{job_id}/status
```

### Data transformation errors
```python
# Check validation
transformer = EnGardeDataTransformer()
validation = transformer.validate_transformed_data(data)
print(validation['errors'])
print(validation['warnings'])
```

---

## 📈 Performance

| Operation | Time | Notes |
|-----------|------|-------|
| SERP request | 500-1500ms | SerpAPI dependent |
| Keyword transformation | <1ms | Per keyword |
| WebSocket message | <50ms | Local network |
| 20 keyword analysis | 4-10s | With rate limiting |

---

## 🔒 Security Notes

- WebSocket currently doesn't verify user ownership
- SERPAPI_KEY should be kept secret
- Rate limiting prevents abuse (5 req/sec)
- Cache prevents redundant API calls

---

## 📝 Key Classes

### SerpAnalyzer
```python
async with SerpAnalyzer(api_key, cache) as analyzer:
    # Methods
    await get_serp_results(keyword, location)
    extract_domains_from_serp(results)
    calculate_keyword_difficulty(results)
    await get_search_volume(keyword)
    identify_serp_features(results)
    await analyze_keyword_batch(keywords)
```

### EnGardeDataTransformer
```python
transformer = EnGardeDataTransformer()
# Methods
transform_keywords(onside_keywords) → List[EnGardeKeywordSchema]
transform_competitors(onside_competitors) → List[EnGardeCompetitorSchema]
transform_content_opportunities(opportunities) → List[EnGardeContentIdeaSchema]
validate_transformed_data(data) → Dict[validation_report]
get_transformation_stats() → Dict[stats]
```

### ConnectionManager (WebSocket)
```python
manager = ConnectionManager()
# Methods
await connect(websocket, job_id, user_id)
await disconnect(websocket)
await broadcast_to_job(job_id, message)
await send_heartbeat(websocket)
get_connection_count(job_id)
```

---

## 🎯 Next Actions

1. ✅ Add SERPAPI_KEY to environment
2. ✅ Install dependencies
3. ✅ Restart API server
4. ⏳ Test SERP integration
5. ⏳ Update frontend to use WebSocket
6. ⏳ Add JWT auth to WebSocket
7. ⏳ Write integration tests

---

**For full documentation, see:** `CRITICAL_BACKEND_ENHANCEMENTS_COMPLETE.md`
