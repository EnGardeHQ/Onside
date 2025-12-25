from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from src.database import Base

class MarketScope(str, Enum):
    GLOBAL = "global"
    REGIONAL = "regional"
    LOCAL = "local"

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    market_scope = Column(SQLEnum(MarketScope))
    language = Column(String)
    search_volume = Column(Integer, nullable=True)
    competition = Column(Float, nullable=True)

    # Relationships
    subtopics = relationship("Subtopic", back_populates="subject")
    content_assets = relationship("ContentAsset", back_populates="subject")
    opportunity_score = relationship("OpportunityScore", back_populates="subject", uselist=False)

class Subtopic(Base):
    __tablename__ = "subtopics"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    name = Column(String, index=True)
    search_volume = Column(Integer)
    competition = Column(Float)

    # Relationships
    subject = relationship("Subject", back_populates="subtopics")

class ContentAsset(Base):
    __tablename__ = "content_assets"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    url = Column(String, index=True)
    topic = Column(String)
    style = Column(String)
    format = Column(String)
    google_ranking = Column(Integer, nullable=True)
    social_engagement = Column(JSON)
    likeability_score = Column(Float, default=0.0)
    market = Column(String)
    persona = Column(JSON)

    # Relationships
    subject = relationship("Subject", back_populates="content_assets")

class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), unique=True)
    opportunity_index = Column(Float)
    niche_potential_index = Column(Float)

    # Relationships
    subject = relationship("Subject", back_populates="opportunity_score")
