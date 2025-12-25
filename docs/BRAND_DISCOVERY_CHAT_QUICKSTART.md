# Brand Discovery Chat - Quick Start Guide

## Overview

This guide will help you integrate the Brand Discovery Chat into your En Garde application in 5 minutes.

## Prerequisites

- Python 3.8+
- PostgreSQL database
- OpenAI API key (or Anthropic API key as fallback)
- Existing En Garde installation

## Step 1: Database Migration

Run the migration to create the chat sessions table:

```bash
cd /Users/cope/EnGardeHQ/Onside

# Using Alembic (recommended)
alembic upgrade head

# Or run migration directly
python -c "from src.database.migrations.007_add_brand_discovery_chat import upgrade; from alembic import op; from sqlalchemy import create_engine; engine = create_engine('your_db_url'); upgrade()"
```

Verify the table was created:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_name = 'brand_discovery_chat_sessions';
```

## Step 2: Environment Variables

Ensure your `.env` file has LLM API keys:

```bash
# Primary LLM (required)
OPENAI_API_KEY=sk-...

# Fallback LLM (optional but recommended)
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/onside
```

## Step 3: Register API Routes

Update `/Users/cope/EnGardeHQ/Onside/src/main.py` to include the chat routes:

```python
from src.api.v1.brand_discovery_chat import router as brand_discovery_chat_router

# Add to your API router registrations
app.include_router(
    brand_discovery_chat_router,
    prefix="/api/v1",
    tags=["brand-discovery-chat"]
)
```

## Step 4: Test the API

Start your server:

```bash
uvicorn src.main:app --reload --port 8000
```

Test with curl:

```bash
# Get auth token first
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"yourpassword"}' \
  | jq -r '.access_token')

# Start chat session
SESSION=$(curl -X POST http://localhost:8000/api/v1/brand-discovery-chat/start \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.session_id')

echo "Session ID: $SESSION"

# Send first message
curl -X POST http://localhost:8000/api/v1/brand-discovery-chat/$SESSION/message \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Acme Corporation"}' \
  | jq

# Check progress
curl -X GET http://localhost:8000/api/v1/brand-discovery-chat/$SESSION/status \
  -H "Authorization: Bearer $TOKEN" \
  | jq
```

## Step 5: Frontend Integration

### Option A: Simple JavaScript

```html
<!DOCTYPE html>
<html>
<head>
    <title>Brand Discovery Chat</title>
    <style>
        .chat-container { max-width: 600px; margin: 50px auto; }
        .messages { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 20px; }
        .message { margin: 10px 0; }
        .user-message { text-align: right; color: blue; }
        .ai-message { text-align: left; color: green; }
        .input-area { margin-top: 20px; }
        .progress-bar { width: 100%; height: 20px; background: #f0f0f0; margin: 10px 0; }
        .progress-fill { height: 100%; background: #4caf50; transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Brand Discovery Chat</h2>

        <div class="progress-bar">
            <div id="progress" class="progress-fill" style="width: 0%"></div>
        </div>
        <div id="progress-text">0% Complete</div>

        <div id="messages" class="messages"></div>

        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Type your message..."
                   style="width: 80%; padding: 10px;">
            <button onclick="sendMessage()" style="padding: 10px 20px;">Send</button>
        </div>

        <div id="finalize-area" style="display: none; margin-top: 20px;">
            <button onclick="finalize()" style="padding: 10px 20px; background: #4caf50; color: white;">
                Start Brand Analysis
            </button>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8000/api/v1';
        let authToken = 'YOUR_AUTH_TOKEN'; // Get from login
        let sessionId = null;
        let isComplete = false;

        // Start chat on page load
        window.onload = async () => {
            const response = await fetch(`${API_BASE}/brand-discovery-chat/start`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            const data = await response.json();
            sessionId = data.session_id;
            addMessage('assistant', data.first_message);
        };

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();

            if (!message || isComplete) return;

            // Add user message to UI
            addMessage('user', message);
            input.value = '';

            // Send to API
            const response = await fetch(
                `${API_BASE}/brand-discovery-chat/${sessionId}/message`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${authToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message })
                }
            );

            const data = await response.json();

            // Add AI response
            addMessage('assistant', data.ai_response);

            // Update progress
            updateProgress(data.progress_pct);

            // Check if complete
            if (data.is_complete) {
                isComplete = true;
                document.getElementById('finalize-area').style.display = 'block';
                document.getElementById('messageInput').disabled = true;
            }
        }

        function addMessage(role, content) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;
            messageDiv.textContent = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function updateProgress(percent) {
            document.getElementById('progress').style.width = `${percent}%`;
            document.getElementById('progress-text').textContent = `${percent}% Complete`;
        }

        async function finalize() {
            const response = await fetch(
                `${API_BASE}/brand-discovery-chat/${sessionId}/finalize`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                }
            );

            const data = await response.json();
            alert(data.message);

            // Redirect to analysis results
            if (data.analysis_job_id) {
                window.location.href = `/analysis/${data.analysis_job_id}`;
            }
        }

        // Allow Enter key to send message
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
```

### Option B: React Component

```jsx
// BrandDiscoveryChat.jsx
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const BrandDiscoveryChat = ({ authToken }) => {
    const [sessionId, setSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [progress, setProgress] = useState(0);
    const [isComplete, setIsComplete] = useState(false);
    const messagesEndRef = useRef(null);

    const API_BASE = '/api/v1/brand-discovery-chat';

    useEffect(() => {
        startChat();
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const startChat = async () => {
        try {
            const response = await axios.post(`${API_BASE}/start`, {}, {
                headers: { Authorization: `Bearer ${authToken}` }
            });

            setSessionId(response.data.session_id);
            setMessages([{
                role: 'assistant',
                content: response.data.first_message,
                timestamp: new Date()
            }]);
        } catch (error) {
            console.error('Error starting chat:', error);
        }
    };

    const sendMessage = async () => {
        if (!inputMessage.trim() || isComplete) return;

        const userMessage = {
            role: 'user',
            content: inputMessage,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');

        try {
            const response = await axios.post(
                `${API_BASE}/${sessionId}/message`,
                { message: inputMessage },
                { headers: { Authorization: `Bearer ${authToken}` } }
            );

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response.data.ai_response,
                timestamp: new Date()
            }]);

            setProgress(response.data.progress_pct);
            setIsComplete(response.data.is_complete);
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };

    const finalize = async () => {
        try {
            const response = await axios.post(
                `${API_BASE}/${sessionId}/finalize`,
                {},
                { headers: { Authorization: `Bearer ${authToken}` } }
            );

            alert(response.data.message);

            if (response.data.analysis_job_id) {
                window.location.href = `/analysis/${response.data.analysis_job_id}`;
            }
        } catch (error) {
            console.error('Error finalizing:', error);
        }
    };

    return (
        <div className="brand-discovery-chat">
            <div className="chat-header">
                <h2>Brand Discovery</h2>
                <div className="progress-bar">
                    <div
                        className="progress-fill"
                        style={{ width: `${progress}%` }}
                    />
                </div>
                <p>{progress}% Complete</p>
            </div>

            <div className="messages-container">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        <p>{msg.content}</p>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-container">
                <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Type your message..."
                    disabled={isComplete}
                />
                <button onClick={sendMessage} disabled={isComplete}>
                    Send
                </button>
            </div>

            {isComplete && (
                <div className="finalize-container">
                    <button onClick={finalize} className="finalize-btn">
                        Start Brand Analysis
                    </button>
                </div>
            )}
        </div>
    );
};

export default BrandDiscoveryChat;
```

## Step 6: Run Tests

```bash
# Unit tests
pytest tests/unit/test_services/test_brand_discovery_chat.py -v

# Integration tests
pytest tests/integration/test_brand_discovery_chat_integration.py -v

# All tests
pytest tests/ -k brand_discovery -v
```

## Common Issues & Solutions

### Issue: LLM not responding

**Solution**: Check API keys in `.env`:
```bash
# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Anthropic key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -X POST \
  -d '{"model":"claude-3-sonnet-20240229","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

### Issue: Database table not found

**Solution**: Run migration manually:
```bash
python -c "
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import os

engine = create_engine(os.getenv('DATABASE_URL'))
metadata = MetaData()

# Create table
with engine.connect() as conn:
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS brand_discovery_chat_sessions (
            session_id UUID PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            messages JSONB NOT NULL DEFAULT '[]',
            extracted_data JSONB NOT NULL DEFAULT '{}',
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    '''))
    conn.commit()
"
```

### Issue: 401 Unauthorized

**Solution**: Ensure you're passing a valid auth token:
```javascript
// Get token from login response
const loginResponse = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'user@example.com', password: 'password' })
});
const { access_token } = await loginResponse.json();

// Use token in chat requests
const chatResponse = await fetch('/api/v1/brand-discovery-chat/start', {
    headers: { 'Authorization': `Bearer ${access_token}` }
});
```

### Issue: Slow responses

**Solution**: Enable streaming (future enhancement) or show loading indicator:
```javascript
// Show typing indicator
function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.innerHTML = 'AI is thinking...';
    document.getElementById('messages').appendChild(indicator);
}

function hideTypingIndicator() {
    document.getElementById('typing-indicator')?.remove();
}

// Use in sendMessage
showTypingIndicator();
const response = await fetch(...);
hideTypingIndicator();
```

## Next Steps

1. **Customize Prompts**: Edit system prompts in `src/services/ai/brand_discovery_chat.py`
2. **Add Analytics**: Track conversation metrics (time, completion rate, drop-off points)
3. **Enhance UI**: Add typing indicators, message timestamps, avatar images
4. **Multi-language**: Add i18n support for international users
5. **Voice Input**: Integrate speech-to-text for mobile users

## Documentation

- **Full Documentation**: `/docs/BRAND_DISCOVERY_CHAT.md`
- **Example Conversations**: `/docs/examples/brand_discovery_conversation_examples.md`
- **API Reference**: Check FastAPI auto-generated docs at `/docs` or `/redoc`
- **Test Suite**: `/tests/unit/test_services/test_brand_discovery_chat.py`

## Support

For questions or issues:
- Check existing tests for usage examples
- Review conversation examples for expected behavior
- Consult LLM service documentation for API integration
- Create an issue in the project repository

## Performance Tips

1. **Cache Sessions**: Use Redis for active session caching in production
2. **Optimize Queries**: Add indexes on frequently queried fields
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Batch Updates**: Update session data in batches rather than on every message
5. **CDN for Static Assets**: Serve frontend assets from CDN for faster load times

## Security Checklist

- [ ] API keys stored in environment variables (not committed to repo)
- [ ] Authentication required for all endpoints
- [ ] Session isolation (users can't access others' sessions)
- [ ] Input validation on all user messages
- [ ] SQL injection prevention (using SQLAlchemy ORM)
- [ ] Rate limiting configured
- [ ] HTTPS enforced in production
- [ ] CORS properly configured

## Monitoring

Track these metrics in production:

- **Conversation Metrics**:
  - Average completion time
  - Completion rate (% of sessions that finish)
  - Drop-off points (which questions users abandon at)
  - Average messages per session

- **Performance Metrics**:
  - API response times
  - LLM response times
  - Database query times
  - Cache hit rates

- **Quality Metrics**:
  - Extraction accuracy
  - Correction frequency
  - Clarification frequency
  - User satisfaction ratings

Congratulations! Your Brand Discovery Chat is now ready to use. 🎉
