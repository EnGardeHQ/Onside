"""Models for En Garde brand analysis integration."""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from src.database import Base


class AnalysisStatus(str, enum.Enum):
    """Status of brand analysis job."""
    INITIATED = "initiated"
    CRAWLING = "crawling"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class KeywordSource(str, enum.Enum):
    """Source of discovered keyword."""
    WEBSITE_CONTENT = "website_content"
    SERP_ANALYSIS = "serp_analysis"
    NLP_EXTRACTION = "nlp_extraction"


class CompetitorCategory(str, enum.Enum):
    """Category of identified competitor."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    EMERGING = "emerging"
    NICHE = "niche"


class GapType(str, enum.Enum):
    """Type of content gap."""
    MISSING_CONTENT = "missing_content"
    WEAK_CONTENT = "weak_content"
    COMPETITOR_STRENGTH = "competitor_strength"


class ContentPriority(str, enum.Enum):
    """Priority level for content opportunity."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BrandAnalysisJob(Base):
    """Brand analysis job tracking."""
    __tablename__ = "brand_analysis_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    questionnaire = Column(JSONB, nullable=False)
    status = Column(SQLEnum(AnalysisStatus), nullable=False, default=AnalysisStatus.INITIATED)
    progress = Column(Integer, nullable=False, default=0)  # 0-100
    results = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="brand_analysis_jobs")
    discovered_keywords = relationship(
        "DiscoveredKeyword",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="select"
    )
    identified_competitors = relationship(
        "IdentifiedCompetitor",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="select"
    )
    content_opportunities = relationship(
        "ContentOpportunity",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="select"
    )


class DiscoveredKeyword(Base):
    """Staging table for discovered keywords from brand analysis."""
    __tablename__ = "discovered_keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("brand_analysis_jobs.id"), nullable=False)
    keyword = Column(Text, nullable=False)
    source = Column(SQLEnum(KeywordSource), nullable=False)
    search_volume = Column(Integer, nullable=True)
    difficulty = Column(Float, nullable=True)  # 0-100
    relevance_score = Column(Float, nullable=False, default=0.0)  # 0-1
    current_ranking = Column(Integer, nullable=True)
    serp_features = Column(JSONB, nullable=True)
    confirmed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job = relationship("BrandAnalysisJob", back_populates="discovered_keywords")


class IdentifiedCompetitor(Base):
    """Staging table for identified competitors from brand analysis."""
    __tablename__ = "identified_competitors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("brand_analysis_jobs.id"), nullable=False)
    domain = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    relevance_score = Column(Float, nullable=False, default=0.0)  # 0-1
    category = Column(SQLEnum(CompetitorCategory), nullable=False, default=CompetitorCategory.SECONDARY)
    overlap_percentage = Column(Float, nullable=True)
    keyword_overlap = Column(JSONB, nullable=True)
    content_similarity = Column(Float, nullable=True)
    confirmed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job = relationship("BrandAnalysisJob", back_populates="identified_competitors")


class ContentOpportunity(Base):
    """Content opportunities and insights from brand analysis."""
    __tablename__ = "content_opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("brand_analysis_jobs.id"), nullable=False)
    topic = Column(Text, nullable=False)
    gap_type = Column(SQLEnum(GapType), nullable=False)
    traffic_potential = Column(Integer, nullable=True)
    difficulty = Column(Float, nullable=True)
    priority = Column(SQLEnum(ContentPriority), nullable=False, default=ContentPriority.MEDIUM)
    recommended_format = Column(String(100), nullable=True)  # blog, guide, video, infographic
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job = relationship("BrandAnalysisJob", back_populates="content_opportunities")
