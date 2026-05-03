from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)
    is_internal: bool = False


class CommentResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    author_id: UUID
    content: str
    is_internal: bool
    is_ai_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}
