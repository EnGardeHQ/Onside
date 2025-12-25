# OnSide
Predictive Scoring, Competitive Intelligence, and AI-Driven Content Recommendations

[![Semantic Seed Coding Standards](https://img.shields.io/badge/Follows-Semantic%20Seed%20Standards-blue)](https://github.com/Open-Cap-Stack/OnSide)
[![Sprint Status](https://img.shields.io/badge/Sprint%204-Completed-brightgreen)](https://github.com/Open-Cap-Stack/OnSide)

## API Components

This repository contains the Python API components migrated from the Capilytics project. The API is built using FastAPI and provides various endpoints for authentication, analytics, and data management.

### Components Overview

1. **Authentication API**
   - User registration and login
   - JWT token management
   - Role-based access control

2. **Reports & Analytics API**
   - KPI report generation
   - Data analysis endpoints
   - Custom report templates

3. **AI Insights API**
   - Content analysis with LLM integration
   - Predictive insights with chain-of-thought reasoning
   - Trend detection with fallback mechanisms
   - Content affinity analysis

4. **Audience API**
   - Audience segmentation
   - Engagement tracking
   - User behavior analysis

5. **Data Ingestion API**
   - Data import functionality
   - Data validation
   - ETL processes

6. **Recommendations API**
   - Content recommendations
   - Personalized suggestions
   - Engagement optimization

## Project Structure

```
src/
├── api/
│   ├── routes/          # API endpoints
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── core/           # Core functionality
│   └── utils/          # Utility functions
```

## Setup Instructions

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the server:
   ```bash
   uvicorn src.api.main:app --reload
   ```

## Development

- Each API component is organized in its own branch for better version control
- Follow Semantic Seed Venture Studio Coding Standards
- Implement BDD-style testing for all features
- Document API endpoints using FastAPI's automatic documentation
- Use TDD workflow: Red Tests → Green Tests → Refactor

## Sprint Progress

### Completed Sprints

#### Sprint 1: Foundational Infrastructure & Authentication
- Authentication with JWT, RBAC, user management
- CRUD endpoints for Customers, Campaigns, Companies, Domains
- Security implementation with OWASP guidelines

#### Sprint 2: Domain Seeding & Competitor Identification
- Domain seeding API with LLM integration
- Competitor identification API with LLM processing
- Automatic domain seeding for new companies

#### Sprint 3: Link Search, Web Scraping & Engagement Extraction
- Link search endpoint for current and historical links
- Web scraping integration with job status monitoring
- Engagement extraction endpoint for metrics from scraped content

#### Sprint 4: Report Generation & Advanced AI/ML Enhancements
- Report Generator API for Content and Sentiment reports with job status tracking
- AI/ML enhancements with chain-of-thought reasoning
- Fallback mechanisms for LLM calls
- Logging of chain-of-thought outputs for traceability
- Circuit breaker pattern for resilient LLM service

### Upcoming Sprints

#### Sprint 5: Internationalization, Cloud Deployment & Optimization
- Support for English, French, and Japanese
- Cloud-native deployment with AWS services
- Performance optimization and security compliance

#### Sprint 6: End-to-End Testing, Monitoring & Documentation
- Admin tools for logs and monitoring
- Comprehensive testing including stress tests
- Complete documentation for developers, API, and users

## Environment Variables

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
- `OPENAI_API_KEY`: OpenAI API key for LLM services
- `ANTHROPIC_API_KEY`: Anthropic API key for LLM fallback
- `COHERE_API_KEY`: Cohere API key for LLM fallback

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`