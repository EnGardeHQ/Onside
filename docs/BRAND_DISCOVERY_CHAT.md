# Brand Discovery Chat - Natural Language Interface

## Overview

The Brand Discovery Chat is a conversational AI interface that replaces the traditional static questionnaire form in the En Garde Setup Wizard. It uses natural language processing to guide users through brand discovery in a friendly, conversational manner while extracting structured data for brand analysis.

## Features

### 1. Conversational Flow
- Natural, one-question-at-a-time dialogue
- Context-aware responses that acknowledge user input
- Handles multiple pieces of information in a single message
- Gracefully manages corrections and clarifications

### 2. Smart Data Extraction
- Automatic entity recognition (URLs, competitor names, keywords)
- URL normalization and validation
- List parsing from natural language (comma-separated, "and" conjunctions)
- Industry term mapping to standard categories

### 3. Progress Tracking
- Real-time completion percentage
- Weighted field importance (required vs. optional)
- Missing field identification
- Session state management

### 4. Resilience
- LLM failover with fallback providers (OpenAI → Anthropic)
- Rule-based extraction fallback when LLM unavailable
- Session recovery and continuation
- Comprehensive error handling

## Architecture

### Components

```
┌─────────────────────────────────────────────┐
│           Frontend (React/Vue)              │
│  - Chat UI component                        │
│  - Message history display                  │
│  - Progress indicator                       │
└─────────────────┬───────────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────────┐
│      API Layer (FastAPI)                    │
│  /brand-discovery-chat/*                    │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│   BrandDiscoveryChatService                 │
│  - Conversation management                  │
│  - Data extraction & validation             │
│  - Progress calculation                     │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼────────┐  ┌────────▼──────────┐
│  LLM Service   │  │  Database         │
│  - OpenAI      │  │  - Sessions       │
│  - Anthropic   │  │  - Messages       │
│  - Fallback    │  │  - Extracted Data │
└────────────────┘  └───────────────────┘
```

### Data Models

**BrandDiscoveryChatSession** (Database Table)
```python
{
    "session_id": UUID,
    "user_id": str,
    "messages": [
        {
            "role": "user|assistant",
            "content": str,
            "timestamp": datetime
        }
    ],
    "extracted_data": {
        "brand_name": str,
        "website": str,
        "industry": str,
        "products_services": str,
        "target_markets": [str],
        "target_audience": str,
        "competitors": [str],
        "marketing_goals": str,
        "keywords": [str]
    },
    "status": "active|completed|abandoned",
    "created_at": datetime,
    "updated_at": datetime
}
```

## API Endpoints

### Start Chat Session
```http
POST /brand-discovery-chat/start
Authorization: Bearer {token}

Response 201:
{
    "session_id": "uuid",
    "first_message": "Hi! I'm here to help you discover your brand's digital footprint..."
}
```

### Send Message
```http
POST /brand-discovery-chat/{session_id}/message
Authorization: Bearer {token}
Content-Type: application/json

{
    "message": "Acme Corporation"
}

Response 200:
{
    "ai_response": "Great! What's your primary website URL?",
    "progress_pct": 15,
    "extracted_data": {
        "brand_name": "Acme Corporation",
        "website": null,
        ...
    },
    "is_complete": false,
    "session_id": "uuid"
}
```

### Get Session Status
```http
GET /brand-discovery-chat/{session_id}/status
Authorization: Bearer {token}

Response 200:
{
    "session_id": "uuid",
    "progress_pct": 45,
    "extracted_data": {...},
    "missing_fields": ["industry", "products_services"],
    "is_complete": false,
    "status": "active"
}
```

### Finalize Session
```http
POST /brand-discovery-chat/{session_id}/finalize
Authorization: Bearer {token}

Response 200:
{
    "questionnaire": {
        "brand_name": "Acme Corporation",
        "website": "https://acmecorp.com",
        "industry": "SaaS/Email Marketing",
        "products_services": "Email automation and analytics",
        "competitors": ["Mailchimp", "Constant Contact"],
        "keywords": ["email marketing", "marketing automation"]
    },
    "analysis_job_id": "uuid",
    "message": "Brand discovery complete! Ready to analyze Acme Corporation."
}
```

### Get Session History
```http
GET /brand-discovery-chat/{session_id}/history
Authorization: Bearer {token}

Response 200:
{
    "session_id": "uuid",
    "user_id": "123",
    "status": "completed",
    "messages": [...],
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:45:00Z"
}
```

## Example Conversation Flow

### Happy Path - Complete Flow

```
AI: Hi! I'm here to help you discover your brand's digital footprint.
    Let's start with the basics - what's your brand or company name?

User: Acme Corporation

AI: Great! And what's your primary website URL?

User: acmecorp.com

AI: Perfect! What industry is Acme Corporation in?

User: We make email marketing software for small businesses

AI: Excellent - so SaaS/Email Marketing industry. Could you describe your
    products or services in a bit more detail?

User: Email automation, newsletter tools, and campaign analytics

AI: Fantastic! Who are your main competitors, if you know any?

User: Mailchimp and Constant Contact

AI: Got it! Any specific marketing goals or keywords you want to target?

User: email marketing, marketing automation, newsletter software

AI: Perfect! I have everything I need. Let me analyze Acme Corporation's
    digital footprint and competitive landscape.

[Session complete - 100% progress]
```

### Multiple Details at Once

```
AI: Hi! I'm here to help you discover your brand's digital footprint.
    Let's start with the basics - what's your brand or company name?

User: Hi, I'm setting up for DataViz Pro, we're at datavizpro.io and
      we do data visualization software

AI: Wonderful! I got that you're DataViz Pro (datavizpro.io) in the data
    visualization software space. What specific products or services do you offer?

User: Interactive dashboards, real-time analytics, and custom reporting tools

AI: Excellent! Who are your main competitors?

[Conversation continues...]
```

### Handling Corrections

```
AI: What's your website URL?

User: techstartup.com

AI: Great! What industry are you in?

User: Actually, the website is techstartup.co, not .com

AI: No problem, updated to techstartup.co. Now, what industry are you in?

User: B2B SaaS

[Conversation continues...]
```

### Clarification Needed

```
AI: What products or services does your company offer?

User: We sell stuff online

AI: Could you be more specific? What type of products or services do you offer?

User: Enterprise project management software with team collaboration features

AI: Perfect! So enterprise SaaS for project management. Who are your competitors?

[Conversation continues...]
```

## Data Extraction Rules

### Required Fields
1. **brand_name** (15% weight)
   - Company or brand name
   - Extracted from initial responses or explicit mentions

2. **website** (15% weight)
   - Primary website URL
   - Normalized: removes protocol, www, trailing slashes
   - Validated for proper domain format

3. **industry** (15% weight)
   - Business sector/category
   - Mapped to standard industry terms when possible
   - Can be extracted from descriptive responses

4. **products_services** (15% weight)
   - What the company offers
   - Can be detailed description
   - Extracted from natural language explanations

### Optional Fields
5. **target_markets** (8% weight)
   - Geographic markets (cities, regions, countries)
   - Stored as list
   - Split from comma-separated or natural language

6. **target_audience** (8% weight)
   - Customer demographics/psychographics
   - Free-form text description

7. **competitors** (12% weight)
   - Known competitors (domain names or company names)
   - Stored as list
   - Parsed from "X, Y, and Z" patterns

8. **marketing_goals** (6% weight)
   - SEO/marketing objectives
   - Free-form text

9. **keywords** (6% weight)
   - Target SEO keywords
   - Stored as list
   - Extracted from comma-separated lists

## Progress Calculation

Progress is calculated using weighted fields:

```python
Total Weight = 100 points

Required Fields (60 points):
- brand_name: 15 points
- website: 15 points
- industry: 15 points
- products_services: 15 points

Optional Fields (40 points):
- competitors: 12 points
- target_markets: 8 points
- target_audience: 8 points
- marketing_goals: 6 points
- keywords: 6 points

Progress % = (Earned Points / Total Points) × 100
```

## LLM Integration

### System Prompt
The service uses a comprehensive system prompt that:
- Defines the AI's role as a brand consultant
- Specifies conversation style (friendly, concise, one question at a time)
- Lists required and optional fields
- Provides extraction rules and normalization guidelines
- Includes few-shot examples

### Fallback Strategy
1. **Primary**: OpenAI GPT-4 with JSON mode
2. **Secondary**: Anthropic Claude with structured output
3. **Tertiary**: Rule-based extraction using regex patterns

### Response Format
LLM returns JSON:
```json
{
    "response": "Natural language response to user",
    "extracted": {
        "field_name": "extracted value",
        ...
    }
}
```

## Error Handling

### Session Errors
- **Session Not Found**: Returns 404 with clear message
- **Inactive Session**: Returns 400 indicating session is completed/abandoned
- **Unauthorized Access**: Returns 401 if authentication fails

### LLM Failures
- Automatic fallback to alternative providers
- Rule-based extraction if all LLMs fail
- Graceful degradation maintains conversation flow

### Validation Errors
- URL format validation with helpful error messages
- Required field checks before finalization
- Clear feedback on missing information

## Testing

### Unit Tests
Location: `/tests/unit/test_services/test_brand_discovery_chat.py`

Coverage:
- Conversation initialization
- Message processing and extraction
- Progress calculation
- Data cleaning and normalization
- Fallback extraction
- Edge cases and error handling

Run tests:
```bash
pytest tests/unit/test_services/test_brand_discovery_chat.py -v
```

### Integration Tests
Location: `/tests/integration/test_brand_discovery_chat_integration.py`

Coverage:
- Complete API workflow
- Multi-message conversations
- Correction handling
- Progress tracking
- Session finalization
- Authentication and authorization

Run tests:
```bash
pytest tests/integration/test_brand_discovery_chat_integration.py -v
```

## Database Migration

Run migration to create table:
```bash
# Using Alembic
alembic upgrade head

# Or manually
python -c "from src.database.migrations.007_add_brand_discovery_chat import upgrade; upgrade()"
```

## Frontend Integration Example

```javascript
// React component example
import { useState } from 'react';

function BrandDiscoveryChat() {
    const [sessionId, setSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [progress, setProgress] = useState(0);
    const [isComplete, setIsComplete] = useState(false);

    // Start chat session
    const startChat = async () => {
        const response = await fetch('/brand-discovery-chat/start', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
            }
        });
        const data = await response.json();

        setSessionId(data.session_id);
        setMessages([{
            role: 'assistant',
            content: data.first_message
        }]);
    };

    // Send message
    const sendMessage = async (userMessage) => {
        // Add user message to UI
        setMessages([...messages, {
            role: 'user',
            content: userMessage
        }]);

        // Send to API
        const response = await fetch(
            `/brand-discovery-chat/${sessionId}/message`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage })
            }
        );
        const data = await response.json();

        // Add AI response
        setMessages(prev => [...prev, {
            role: 'assistant',
            content: data.ai_response
        }]);

        // Update progress
        setProgress(data.progress_pct);
        setIsComplete(data.is_complete);
    };

    // Finalize and start analysis
    const finalize = async () => {
        const response = await fetch(
            `/brand-discovery-chat/${sessionId}/finalize`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                }
            }
        );
        const data = await response.json();

        // Redirect to analysis results
        window.location.href = `/analysis/${data.analysis_job_id}`;
    };

    return (
        <div className="chat-container">
            <ProgressBar value={progress} />

            <MessageList messages={messages} />

            <MessageInput onSend={sendMessage} disabled={isComplete} />

            {isComplete && (
                <button onClick={finalize}>
                    Analyze My Brand
                </button>
            )}
        </div>
    );
}
```

## Performance Considerations

### Response Times
- Average LLM response: 1-3 seconds
- Fallback adds 2-5 seconds if primary fails
- Rule-based fallback: <100ms

### Optimization Tips
1. Use streaming responses for real-time feel
2. Cache common industry mappings
3. Prefetch user's previous sessions for context
4. Implement typing indicators during LLM processing

### Scalability
- Stateless service design allows horizontal scaling
- Database indexes on user_id, status, created_at
- Consider Redis for session caching in high-traffic scenarios

## Future Enhancements

1. **Multi-language Support**
   - Detect user language
   - Provide localized responses
   - Extract data regardless of language

2. **Voice Interface**
   - Speech-to-text integration
   - Voice responses
   - Mobile-friendly

3. **Smart Suggestions**
   - Autocomplete for competitors
   - Industry-specific keyword suggestions
   - Audience template options

4. **Session Analytics**
   - Track completion rates
   - Identify drop-off points
   - A/B test different conversation flows

5. **Integration with Brand Analysis**
   - Auto-start analysis when complete
   - Real-time preview of analysis results
   - Iterative refinement based on initial findings

## Troubleshooting

### Common Issues

**Issue**: LLM not extracting data correctly
**Solution**: Check system prompt and few-shot examples; verify JSON mode is enabled

**Issue**: Progress not updating
**Solution**: Verify field weights calculation; check extracted_data persistence

**Issue**: Session marked as complete prematurely
**Solution**: Validate _is_complete() logic; ensure all required fields checked

**Issue**: URL normalization failures
**Solution**: Review _clean_url() regex; add edge cases to tests

## Support

For questions or issues:
- Check test files for usage examples
- Review conversation transcripts in `/docs/examples/`
- Consult LLM service documentation
- Contact: engineering@engarde.com
