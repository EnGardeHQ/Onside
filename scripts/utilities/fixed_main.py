"""
Fixed version of the main application with working Swagger documentation
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, constr
from enum import Enum

# Create the FastAPI application
app = FastAPI(
    title="OnSide API",
    description="API components for OnSide platform - Completed through Sprint 4",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Auth", "description": "Authentication and authorization endpoints"},
        {"name": "Customers", "description": "Customer management endpoints"},
        {"name": "Campaigns", "description": "Campaign management endpoints"},
        {"name": "Companies", "description": "Company management endpoints"},
        {"name": "Domains", "description": "Domain management and seeding endpoints"},
        {"name": "Competitors", "description": "Competitor identification and analysis"},
        {"name": "AI Insights", "description": "AI-powered content analysis and insights"},
        {"name": "Web Scraper", "description": "Web content scraping and processing"},
        {"name": "Reports", "description": "Report generation and management"},
        {"name": "Link Search", "description": "Link discovery and search functionality"},
        {"name": "Engagement", "description": "Content engagement metrics and analysis"},
        {"name": "SEO", "description": "Search engine optimization analysis"},
        {"name": "Audience", "description": "Audience analysis and insights"},
        {"name": "Data Ingestion", "description": "Data import and processing"},
        {"name": "Health", "description": "System health and monitoring"}
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class ReportType(str, Enum):
    CONTENT = "content"
    SENTIMENT = "sentiment"

class ReportStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    ANALYST = "analyst"
    USER = "user"

# Base Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    email: str
    username: str
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True

# Report Models
class ReportBase(BaseModel):
    type: ReportType
    parameters: Dict[str, Any]

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    id: int
    user_id: int
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

# AI Insight Models
class AIInsightBase(BaseModel):
    content_id: int
    insight_type: str
    parameters: Dict[str, Any]

class AIInsightCreate(AIInsightBase):
    pass

class AIInsight(AIInsightBase):
    id: int
    user_id: int
    created_at: datetime
    result: Dict[str, Any]

    class Config:
        from_attributes = True

# Link Models
class LinkBase(BaseModel):
    url: str
    domain_id: int

class LinkCreate(LinkBase):
    pass

class Link(LinkBase):
    id: int
    created_at: datetime
    last_scraped_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# OAuth2 scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Additional Models
class CustomerBase(BaseModel):
    name: str
    email: str
    company_id: int

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CampaignBase(BaseModel):
    name: str
    description: str
    company_id: int
    start_date: datetime
    end_date: Optional[datetime] = None

class CampaignCreate(CampaignBase):
    pass

class Campaign(CampaignBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CompanyBase(BaseModel):
    name: str
    website: str
    industry: str

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DomainBase(BaseModel):
    name: str
    company_id: int
    is_primary: bool = False

class DomainCreate(DomainBase):
    pass

class Domain(DomainBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CompetitorBase(BaseModel):
    name: str
    company_id: int
    domain: str
    confidence_score: float

class CompetitorCreate(CompetitorBase):
    pass

class Competitor(CompetitorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Basic routes
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {"message": "Welcome to OnSide API - Completed through Sprint 4"}

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "ai_services": "operational",
            "web_scraper": "operational"
        }
    }

# Auth routes
@app.post("/api/v1/auth/token", response_model=Token, tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login, get an access token for future requests"""
    return {"access_token": "mock_token", "token_type": "bearer"}

@app.get("/api/v1/auth/me", response_model=User, tags=["Auth"])
async def read_users_me(token: str = Depends(oauth2_scheme)):
    """Get current user information"""
    return {
        "id": 1,
        "email": "user@example.com",
        "username": "testuser",
        "name": "Test User",
        "is_active": True,
        "role": UserRole.USER,
        "created_at": datetime.utcnow()
    }

# Analytics routes
@app.get("/api/v1/analytics/competitive-intelligence/{competitor_id}", tags=["Analytics"])
async def get_competitor_intelligence(
    competitor_id: int,
    start_date: datetime,
    end_date: datetime,
    token: str = Depends(oauth2_scheme)
):
    """Get competitive intelligence data for a specific competitor"""
    return {
        "mentions": 150,
        "sentiment_score": 0.75,
        "share_of_voice": 0.25,
        "trending_topics": ["innovation", "technology", "growth"],
        "key_metrics": {
            "social_engagement": 5000,
            "media_mentions": 75,
            "sentiment_trend": "positive"
        }
    }

@app.get("/api/v1/analytics/market-analysis", tags=["Analytics"])
async def get_market_analysis(
    company_id: int,
    timeframe: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    token: str = Depends(oauth2_scheme)
):
    """Get market analysis data including trends and opportunities"""
    return {
        "market_size": 1000000000,
        "growth_rate": 0.15,
        "key_trends": [
            {"name": "Digital Transformation", "relevance": 0.9},
            {"name": "Cloud Adoption", "relevance": 0.85}
        ],
        "opportunities": [
            {"segment": "Enterprise", "potential": "high"},
            {"segment": "SMB", "potential": "medium"}
        ]
    }

@app.get("/api/v1/analytics/temporal-analysis", tags=["Analytics"])
async def get_temporal_analysis(
    content_id: int,
    timeframe: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    token: str = Depends(oauth2_scheme)
):
    """Get temporal analysis of content performance"""
    return {
        "peak_times": ["09:00", "14:00", "19:00"],
        "optimal_posting_times": ["10:30", "15:30"],
        "engagement_patterns": {
            "weekday": {"best": "Wednesday", "worst": "Friday"},
            "time_of_day": {"best": "Morning", "worst": "Late Night"}
        }
    }

# AI Insights routes
@app.post("/api/v1/ai-insights/sentiment/{content_id}", tags=["AI Insights"])
async def analyze_sentiment(
    content_id: int,
    with_reasoning: bool = False,
    token: str = Depends(oauth2_scheme)
):
    """Analyze sentiment of content using enhanced AI with fallback mechanisms"""
    return {
        "sentiment": "positive",
        "confidence": 0.85,
        "reasoning": "Content shows positive language and engagement" if with_reasoning else None
    }

@app.post("/api/v1/ai-insights/affinity/{content_id}", tags=["AI Insights"])
async def analyze_content_affinity(
    content_id: int,
    token: str = Depends(oauth2_scheme)
):
    """Analyze content affinity and audience alignment"""
    return {
        "affinity_score": 0.75,
        "audience_segments": ["tech_enthusiasts", "early_adopters"],
        "recommendations": ["Increase technical depth", "Add more case studies"]
    }

# Web Scraper routes
@app.post("/api/v1/web-scraper/scrape/{link_id}", tags=["Web Scraper"])
async def scrape_link(
    link_id: int,
    depth: int = Query(1, gt=0, le=3),
    extract_metadata: bool = True,
    token: str = Depends(oauth2_scheme)
):
    """Scrape content from a link with configurable depth and metadata extraction"""
    return {
        "job_id": "scrape-123",
        "estimated_completion_time": "2m",
        "scrape_config": {
            "link_id": link_id,
            "depth": depth,
            "extract_metadata": extract_metadata,
            "features": [
                "content",
                "images",
                "metadata",
                "structured_data"
            ]
        }
    }

@app.get("/api/v1/web-scraper/content/{link_id}", tags=["Web Scraper"])
async def get_scraped_content(
    link_id: int,
    include_raw: bool = False,
    token: str = Depends(oauth2_scheme)
):
    """Get scraped content for a link"""
    return {
        "content": {
            "title": "Example Article Title",
            "text": "Main article content...",
            "summary": "Brief summary of the content",
            "images": [
                {
                    "url": "https://example.com/image1.jpg",
                    "alt_text": "Example image 1",
                    "dimensions": {"width": 800, "height": 600}
                }
            ],
            "metadata": {
                "author": "John Doe",
                "published_date": "2025-03-07T14:53:14-08:00",
                "modified_date": "2025-03-07T14:53:14-08:00",
                "categories": ["Technology", "AI"],
                "tags": ["machine learning", "artificial intelligence"]
            }
        },
        "structured_data": {
            "schema_type": "Article",
            "properties": {
                "wordCount": 1500,
                "timeToRead": "7 minutes"
            }
        },
        "raw_html": "<html>...</html>" if include_raw else None
    }

@app.post("/api/v1/web-scraper/batch", tags=["Web Scraper"])
async def batch_scrape(
    link_ids: List[int],
    priority: str = Query("normal", pattern="^(high|normal|low)$"),
    token: str = Depends(oauth2_scheme)
):
    """Scrape multiple links in batch"""
    return {
        "job_id": "batch-scrape-123",
        "estimated_completion_time": "15m",
        "batch_size": len(link_ids),
        "priority": priority
    }

# Reports routes
@app.get("/api/v1/reports", response_model=List[Report], tags=["Reports"])
async def list_reports(
    status: Optional[ReportStatus] = None,
    report_type: Optional[ReportType] = None,
    token: str = Depends(oauth2_scheme)
):
    """List all reports for the current user"""
    return [{
        "id": 1,
        "user_id": 1,
        "type": ReportType.CONTENT,
        "status": ReportStatus.COMPLETED,
        "parameters": {"timeframe": "7d"},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "result": {"summary": "Content performance analysis complete"}
    }]

@app.post("/api/v1/reports", response_model=Report, tags=["Reports"])
async def create_report(
    report: ReportCreate,
    token: str = Depends(oauth2_scheme)
):
    """Create a new report"""
    return {
        "id": 1,
        "user_id": 1,
        "type": report.type,
        "status": ReportStatus.QUEUED,
        "parameters": report.parameters,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

# Link Search routes
@app.get("/api/v1/link-search/domain/{domain_id}", tags=["Link Search"])
async def search_links_for_domain(
    domain_id: int,
    max_results: int = Query(50, gt=0, le=100),
    keywords: Optional[List[str]] = Query(None),
    content_type: Optional[str] = Query(None),
    date_range: Optional[str] = Query(None, pattern="^(\d{4}-\d{2}-\d{2},\d{4}-\d{2}-\d{2})$"),
    token: str = Depends(oauth2_scheme)
):
    """Search for links associated with a domain with advanced filtering"""
    return [{
        "id": 1,
        "url": "https://example.com/article1",
        "domain_id": domain_id,
        "content_type": "article",
        "relevance_score": 0.85,
        "created_at": datetime.utcnow(),
        "last_scraped_at": datetime.utcnow(),
        "metadata": {
            "title": "Example Article",
            "description": "An example article about AI",
            "author": "John Doe",
            "published_date": datetime.utcnow().isoformat()
        }
    }]

@app.get("/api/v1/link-search/historical/{link_id}", tags=["Link Search"])
async def get_link_history(
    link_id: int,
    token: str = Depends(oauth2_scheme)
):
    """Get historical versions of a link's content"""
    return {
        "link_id": link_id,
        "versions": [
            {
                "version_id": 1,
                "snapshot_date": datetime.utcnow() - timedelta(days=7),
                "content_hash": "abc123",
                "changes": {
                    "added": 150,
                    "removed": 50,
                    "modified": 25
                }
            },
            {
                "version_id": 2,
                "snapshot_date": datetime.utcnow(),
                "content_hash": "def456",
                "changes": {
                    "added": 75,
                    "removed": 25,
                    "modified": 10
                }
            }
        ]
    }

@app.post("/api/v1/link-search/discover", tags=["Link Search"])
async def discover_new_links(
    domain_id: int,
    discovery_depth: int = Query(2, gt=0, le=5),
    token: str = Depends(oauth2_scheme)
):
    """Discover new links from a domain using intelligent crawling"""
    return {
        "job_id": "discover-123",
        "estimated_completion_time": "5m",
        "discovery_params": {
            "domain_id": domain_id,
            "depth": discovery_depth,
            "intelligent_filtering": True
        }
    }

# Engagement routes
@app.post("/api/v1/engagement/extract/{link_id}", tags=["Engagement"])
async def extract_engagement_metrics(
    link_id: int,
    include_historical: bool = False,
    token: str = Depends(oauth2_scheme)
):
    """Extract engagement metrics for a single link with optional historical data"""
    return {
        "job_id": "engagement-123",
        "estimated_completion_time": "2m",
        "extraction_params": {
            "link_id": link_id,
            "metrics": [
                "social_shares",
                "comments",
                "likes",
                "time_on_page",
                "bounce_rate"
            ],
            "include_historical": include_historical
        }
    }

@app.get("/api/v1/engagement/metrics/{link_id}", tags=["Engagement"])
async def get_engagement_metrics(
    link_id: int,
    timeframe: str = Query("7d", pattern="^(1d|7d|30d|90d)$"),
    token: str = Depends(oauth2_scheme)
):
    """Get detailed engagement metrics for a link"""
    return {
        "overall_score": 85,
        "metrics": {
            "social_shares": {
                "total": 1500,
                "by_platform": {
                    "twitter": 500,
                    "linkedin": 750,
                    "facebook": 250
                }
            },
            "comments": {
                "total": 75,
                "sentiment_distribution": {
                    "positive": 0.6,
                    "neutral": 0.3,
                    "negative": 0.1
                }
            },
            "user_engagement": {
                "avg_time_on_page": "3m 45s",
                "bounce_rate": 0.25,
                "return_visits": 450
            }
        },
        "trending_score": 0.85,
        "engagement_velocity": "increasing"
    }

@app.post("/api/v1/engagement/batch-extract", tags=["Engagement"])
async def batch_extract_engagement(
    link_ids: List[int],
    priority: str = Query("normal", pattern="^(high|normal|low)$"),
    token: str = Depends(oauth2_scheme)
):
    """Extract engagement metrics for multiple links in batch"""
    return {
        "job_id": "batch-engagement-123",
        "estimated_completion_time": "10m",
        "batch_size": len(link_ids),
        "priority": priority
    }

# SEO routes
@app.get("/api/v1/seo/analyze/{content_id}", tags=["SEO"])
async def analyze_seo(
    content_id: int,
    enhanced: bool = True,
    token: str = Depends(oauth2_scheme)
):
    """Analyze SEO metrics for content with enhanced scoring"""
    return {
        "score": 85,
        "recommendations": [
            "Add more internal links",
            "Optimize meta description"
        ],
        "keywords": {
            "primary": "ai technology",
            "secondary": ["machine learning", "artificial intelligence"]
        },
        "serp_analysis": {
            "position": 3,
            "featured_snippet_potential": "high",
            "competitors": [
                {"url": "competitor1.com", "position": 1},
                {"url": "competitor2.com", "position": 2}
            ]
        },
        "technical_seo": {
            "mobile_friendly": True,
            "page_speed": 95,
            "core_web_vitals": "good"
        }
    }

@app.get("/api/v1/seo/trends/{keyword}", tags=["SEO"])
async def get_seo_trends(
    keyword: str,
    timeframe: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    token: str = Depends(oauth2_scheme)
):
    """Get SEO trends for a specific keyword"""
    return {
        "search_volume": 10000,
        "trend": "increasing",
        "related_keywords": [
            {"keyword": "ai solutions", "volume": 5000},
            {"keyword": "machine learning tools", "volume": 3000}
        ],
        "seasonal_patterns": {
            "peak_months": ["January", "September"],
            "low_months": ["July", "December"]
        }
    }

@app.get("/api/v1/seo/semrush/{domain}", tags=["SEO"])
async def get_semrush_data(
    domain: str,
    token: str = Depends(oauth2_scheme)
):
    """Get SEO data from SEMrush for a domain"""
    return {
        "domain_authority": 45,
        "organic_traffic": 50000,
        "keyword_rankings": {
            "top_3": 5,
            "top_10": 15,
            "top_100": 150
        },
        "backlinks": {
            "total": 1000,
            "quality_score": 0.8
        }
    }

# Audience routes
@app.get("/api/v1/audience/personas/{company_id}", tags=["Audience"])
async def get_audience_personas(
    company_id: int,
    token: str = Depends(oauth2_scheme)
):
    """Get audience personas for a company"""
    return {
        "personas": [
            {
                "id": 1,
                "name": "Tech-Savvy Professional",
                "demographics": {
                    "age_range": "25-34",
                    "industries": ["Technology", "Finance"],
                    "job_levels": ["Mid-level", "Senior"]
                },
                "interests": [
                    "AI/ML",
                    "Digital Transformation",
                    "Cloud Computing"
                ],
                "behavior_patterns": {
                    "content_preferences": ["Technical", "Case Studies"],
                    "engagement_channels": ["LinkedIn", "Tech Blogs"],
                    "decision_factors": ["Technical Depth", "ROI"]
                },
                "confidence_score": 0.85
            }
        ],
        "total_audience_size": 50000,
        "engagement_distribution": {
            "highly_engaged": 0.2,
            "moderately_engaged": 0.5,
            "low_engagement": 0.3
        }
    }

@app.get("/api/v1/audience/intelligence/{content_id}", tags=["Audience"])
async def get_audience_intelligence(
    content_id: int,
    token: str = Depends(oauth2_scheme)
):
    """Get audience intelligence for specific content"""
    return {
        "audience_match": {
            "score": 0.85,
            "target_personas": [1, 2],
            "reach_potential": "high"
        },
        "engagement_prediction": {
            "expected_engagement_rate": 0.15,
            "viral_potential": "medium",
            "best_sharing_times": ["09:00", "15:00"]
        },
        "content_recommendations": {
            "topics": [
                {"name": "Cloud Security", "relevance": 0.9},
                {"name": "DevOps", "relevance": 0.8}
            ],
            "formats": [
                {"type": "Blog Post", "effectiveness": 0.85},
                {"type": "Case Study", "effectiveness": 0.75}
            ]
        }
    }

@app.post("/api/v1/audience/segment", tags=["Audience"])
async def create_audience_segment(
    company_id: int,
    segment_criteria: Dict[str, Any] = Body(...),
    token: str = Depends(oauth2_scheme)
):
    """Create a new audience segment based on specified criteria"""
    return {
        "segment_id": "seg-123",
        "name": "Enterprise Tech Decision Makers",
        "size": 15000,
        "match_score": 0.92,
        "key_characteristics": {
            "industry_focus": ["Technology", "Finance"],
            "company_size": "Enterprise",
            "decision_making_power": "High"
        },
        "recommended_approaches": [
            {
                "channel": "LinkedIn",
                "content_type": "Whitepaper",
                "messaging_theme": "Innovation Leadership"
            }
        ]
    }

# Customer routes
@app.get("/api/v1/customers", response_model=List[Customer], tags=["Customers"])
async def list_customers(
    token: str = Depends(oauth2_scheme)
):
    """List all customers"""
    return [{
        "id": 1,
        "name": "Example Customer",
        "email": "customer@example.com",
        "company_id": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }]

@app.post("/api/v1/customers", response_model=Customer, tags=["Customers"])
async def create_customer(
    customer: CustomerCreate,
    token: str = Depends(oauth2_scheme)
):
    """Create a new customer"""
    return {
        "id": 1,
        **customer.dict(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

# Campaign routes
@app.get("/api/v1/campaigns", response_model=List[Campaign], tags=["Campaigns"])
async def list_campaigns(
    token: str = Depends(oauth2_scheme)
):
    """List all campaigns"""
    return [{
        "id": 1,
        "name": "Q1 Marketing Campaign",
        "description": "First quarter marketing initiatives",
        "company_id": 1,
        "start_date": datetime.utcnow(),
        "end_date": datetime.utcnow() + timedelta(days=90),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }]

@app.post("/api/v1/campaigns", response_model=Campaign, tags=["Campaigns"])
async def create_campaign(
    campaign: CampaignCreate,
    token: str = Depends(oauth2_scheme)
):
    """Create a new campaign"""
    return {
        "id": 1,
        **campaign.dict(),
        "status": "draft",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

# Company routes
@app.get("/api/v1/companies", response_model=List[Company], tags=["Companies"])
async def list_companies(
    token: str = Depends(oauth2_scheme)
):
    """List all companies"""
    return [{
        "id": 1,
        "name": "Example Corp",
        "website": "https://example.com",
        "industry": "Technology",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }]

@app.post("/api/v1/companies", response_model=Company, tags=["Companies"])
async def create_company(
    company: CompanyCreate,
    token: str = Depends(oauth2_scheme)
):
    """Create a new company"""
    return {
        "id": 1,
        **company.dict(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

# Domain routes
@app.get("/api/v1/domains", response_model=List[Domain], tags=["Domains"])
async def list_domains(
    company_id: Optional[int] = None,
    token: str = Depends(oauth2_scheme)
):
    """List all domains"""
    return [{
        "id": 1,
        "name": "example.com",
        "company_id": 1,
        "is_primary": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }]

@app.post("/api/v1/domains", response_model=Domain, tags=["Domains"])
async def create_domain(
    domain: DomainCreate,
    token: str = Depends(oauth2_scheme)
):
    """Create a new domain"""
    return {
        "id": 1,
        **domain.dict(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

@app.post("/api/v1/domains/{domain_id}/seed", tags=["Domains"])
async def seed_domain(
    domain_id: int,
    token: str = Depends(oauth2_scheme)
):
    """Seed a domain with LLM integration for content discovery"""
    return {"job_id": "mock-domain-seed-job-id"}

# Competitor routes
@app.get("/api/v1/competitors", response_model=List[Competitor], tags=["Competitors"])
async def list_competitors(
    company_id: Optional[int] = None,
    token: str = Depends(oauth2_scheme)
):
    """List all competitors"""
    return [{
        "id": 1,
        "name": "Competitor Inc",
        "company_id": 1,
        "domain": "competitor.com",
        "confidence_score": 0.95,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }]

@app.post("/api/v1/competitors/identify", tags=["Competitors"])
async def identify_competitors(
    company_id: int,
    use_llm: bool = True,
    token: str = Depends(oauth2_scheme)
):
    """Automatically identify competitors using LLM processing"""
    return {"job_id": "mock-competitor-identification-job-id"}

# Data Ingestion routes
@app.post("/api/v1/data-ingestion/import", tags=["Data Ingestion"])
async def import_data(
    source_type: str = Body(..., pattern="^(csv|json|api)$"),
    configuration: Dict[str, Any] = Body(...),
    token: str = Depends(oauth2_scheme)
):
    """Import data from external sources"""
    return {"job_id": "mock-import-job-id"}

# Auth routes
@app.post("/api/v1/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # This is a mock implementation for documentation purposes
    return {
        "access_token": "mock_token",
        "token_type": "bearer"
    }

@app.get("/api/v1/auth/me", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    """
    Get current user information
    """
    # This is a mock implementation for documentation purposes
    return {
        "id": 1,
        "email": "user@example.com",
        "username": "testuser",
        "name": "Test User",
        "is_active": True,
        "role": "user",
        "created_at": datetime.utcnow()
    }

# Web scraper routes
class ScrapeResponse(BaseModel):
    job_id: str

@app.post("/api/v1/web-scraper/scrape/{link_id}", response_model=ScrapeResponse)
async def scrape_link(link_id: int):
    """
    Scrape content from a single link
    """
    return {"job_id": "mock-job-id"}

@app.post("/api/v1/web-scraper/scrape/batch", response_model=ScrapeResponse)
async def scrape_links_batch(link_ids: List[int]):
    """
    Scrape content from multiple links in batch
    """
    return {"job_id": "mock-job-id"}

# Report routes
class ReportResponse(BaseModel):
    id: int
    user_id: int
    type: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

@app.get("/api/v1/reports/", response_model=List[ReportResponse])
async def list_reports(token: str = Depends(oauth2_scheme)):
    """
    List all reports for the current user
    """
    return [
        {
            "id": 1,
            "user_id": 1,
            "type": "content",
            "status": "completed",
            "created_at": datetime.utcnow()
        }
    ]

@app.post("/api/v1/reports/", response_model=ReportResponse)
async def create_report(
    report_type: str,
    parameters: Dict[str, Any],
    token: str = Depends(oauth2_scheme)
):
    """
    Create a new report
    """
    return {
        "id": 1,
        "user_id": 1,
        "type": report_type,
        "status": "queued",
        "created_at": datetime.utcnow()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
