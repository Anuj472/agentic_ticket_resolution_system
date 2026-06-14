from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
from app.models.ticket import TicketStatus, TicketPriority, TicketChannel


class UniversalTicket(BaseModel):
    title: str
    description: str
    source: str
    source_ref_id: Optional[str] = None
    submitter_email: Optional[str] = None
    priority_hint: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    description: str = Field(..., min_length=10)
    priority: TicketPriority = TicketPriority.MEDIUM
    channel: TicketChannel = TicketChannel.WEB
    category: Optional[str] = None
    tags: Optional[List[str]] = []


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    category: Optional[str] = None
    assignee_id: Optional[uuid.UUID] = None
    tags: Optional[List[str]] = None
    human_resolution: Optional[str] = None


class TicketResolve(BaseModel):
    human_resolution: Optional[str] = None


class TicketResponse(BaseModel):
    id: uuid.UUID
    ticket_number: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    channel: TicketChannel
    category: Optional[str] = None
    sub_category: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_suggested_solution: Optional[str] = None
    human_resolution: Optional[str] = None
    urgency_score: Optional[float] = None
    is_escalated: bool = False
    # Routing & confidence fields
    routing_confidence: Optional[float] = None
    repeat_issue: bool = False
    automation_candidate: bool = False
    similar_ticket_count: int = 0
    routing_reason: Optional[str] = None
    assigned_department: Optional[str] = None
    submitter_id: uuid.UUID
    assignee_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    items: List[TicketResponse]
    total: int
    page: int
    page_size: int
    pages: int
