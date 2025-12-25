"""Models for brand discovery chat sessions."""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from src.database import Base


class BrandDiscoveryChatSession(Base):
    """Brand discovery conversational AI chat session."""
    __tablename__ = "brand_discovery_chat_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(36), nullable=False, index=True)
    messages = Column(JSONB, nullable=False, default=list)  # [{role, content, timestamp}]
    extracted_data = Column(JSONB, nullable=False, default=dict)  # Structured questionnaire data
    status = Column(String(50), nullable=False, default='active', index=True)  # active, completed, abandoned
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "session_id": str(self.session_id),
            "user_id": self.user_id,
            "messages": self.messages,
            "extracted_data": self.extracted_data,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
