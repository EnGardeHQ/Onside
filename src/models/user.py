"""User model module."""
from sqlalchemy import String, DateTime, Boolean, Column, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Optional
from enum import Enum as PyEnum

from src.database import Base
from src.auth.password_utils import generate_password_hash, check_password_hash

class UserRole(str, PyEnum):
    """User roles for role-based access control."""
    ADMIN = "admin"
    USER = "user"
    ANALYST = "analyst"
    MANAGER = "manager"

class User(Base):
    """User model class."""
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(Enum(UserRole), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships using string literals to prevent circular imports
    contents = relationship(
        "Content", 
        back_populates="user",
        lazy="select"
    )
    insights = relationship(
        "AIInsight", 
        back_populates="user",
        lazy="select"
    )
    reports = relationship(
        "Report",
        back_populates="user",
        lazy="select"
    )
    progress_trackers = relationship(
        "ProgressTracker",
        back_populates="user",
        lazy="select"
    )
    oauth_tokens = relationship(
        "OAuthToken",
        back_populates="user",
        lazy="select"
    )
    search_history = relationship(
        "SearchHistory",
        back_populates="user",
        lazy="select"
    )
    report_schedules = relationship(
        "ReportSchedule",
        back_populates="user",
        lazy="select"
    )
    brand_analysis_jobs = relationship(
        "BrandAnalysisJob",
        back_populates="user",
        lazy="select"
    )

    def set_password(self, password: str) -> None:
        """Set user password."""
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if provided password matches stored hash."""
        return check_password_hash(self.hashed_password, password)
        
    def has_role(self, role: str) -> bool:
        """Check if user has the specified role."""
        return self.role == role or self.is_admin

    def __repr__(self) -> str:
        """String representation of the User model."""
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
