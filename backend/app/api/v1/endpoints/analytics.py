from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.ticket import Ticket, TicketStatus, TicketPriority
from app.models.user import User
router = APIRouter()
@router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Total counts
    total = (await db.execute(select(func.count(Ticket.id)))).scalar()
    open_count = (await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.status.in_(["NEW", "OPEN", "IN_PROGRESS", "PENDING"])
        )
    )).scalar()
    resolved = (await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.status.in_(["RESOLVED", "CLOSED"])
        )
    )).scalar()
    escalated = (await db.execute(
        select(func.count(Ticket.id)).where(Ticket.is_escalated == True)
    )).scalar()
    critical = (await db.execute(
        select(func.count(Ticket.id)).where(Ticket.priority == "CRITICAL")
    )).scalar()
    # By category
    cat_rows = (await db.execute(
        select(Ticket.category, func.count(Ticket.id).label("count"))
        .where(Ticket.category.isnot(None))
        .group_by(Ticket.category)
        .order_by(func.count(Ticket.id).desc())
    )).all()
    # By priority
    pri_rows = (await db.execute(
        select(Ticket.priority, func.count(Ticket.id).label("count"))
        .group_by(Ticket.priority)
        .order_by(func.count(Ticket.id).desc())
    )).all()
    # By status
    sta_rows = (await db.execute(
        select(Ticket.status, func.count(Ticket.id).label("count"))
        .group_by(Ticket.status)
        .order_by(func.count(Ticket.id).desc())
    )).all()
    return {
        "totals": {
            "total": total,
            "open": open_count,
            "resolved": resolved,
            "escalated": escalated,
            "critical": critical,
            "resolution_rate": round((resolved / total * 100), 1) if total else 0,
        },
        "by_category": [{"category": r.category, "count": r.count} for r in cat_rows],
        "by_priority": [{"priority": str(r.priority).split(".")[-1], "count": r.count} for r in pri_rows],
        "by_status":   [{"status":   str(r.status).split(".")[-1],   "count": r.count} for r in sta_rows],
    }
@router.get("/trends")
async def get_trends(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (await db.execute(
        select(
            func.date_trunc("day", Ticket.created_at).label("day"),
            func.count(Ticket.id).label("created"),
            func.count(Ticket.resolved_at).label("resolved"),
        )
        .where(Ticket.created_at >= since)
        .group_by(func.date_trunc("day", Ticket.created_at))
        .order_by(func.date_trunc("day", Ticket.created_at))
    )).all()
    return {
        "days": days,
        "data": [
            {
                "date": r.day.strftime("%Y-%m-%d"),
                "created": r.created,
                "resolved": r.resolved,
            }
            for r in rows
        ],
    }
@router.get("/sla")
async def get_sla_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = (await db.execute(select(func.count(Ticket.id)))).scalar()
    breached = (await db.execute(
        select(func.count(Ticket.id)).where(Ticket.sla_breached == True)
    )).scalar()
    with_sla = (await db.execute(
        select(func.count(Ticket.id)).where(Ticket.sla_due_at.isnot(None))
    )).scalar()
    # Breach by category
    breach_rows = (await db.execute(
        select(Ticket.category, func.count(Ticket.id).label("breached"))
        .where(Ticket.sla_breached == True)
        .where(Ticket.category.isnot(None))
        .group_by(Ticket.category)
        .order_by(func.count(Ticket.id).desc())
    )).all()
    return {
        "total_tickets": total,
        "with_sla": with_sla,
        "breached": breached,
        "breach_rate": round((breached / total * 100), 2) if total else 0,
        "compliance_rate": round(((total - breached) / total * 100), 2) if total else 100,
        "breached_by_category": [{"category": r.category, "breached": r.breached} for r in breach_rows],
    }
@router.get("/agents")
async def get_agent_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (await db.execute(
        select(Ticket.category, Ticket.priority, func.count(Ticket.id).label("count"))
        .where(Ticket.category.isnot(None))
        .group_by(Ticket.category, Ticket.priority)
        .order_by(Ticket.category, func.count(Ticket.id).desc())
    )).all()
    heatmap = {}
    for r in rows:
        heatmap.setdefault(r.category, {})[str(r.priority)] = r.count
    return {"category_priority_heatmap": heatmap}
