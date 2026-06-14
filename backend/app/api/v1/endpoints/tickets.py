import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import noload
from datetime import datetime, timezone
import math

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.ticket import Ticket, TicketStatus, TicketPriority, TicketChannel
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketListResponse,
    TicketResolve,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _gen_ticket_number(db: AsyncSession) -> str:
    """Generate a sequential ticket number using DB to avoid collisions."""
    result = await db.execute(select(func.count(Ticket.id)))
    count = result.scalar() or 0
    return f"TKT-{count + 1:06d}"


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = Ticket(
        ticket_number=await _gen_ticket_number(db),
        title=payload.title,
        description=payload.description,
        priority=TicketPriority[payload.priority.value.upper()]
        if hasattr(payload.priority, "value")
        else TicketPriority.MEDIUM,
        channel=TicketChannel[payload.channel.value.upper()]
        if hasattr(payload.channel, "value")
        else TicketChannel.WEB,
        category=payload.category,
        tags=payload.tags or [],
        status=TicketStatus.NEW,
        submitter_id=current_user.id,
        rag_kb_articles=[],
        custom_fields={},
        sla_breached=False,
        is_escalated=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    # Fire Celery task async (don't block response)
    try:
        from app.workers.tasks.ticket_tasks import process_new_ticket

        process_new_ticket.apply_async(
            args=[str(ticket.id)],
            queue="ticket_processing",
        )
    except Exception:
        pass  # Task failure never blocks ticket creation
    return ticket


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    priority: str = Query(None),
    category: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Build a shared count query — avoids the hanging subquery() pattern
    count_q = select(func.count(Ticket.id))
    q = select(Ticket)

    # DB stores enums as UPPERCASE (IN_PROGRESS, RESOLVED, etc.) - Enums now match
    if status:
        count_q = count_q.where(Ticket.status == status.upper())
        q = q.where(Ticket.status == status.upper())
    if priority:
        count_q = count_q.where(Ticket.priority == priority.upper())
        q = q.where(Ticket.priority == priority.upper())
    if category:
        count_q = count_q.where(Ticket.category == category)
        q = q.where(Ticket.category == category)

    count_result = await db.execute(count_q)
    total = count_result.scalar()
    logger.info(f"[API] list_tickets total: {total}")

    # noload('*') prevents async lazy-loading of relationships (hangs indefinitely in async)
    q = q.options(noload("*")).order_by(Ticket.created_at.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(q)
    items = result.scalars().all()

    return TicketListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket).options(noload("*")).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    ticket.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/queue/unprocessed")
async def get_unprocessed_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return IN_PROGRESS tickets with AI solutions awaiting human review.
    These are tickets the AI has processed (HIGH priority) but that need
    a human agent to confirm and mark resolved.
    """
    q = select(Ticket).where(
        Ticket.status == "IN_PROGRESS",
        or_(Ticket.ai_suggested_solution.isnot(None), Ticket.is_escalated.is_(True)),
    )
    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar()
    q = q.order_by(Ticket.created_at.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    items = result.scalars().all()

    def _val(v):
        return v.value if hasattr(v, "value") else str(v)

    return {
        "items": [
            {
                "id": str(t.id),
                "ticket_number": t.ticket_number,
                "title": t.title,
                "description": t.description,
                "priority": _val(t.priority),
                "status": _val(t.status),
                "category": t.category,
                "sub_category": t.sub_category,
                "urgency_score": t.urgency_score,
                "ai_summary": t.ai_summary,
                "ai_suggested_solution": t.ai_suggested_solution,
                "routing_confidence": t.routing_confidence,
                "repeat_issue": t.repeat_issue,
                "automation_candidate": t.automation_candidate,
                "similar_ticket_count": t.similar_ticket_count,
                "routing_reason": t.routing_reason,
                "assigned_department": t.assigned_department,
                "created_at": t.created_at,
            }
            for t in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
    }


@router.post("/{ticket_id}/process")
async def trigger_process_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger the AI agent pipeline (Celery task) for an existing ticket.
    Safe to call multiple times — the task is idempotent (overwrites fields).
    """
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    try:
        from app.workers.tasks.ticket_tasks import process_new_ticket

        process_new_ticket.apply_async(
            args=[str(ticket.id)],
            queue="ticket_processing",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {e}")
    return {
        "message": "AI pipeline started",
        "ticket_id": str(ticket.id),
        "ticket_number": ticket.ticket_number,
    }


@router.post("/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: uuid.UUID,
    payload: TicketResolve = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a ticket as RESOLVED by a human agent after AI review."""
    from app.models.ticket import TicketStatus

    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = TicketStatus.RESOLVED
    ticket.resolved_at = datetime.now(timezone.utc)
    ticket.updated_at = datetime.now(timezone.utc)
    if payload and payload.human_resolution:
        ticket.human_resolution = payload.human_resolution
    await db.commit()
    await db.refresh(ticket)
    return {
        "message": "Ticket resolved",
        "ticket_number": ticket.ticket_number,
        "status": "RESOLVED",
    }
