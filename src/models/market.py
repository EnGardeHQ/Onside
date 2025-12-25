"""
Models for market analysis and competitor tracking
"""
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float, Table
from sqlalchemy.orm import relationship
from src.database import Base

# Association tables must be defined before the models that use them
competitor_tags = Table(
    'competitor_tags',
    Base.metadata,
    Column('competitor_id', Integer, ForeignKey('competitors.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('market_tags.id', ondelete='CASCADE'), primary_key=True)
)

content_segments = Table(
    'content_segments',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('competitor_content.id', ondelete='CASCADE'), primary_key=True),
    Column('segment_id', Integer, ForeignKey('market_segments.id', ondelete='CASCADE'), primary_key=True)
)

class MarketTag(Base):
    """Model for market categorization tags"""
    __tablename__ = 'market_tags'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    
    # Relationships
    competitors = relationship("Competitor", secondary=competitor_tags, back_populates="tags")

class MarketSegment(Base):
    """Model for market segmentation"""
    __tablename__ = 'market_segments'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    
    # Relationships
    content_items = relationship(
        "CompetitorContent",
        secondary=content_segments,
        back_populates="market_segments"
    )

class Competitor(Base):
    """Model for tracking competitors"""
    __tablename__ = 'competitors'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False, unique=True)
    description = Column(String)
    market_share = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now)
    meta_data = Column(JSON, default=dict)
    
    # Relationships
    content_items = relationship("CompetitorContent", back_populates="competitor", cascade="all, delete-orphan")
    tags = relationship("MarketTag", secondary=competitor_tags, back_populates="competitors")
    performance_metrics = relationship("CompetitorMetrics", back_populates="competitor", cascade="all, delete-orphan")

class CompetitorContent(Base):
    """Model for tracking competitor content"""
    __tablename__ = 'competitor_content'

    id = Column(Integer, primary_key=True)
    competitor_id = Column(Integer, ForeignKey('competitors.id', ondelete='CASCADE'), nullable=False)
    url = Column(String, nullable=False, unique=True)
    title = Column(String)
    content_type = Column(String)
    publish_date = Column(DateTime(timezone=True))
    discovered_date = Column(DateTime(timezone=True), default=datetime.now)
    last_updated = Column(DateTime(timezone=True), onupdate=datetime.now)
    engagement_metrics = Column(JSON, default=dict)
    content_metrics = Column(JSON, default=dict)
    meta_data = Column(JSON, default=dict)
    
    # Relationships
    competitor = relationship("Competitor", back_populates="content_items")
    market_segments = relationship(
        "MarketSegment",
        secondary=content_segments,
        back_populates="content_items"
    )

class CompetitorMetrics(Base):
    """Model for tracking competitor performance metrics"""
    __tablename__ = 'competitor_metrics'

    id = Column(Integer, primary_key=True)
    competitor_id = Column(Integer, ForeignKey('competitors.id', ondelete='CASCADE'), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    metric_date = Column(DateTime(timezone=True), nullable=False)
    metric_type = Column(String, nullable=False)
    value = Column(Float)
    confidence_score = Column(Float)
    source = Column(String)
    mentions_count = Column(Integer, default=0)
    sentiment_score = Column(Float)
    engagement_rate = Column(Float)
    meta_data = Column(JSON, default=dict)
    
    # Relationships
    competitor = relationship("Competitor", back_populates="performance_metrics")
