from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class KBArticleCreate(BaseModel):
    title: str = Field(..., min_length=5)
    content: str = Field(..., min_length=20)
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []


class KBArticleResponse(BaseModel):
    id: UUID
    title: str
    content: str
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: List[str]
    is_published: bool
    view_count: int
    helpful_votes: int
    created_at: datetime

    model_config = {"from_attributes": True}
