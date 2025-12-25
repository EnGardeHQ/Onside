"""Create market analysis tables"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, ForeignKey,
    Table, MetaData, create_engine
)
from datetime import datetime

metadata = MetaData()

# Competitors table
competitors = Table(
    'competitors',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('domain', String, nullable=False, unique=True),
    Column('description', String),
    Column('market_share', Float, default=0.0),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('updated_at', DateTime, onupdate=datetime.utcnow),
    Column('meta_data', JSON, default=dict)
)

# Competitor Content table
competitor_content = Table(
    'competitor_content',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('competitor_id', Integer, ForeignKey('competitors.id', ondelete='CASCADE'), nullable=False),
    Column('title', String),
    Column('url', String, nullable=False),
    Column('content_type', String),
    Column('published_date', DateTime),
    Column('engagement_metrics', JSON, default=dict),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('updated_at', DateTime, onupdate=datetime.utcnow)
)

# Market Tags table
market_tags = Table(
    'market_tags',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False, unique=True),
    Column('description', String),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)

# Market Segments table
market_segments = Table(
    'market_segments',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('description', String),
    Column('size', Float),
    Column('growth_rate', Float),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('updated_at', DateTime, onupdate=datetime.utcnow)
)

# Competitor Metrics table
competitor_metrics = Table(
    'competitor_metrics',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('competitor_id', Integer, ForeignKey('competitors.id', ondelete='CASCADE'), nullable=False),
    Column('metric_type', String, nullable=False),
    Column('value', Float),
    Column('timestamp', DateTime, default=datetime.utcnow, nullable=False),
    Column('meta_data', JSON, default=dict)
)

def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.create_all()

def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.drop_all()
