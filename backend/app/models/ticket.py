import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Float,
    JSON,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum


class TicketStatus(str, enum.Enum):
    NEW = "NEW"
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class TicketPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TicketChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    WEB = "WEB"
    SLACK = "SLACK"
    API = "API"
    PHONE = "PHONE"


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        SAEnum(TicketStatus), default=TicketStatus.NEW, index=True
    )
    priority: Mapped[TicketPriority] = mapped_column(
        SAEnum(TicketPriority), default=TicketPriority.MEDIUM, index=True
    )
    channel: Mapped[TicketChannel] = mapped_column(
        SAEnum(TicketChannel), default=TicketChannel.WEB
    )
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    sub_category: Mapped[str] = mapped_column(String(100), nullable=True)
    category_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    predicted_priority: Mapped[str] = mapped_column(String(20), nullable=True)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=True)
    urgency_score: Mapped[float] = mapped_column(Float, nullable=True)
    ai_summary: Mapped[str] = mapped_column(Text, nullable=True)
    ai_suggested_solution: Mapped[str] = mapped_column(Text, nullable=True)
    human_resolution: Mapped[str] = mapped_column(Text, nullable=True)
    rag_kb_articles: Mapped[list] = mapped_column(JSON, default=list)
    submitter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    assignee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_groups.id"), nullable=True
    )
    sla_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    first_response_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tags: Mapped[list] = mapped_column(JSON, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_reason: Mapped[str] = mapped_column(Text, nullable=True)
    # Automation & recurrence signals
    repeat_issue: Mapped[bool] = mapped_column(Boolean, default=False)
    automation_candidate: Mapped[bool] = mapped_column(Boolean, default=False)
    similar_ticket_count: Mapped[int] = mapped_column(default=0)

    # Omnichannel / Source fields
    source: Mapped[str] = mapped_column(String(50), default="api", index=True)
    source_ref_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    source_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    routing_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    routing_reason: Mapped[str] = mapped_column(Text, nullable=True)
    assigned_department: Mapped[str] = mapped_column(Text, nullable=True)
    parent_ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    submitter = relationship(
        "User", back_populates="submitted_tickets", foreign_keys=[submitter_id]
    )
    assignee = relationship(
        "User", back_populates="assigned_tickets", foreign_keys=[assignee_id]
    )
    comments = relationship(
        "Comment", back_populates="ticket", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "Attachment", back_populates="ticket", cascade="all, delete-orphan"
    )
    audit_logs = relationship("AuditLog", back_populates="ticket")
    agent_runs = relationship("AgentExecution", back_populates="ticket")
    child_tickets = relationship("Ticket", foreign_keys=[parent_ticket_id])
