"""Models for email delivery and tracking."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Optional
from sqlalchemy import ForeignKey, JSON, DateTime, String, Integer, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database import Base


class EmailStatus(str, PyEnum):
    """Email delivery status enumeration."""
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    DELIVERED = "delivered"


class EmailProvider(str, PyEnum):
    """Email service provider enumeration."""
    SENDGRID = "sendgrid"
    SES = "ses"
    SMTP = "smtp"


class EmailRecipient(Base):
    """Model for managing email recipients.

    This model stores email recipients associated with companies,
    enabling distribution lists for automated reports and notifications.
    """
    __tablename__ = "email_recipients"
    __table_args__ = (
        UniqueConstraint('company_id', 'email', name='uq_email_recipients_company_email'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()", onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="email_recipients")

    def __repr__(self) -> str:
        """String representation."""
        return f"<EmailRecipient(id={self.id}, email='{self.email}', active={self.is_active})>"


class EmailDelivery(Base):
    """Model for tracking email delivery status and history.

    This model stores detailed information about each email sent,
    including delivery status, provider information, and engagement metrics.
    """
    __tablename__ = "email_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reports.id"), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachment_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=EmailStatus.QUEUED.value)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    bounced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivery_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()", onupdate=datetime.utcnow)

    # Relationships
    report = relationship("Report", back_populates="email_deliveries")

    def mark_sent(self, provider_message_id: Optional[str] = None) -> None:
        """Mark email as sent.

        Args:
            provider_message_id: Message ID from the email provider
        """
        self.status = EmailStatus.SENT.value
        self.sent_at = datetime.utcnow()
        self.provider_message_id = provider_message_id
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """Mark email as failed.

        Args:
            error_message: Error description
        """
        self.status = EmailStatus.FAILED.value
        self.error_message = error_message
        self.retry_count += 1
        self.updated_at = datetime.utcnow()

    def mark_bounced(self, bounce_reason: Optional[str] = None) -> None:
        """Mark email as bounced.

        Args:
            bounce_reason: Reason for bounce
        """
        self.status = EmailStatus.BOUNCED.value
        self.bounced_at = datetime.utcnow()
        if bounce_reason:
            self.error_message = bounce_reason
        self.updated_at = datetime.utcnow()

    def mark_opened(self) -> None:
        """Mark email as opened by recipient."""
        if not self.opened_at:
            self.opened_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def mark_clicked(self) -> None:
        """Mark email link as clicked by recipient."""
        if not self.clicked_at:
            self.clicked_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def should_retry(self, max_retries: int = 3) -> bool:
        """Check if email should be retried.

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            bool: True if should retry
        """
        return (
            self.status == EmailStatus.FAILED.value and
            self.retry_count < max_retries
        )

    def get_delivery_metrics(self) -> Dict:
        """Get delivery metrics for this email.

        Returns:
            Dict: Metrics including delivery time, open time, etc.
        """
        metrics = {
            "status": self.status,
            "retry_count": self.retry_count,
            "sent": self.sent_at is not None,
            "opened": self.opened_at is not None,
            "clicked": self.clicked_at is not None,
            "bounced": self.bounced_at is not None,
        }

        if self.sent_at and self.created_at:
            metrics["delivery_time_seconds"] = (self.sent_at - self.created_at).total_seconds()

        if self.opened_at and self.sent_at:
            metrics["time_to_open_seconds"] = (self.opened_at - self.sent_at).total_seconds()

        if self.clicked_at and self.sent_at:
            metrics["time_to_click_seconds"] = (self.clicked_at - self.sent_at).total_seconds()

        return metrics

    def __repr__(self) -> str:
        """String representation."""
        return f"<EmailDelivery(id={self.id}, recipient='{self.recipient_email}', status='{self.status}')>"
