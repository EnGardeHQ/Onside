# En Garde Integration Guide

Complete integration guide for exporting Onside brand analysis results into En Garde's campaign import system.

## Overview

Onside provides **brand digital footprint analysis** that discovers:
- Keywords your brand should target
- Competitors in your market
- Content opportunities and gaps

En Garde provides **campaign management** with:
- Campaign spaces for organizing marketing assets
- CSV import for bulk data upload
- Platform integrations for ad networks

This integration connects the two systems, allowing you to seamlessly flow from brand analysis to campaign execution.

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ONSIDE WORKFLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User completes Setup Wizard questionnaire              │
│     ↓                                                       │
│  2. Onside analyzes brand digital footprint                │
│     ↓                                                       │
│  3. Results stored in Onside DB:                           │
│     - discovered_keywords                                   │
│     - identified_competitors                                │
│     - content_opportunities                                 │
│     ↓                                                       │
│  4. User reviews results in frontend                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  INTEGRATION LAYER                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Option A: CSV Export                                       │
│  GET /engarde/brand-analysis/{job_id}/export/csv           │
│     → Returns downloadable CSV file                         │
│                                                             │
│  Option B: Campaign JSON Export                             │
│  GET /engarde/brand-analysis/{job_id}/export/campaign      │
│     → Returns campaign-formatted JSON                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   EN GARDE IMPORT                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Option A1: Manual CSV Upload                               │
│  - User downloads CSV                                       │
│  - User uploads via En Garde CSV import page               │
│                                                             │
│  Option B1: Create New Campaign                             │
│  POST /campaign-spaces                                      │
│  - Creates campaign space with all analysis results        │
│                                                             │
│  Option B2: Add to Existing Campaign                        │
│  POST /campaign-spaces/{id}/assets/import                   │
│  - Adds analysis results to existing campaign              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. Export to CSV Format

**Endpoint:** `GET /engarde/brand-analysis/{job_id}/export/csv`

**Description:** Export all analysis results to CSV format compatible with En Garde's CSV import system.

**Parameters:**
- `job_id` (path): UUID of the completed brand analysis job

**Response:** CSV file download with headers:
```
type,keyword,domain,topic,source,search_volume,difficulty,relevance_score,priority,current_ranking,category,traffic_potential,gap_type,recommended_format,overlap_percentage,metadata
```

**Example:**
```bash
curl -X GET "https://api.onside.com/engarde/brand-analysis/550e8400-e29b-41d4-a716-446655440000/export/csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output analysis_results.csv
```

**Use Cases:**
- Manual review before import
- Archival/backup of analysis results
- Integration with external tools
- Batch import via CSV upload UI

---

### 2. Export to Campaign Format

**Endpoint:** `GET /engarde/brand-analysis/{job_id}/export/campaign`

**Description:** Export analysis results in En Garde campaign format for direct API import.

**Parameters:**
- `job_id` (path): UUID of the completed brand analysis job

**Response:** JSON object matching En Garde's campaign schema

**Example:**
```bash
curl -X GET "https://api.onside.com/engarde/brand-analysis/550e8400-e29b-41d4-a716-446655440000/export/campaign" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response Structure:**
```json
{
  "campaign_name": "Brand Analysis - {brand_name}",
  "platform": "onside_analysis",
  "import_source": "onside_brand_analysis",
  "description": "Automated brand digital footprint analysis",
  "campaign_objective": "Brand digital footprint analysis and SEO strategy",
  "keywords": [...],
  "competitors": [...],
  "content_opportunities": [...],
  "import_metadata": {
    "onside_job_id": "...",
    "analysis_date": "...",
    "brand_name": "...",
    "brand_website": "..."
  }
}
```

---

### 3. Confirm with Export (Enhanced)

**Endpoint:** `POST /engarde/brand-analysis/{job_id}/confirm`

**Description:** Confirm and import selected items, OR export to CSV/JSON format.

**Request Body:**
```json
{
  "selected_keywords": [123, 124, 125],
  "selected_competitors": [456, 457],
  "selected_opportunities": [789],
  "tenant_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "import_strategy": "skip",
  "export_format": null  // NEW: "csv", "campaign_json", or null
}
```

**Parameters:**
- `export_format` (optional):
  - `null` (default): Import to En Garde database
  - `"csv"`: Return CSV download
  - `"campaign_json"`: Return campaign JSON format

**Example - Export to CSV:**
```javascript
const response = await fetch('/engarde/brand-analysis/{job_id}/confirm', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    selected_keywords: [123, 124, 125],
    export_format: 'csv'
  })
});

// Response is CSV file download
const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'selected_analysis_results.csv';
a.click();
```

---

## Frontend Integration

### Setup Wizard Completion Flow

After the user reviews analysis results in the Setup Wizard, present three options:

```tsx
// After analysis completes and user reviews results
const handleAnalysisComplete = async (jobId: string, selectedItems: SelectedItems) => {
  // Option 1: Create New Campaign
  const createCampaign = async () => {
    // Get campaign-formatted data
    const campaignData = await fetch(
      `/engarde/brand-analysis/${jobId}/export/campaign`
    ).then(r => r.json());

    // Create campaign in En Garde
    const response = await fetch('/campaign-spaces', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...campaignData,
        tenant_id: currentTenant.id,
        user_id: currentUser.id
      })
    });

    const newCampaign = await response.json();

    // Redirect to new campaign
    router.push(`/campaign-spaces/${newCampaign.id}`);
  };

  // Option 2: Download CSV
  const downloadCSV = async () => {
    const response = await fetch(
      `/engarde/brand-analysis/${jobId}/export/csv`
    );

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `brand_analysis_${jobId}.csv`;
    a.click();

    // Show success toast
    toast({
      title: 'CSV Downloaded',
      description: 'Upload via En Garde CSV import page',
      status: 'success'
    });
  };

  // Option 3: Add to Existing Campaign
  const addToExistingCampaign = async (campaignId: string) => {
    // Get campaign-formatted data
    const campaignData = await fetch(
      `/engarde/brand-analysis/${jobId}/export/campaign`
    ).then(r => r.json());

    // Import into existing campaign
    const response = await fetch(
      `/campaign-spaces/${campaignId}/assets/import`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform_config: {
            source: 'onside_analysis',
            data: campaignData
          },
          tenant_id: currentTenant.id,
          user_id: currentUser.id
        })
      }
    );

    // Redirect to campaign
    router.push(`/campaign-spaces/${campaignId}`);
  };

  // Show options modal
  return (
    <Modal>
      <ModalBody>
        <VStack spacing={4}>
          <Button onClick={createCampaign} colorScheme="purple">
            Create New Campaign
          </Button>
          <Button onClick={downloadCSV} variant="outline">
            Download CSV
          </Button>
          <Button onClick={() => setShowCampaignSelector(true)} variant="outline">
            Add to Existing Campaign
          </Button>
        </VStack>
      </ModalBody>
    </Modal>
  );
};
```

---

## CSV Format Specification

### Headers

```
type,keyword,domain,topic,source,search_volume,difficulty,relevance_score,priority,current_ranking,category,traffic_potential,gap_type,recommended_format,overlap_percentage,metadata
```

### Row Types

**Type: `keyword`**
- `keyword`: The keyword phrase
- `source`: nlp_extraction, website_content, serp_analysis
- `search_volume`: Monthly search volume
- `difficulty`: SEO difficulty (0-100)
- `relevance_score`: Relevance to brand (0-1)
- `priority`: high, medium, low
- `current_ranking`: Current SERP position (if ranking)
- `category`: Source category

**Type: `competitor`**
- `domain`: Competitor domain
- `source`: competitor_analysis
- `relevance_score`: Market relevance (0-1)
- `priority`: high, medium, low
- `category`: primary, secondary, emerging, niche
- `overlap_percentage`: Keyword overlap percentage
- `metadata`: Additional info (name, confirmed status)

**Type: `content_opportunity`**
- `topic`: Content topic/title
- `source`: content_gap_analysis
- `difficulty`: Content difficulty (0-100)
- `priority`: high, medium, low
- `traffic_potential`: Estimated monthly traffic
- `gap_type`: missing_content, weak_content, competitor_strength
- `recommended_format`: blog, guide, video, infographic

### Example CSV

See `/examples/export_example.csv`

---

## Campaign JSON Format Specification

### Schema

```typescript
interface CampaignExport {
  campaign_name: string;
  platform: "onside_analysis";
  import_source: "onside_brand_analysis";
  description: string;
  campaign_objective: string;
  target_audience: string[];
  is_active: boolean;
  tags: string[];
  category: string;
  import_metadata: {
    onside_job_id: string;
    analysis_date: string;
    brand_name: string;
    brand_website: string;
    industry: string;
    questionnaire: object;
    total_keywords: number;
    total_competitors: number;
    total_opportunities: number;
  };
  keywords: EnGardeKeyword[];
  competitors: EnGardeCompetitor[];
  content_opportunities: EnGardeContentIdea[];
  currency: string;
  budget: number | null;
}
```

### Keyword Schema (EnGardeKeyword)

```typescript
interface EnGardeKeyword {
  keyword_text: string;
  search_volume: number | null;
  competition_score: number | null;
  cpc_estimate: string | null;  // Decimal as string
  current_position: number | null;
  target_position: number | null;
  priority_level: "high" | "medium" | "low";
  category: string | null;
  intent_type: "informational" | "navigational" | "transactional" | "commercial" | null;
  metadata: {
    onside_id: number;
    relevance_score: number;
    serp_features: object | null;
    confirmed: boolean;
    transformation_date: string;
  };
  source: "onside_analysis";
  created_at: string;
  updated_at: string;
}
```

### Competitor Schema (EnGardeCompetitor)

```typescript
interface EnGardeCompetitor {
  competitor_name: string;
  domain: string;
  competitor_type: "direct" | "indirect" | "aspirational" | "emerging";
  market_share: number | null;
  strength_score: number | null;
  keyword_overlap_count: number | null;
  shared_keywords: string[] | null;
  competitive_advantages: string[] | null;
  weaknesses: string[] | null;
  monitoring_enabled: boolean;
  metadata: {
    onside_id: number;
    relevance_score: number;
    category: string;
    overlap_percentage: number | null;
    confirmed: boolean;
    transformation_date: string;
  };
  source: "onside_analysis";
  created_at: string;
  updated_at: string;
}
```

### Content Opportunity Schema (EnGardeContentIdea)

```typescript
interface EnGardeContentIdea {
  title: string;
  description: string | null;
  content_type: "blog_post" | "guide" | "video" | "infographic" | "case_study" | "whitepaper";
  priority: "high" | "medium" | "low";
  estimated_traffic: number | null;
  difficulty_score: number | null;
  target_keywords: string[] | null;
  target_audience: string | null;
  content_gap: string | null;
  competitor_coverage: boolean | null;
  status: "idea" | "planned" | "in_progress" | "published";
  metadata: {
    onside_id: number;
    topic: string;
    gap_type: string;
    recommended_format: string;
    transformation_date: string;
  };
  source: "onside_analysis";
  created_at: string;
  updated_at: string;
}
```

### Example JSON

See `/examples/export_example.json`

---

## Data Transformation

Onside data is automatically transformed to En Garde format using `EnGardeDataTransformer`.

### Keyword Transformation

**Onside → En Garde Mappings:**
- `keyword` → `keyword_text`
- `difficulty` → `competition_score`
- `search_volume` → `search_volume` (unchanged)
- `current_ranking` → `current_position`
- `relevance_score` → stored in metadata

**Enrichments Applied:**
- **CPC Estimate**: Calculated from search volume + difficulty
- **Intent Type**: Inferred from keyword text patterns
- **Priority Level**: Calculated from search volume + difficulty + relevance
- **Target Position**: Calculated from current position

### Competitor Transformation

**Onside → En Garde Mappings:**
- `domain` → `domain` (unchanged)
- `name` → `competitor_name`
- `category` → `competitor_type` (with mapping)
- `relevance_score` → `strength_score` (normalized to 0-100)
- `overlap_percentage` → stored in metadata

**Category Mappings:**
- primary → direct
- secondary → indirect
- emerging → emerging
- niche → indirect

### Content Opportunity Transformation

**Onside → En Garde Mappings:**
- `topic` → `title`
- `gap_type` → `content_gap`
- `recommended_format` → `content_type` (with mapping)
- `traffic_potential` → `estimated_traffic`
- `difficulty` → `difficulty_score`
- `priority` → `priority` (unchanged)

**Format Mappings:**
- blog → blog_post
- guide → guide
- video → video
- infographic → infographic
- case_study → case_study
- whitepaper → whitepaper

---

## En Garde Import Endpoints

### Create Campaign Space

**Endpoint:** `POST /campaign-spaces`

**Request Body:**
```json
{
  "campaign_name": "Brand Analysis - Acme Corp",
  "platform": "onside_analysis",
  "import_source": "onside_brand_analysis",
  "tenant_id": "tenant-uuid",
  "user_id": "user-uuid",
  "description": "...",
  "keywords": [...],
  "competitors": [...],
  "import_metadata": {...}
}
```

**Response:**
```json
{
  "success": true,
  "id": "campaign-uuid",
  "campaign_name": "Brand Analysis - Acme Corp",
  "created_at": "2025-12-24T10:45:30.000000"
}
```

### Import Assets to Existing Campaign

**Endpoint:** `POST /campaign-spaces/{campaign_id}/assets/import`

**Request Body:**
```json
{
  "platform_config": {
    "source": "onside_analysis",
    "data": {
      "keywords": [...],
      "competitors": [...],
      "content_opportunities": [...]
    }
  },
  "tenant_id": "tenant-uuid",
  "user_id": "user-uuid"
}
```

---

## Error Handling

### Common Errors

**400 Bad Request - Analysis Not Complete**
```json
{
  "detail": "Analysis is not complete. Current status: analyzing"
}
```
**Solution:** Wait for analysis to complete before exporting

**404 Not Found - Job Not Found**
```json
{
  "detail": "Analysis job not found"
}
```
**Solution:** Verify job_id is correct and belongs to authenticated user

**401 Unauthorized**
```json
{
  "detail": "Unauthorized - Invalid or missing authentication token"
}
```
**Solution:** Include valid authentication token in request headers

---

## Testing

### Test CSV Export

```bash
# 1. Create test analysis job
curl -X POST "https://api.onside.com/engarde/brand-analysis/initiate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "Test Brand",
    "primary_website": "https://testbrand.com",
    "industry": "Technology"
  }'

# 2. Wait for completion (poll status endpoint)
# ...

# 3. Export to CSV
curl -X GET "https://api.onside.com/engarde/brand-analysis/{job_id}/export/csv" \
  -H "Authorization: Bearer $TOKEN" \
  --output test_export.csv

# 4. Verify CSV format
head -n 3 test_export.csv
```

### Test Campaign Export

```bash
# Export to campaign format
curl -X GET "https://api.onside.com/engarde/brand-analysis/{job_id}/export/campaign" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Create campaign in En Garde
curl -X POST "https://api.engarde.com/campaign-spaces" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @campaign_export.json
```

---

## Production Deployment

### Environment Variables

```bash
# Onside Backend
ENGARDE_API_URL=https://api.engarde.com
ENGARDE_API_KEY=your_api_key_here

# En Garde Backend
ONSIDE_WEBHOOK_URL=https://api.onside.com/webhooks
ONSIDE_API_KEY=your_api_key_here
```

### Database Considerations

- Onside and En Garde use **separate databases**
- Integration uses **API-based data transfer** (not direct DB access)
- Import batches tracked in Onside DB for audit trail
- En Garde stores final campaign data

### Security

- All endpoints require **authentication tokens**
- Export endpoints validate **user ownership** of analysis jobs
- Import endpoints enforce **tenant isolation**
- Sensitive data sanitized before export

---

## Troubleshooting

### CSV Import Fails in En Garde

**Issue:** CSV format not recognized

**Solution:**
1. Verify CSV headers match expected format
2. Check for encoding issues (should be UTF-8)
3. Ensure no special characters in data values
4. Validate with example CSV in `/examples/export_example.csv`

### Campaign Creation Fails

**Issue:** Invalid platform or import_source

**Solution:**
- Ensure `platform: "onside_analysis"` is added to En Garde's allowed platforms
- Add `import_source: "onside_brand_analysis"` to allowed sources
- Update En Garde's validation schemas to accept Onside exports

### Missing Data in Export

**Issue:** Keywords/competitors not appearing in export

**Solution:**
1. Verify analysis job completed successfully
2. Check that items exist in Onside database
3. Confirm user has permission to access job
4. Review transformation logs for errors

---

## Support

For integration questions or issues:

- **Onside Documentation**: `/docs/api`
- **En Garde Documentation**: `https://engarde.com/docs/api`
- **Integration Examples**: `/examples/`
- **Support Email**: support@onside.com
