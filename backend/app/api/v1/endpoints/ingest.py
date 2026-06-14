import uuid
import random
import string
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.ticket import Ticket, TicketStatus, TicketPriority, TicketChannel
from app.models.user import User, UserRole, UserStatus
from app.core.security import hash_password
from app.adapters.factory import get_adapter
from app.workers.tasks.ticket_tasks import process_new_ticket

router = APIRouter()


def _gen_ticket_number() -> str:
    suffix = "".join(random.choices(string.digits, k=6))
    return f"TKT-{suffix}"


async def _get_or_create_guest_user(db: AsyncSession, email: str, source: str) -> User:
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        return user

    # Create guest user
    guest_uuid = str(uuid.uuid4())[:8]
    user = User(
        employee_id=f"guest_{source}_{guest_uuid}",
        email=email,
        full_name=f"Guest User ({source})",
        hashed_password=hash_password(str(uuid.uuid4())),  # Random unguessable password
        role=UserRole.END_USER,
        status=UserStatus.ACTIVE,
        is_agent=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/webhooks/{source}", status_code=status.HTTP_202_ACCEPTED)
async def ingest_ticket(
    source: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Universal ingestion endpoint for external webhooks.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        adapter = get_adapter(source)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        universal_ticket = adapter.normalize(payload)
    except Exception as e:
        raise HTTPException(
            status_code=422, detail=f"Failed to normalize payload: {str(e)}"
        )

    # Resolve submitter
    email = (
        universal_ticket.submitter_email
        or f"anonymous_{source}_{str(uuid.uuid4())[:8]}@local.guest"
    )
    submitter = await _get_or_create_guest_user(db, email, source)

    # Map source to channel if possible
    source_lower = source.lower()
    if source_lower == "slack":
        channel = TicketChannel.SLACK
    elif source_lower == "email":
        channel = TicketChannel.EMAIL
    else:
        channel = TicketChannel.API

    # Create Ticket in DB
    ticket = Ticket(
        ticket_number=_gen_ticket_number(),
        title=universal_ticket.title,
        description=universal_ticket.description,
        status=TicketStatus.NEW,
        priority=TicketPriority.MEDIUM,  # Could map priority_hint here
        channel=channel,
        source=source_lower,
        source_ref_id=universal_ticket.source_ref_id,
        source_metadata=universal_ticket.metadata,
        submitter_id=submitter.id,
        rag_kb_articles=[],
        custom_fields={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    # Dispatch to Celery
    try:
        process_new_ticket.apply_async(
            args=[str(ticket.id)],
            queue="ticket_processing",
        )
    except Exception:
        pass  # Log error in production

    return {
        "status": "accepted",
        "ticket_id": str(ticket.id),
        "ticket_number": ticket.ticket_number,
        "source": source,
    }
