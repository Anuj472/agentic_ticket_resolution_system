import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class KBArticle(Base):
    __tablename__ = "kb_articles"

    id: Mapped[uuid.UUID]    = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str]       = mapped_column(String(500), nullable=False)
    content: Mapped[str]     = mapped_column(Text, nullable=False)
    summary: Mapped[str]     = mapped_column(Text, nullable=True)
    category: Mapped[str]    = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[list]       = mapped_column(JSON, default=list)
    is_published: Mapped[bool]   = mapped_column(Boolean, default=True)
    view_count: Mapped[int]      = mapped_column(default=0)
    helpful_votes: Mapped[int]   = mapped_column(default=0)
    qdrant_point_id: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentGroup(Base):
    __tablename__ = "agent_groups"

    id: Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]         = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str]  = mapped_column(Text, nullable=True)
    skills: Mapped[list]      = mapped_column(JSON, default=list)
    is_active: Mapped[bool]   = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
