import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    END_USER   = "end_user"
    L1_AGENT   = "l1_agent"
    L2_AGENT   = "l2_agent"
    L3_AGENT   = "l3_agent"
    SUPERVISOR = "supervisor"
    ADMIN      = "admin"


class UserStatus(str, enum.Enum):
    ACTIVE   = "active"
    INACTIVE = "inactive"
    LOCKED   = "locked"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID]    = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str]       = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str]   = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole]   = mapped_column(SAEnum(UserRole), default=UserRole.END_USER)
    department: Mapped[str]  = mapped_column(String(100), nullable=True)
    phone: Mapped[str]       = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str]  = mapped_column(Text, nullable=True)
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus), default=UserStatus.ACTIVE)
    is_agent: Mapped[bool]   = mapped_column(Boolean, default=False)
    max_concurrent_tickets: Mapped[int] = mapped_column(default=10)
    skills: Mapped[str]      = mapped_column(Text, nullable=True)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    submitted_tickets = relationship("Ticket", back_populates="submitter", foreign_keys="Ticket.submitter_id")
    assigned_tickets  = relationship("Ticket", back_populates="assignee",  foreign_keys="Ticket.assignee_id")
    comments          = relationship("Comment", back_populates="author")
    audit_logs        = relationship("AuditLog", back_populates="actor")
