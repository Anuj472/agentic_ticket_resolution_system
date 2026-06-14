import json
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.ticket import Ticket
from app.models.user import User
from app.core.redis import get_redis

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_cached_analytics(key: str) -> dict | None:
    """Read cached analytics data from Redis."""
    try:
        redis = await get_redis()
        data = await redis.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.error(f"[ANALYTICS] Cache read error: {e}")
    return None


async def set_cached_analytics(key: str, data: dict, expire_seconds: int = 300):
    """Write analytics data to Redis with TTL."""
    try:
        redis = await get_redis()
        await redis.set(key, json.dumps(data), ex=expire_seconds)
    except Exception as e:
        logger.error(f"[ANALYTICS] Cache write error: {e}")


@router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = "analytics:summary"
    cached = await get_cached_analytics(cache_key)
    if cached:
        return cached

    from sqlalchemy import case

    # Total counts via a single query to minimize DB roundtrips and connection hold time
    counts_query = select(
        func.count(Ticket.id).label("total"),
        func.count(case((Ticket.status.in_(["NEW", "OPEN", "IN_PROGRESS", "PENDING"]), 1))).label("open"),
        func.count(case((Ticket.status.in_(["RESOLVED", "CLOSED"]), 1))).label("resolved"),
        func.count(case((Ticket.is_escalated.is_(True), 1))).label("escalated"),
        func.count(case((Ticket.priority == "CRITICAL", 1))).label("critical"),
    )
    counts_result = (await db.execute(counts_query)).fetchone()

    total = counts_result.total or 0
    open_count = counts_result.open or 0
    resolved = counts_result.resolved or 0
    escalated = counts_result.escalated or 0
    critical = counts_result.critical or 0
    # By category
    cat_rows = (
        await db.execute(
            select(Ticket.category, func.count(Ticket.id).label("count"))
            .where(Ticket.category.isnot(None))
            .group_by(Ticket.category)
            .order_by(func.count(Ticket.id).desc())
        )
    ).all()
    # By priority
    pri_rows = (
        await db.execute(
            select(Ticket.priority, func.count(Ticket.id).label("count"))
            .group_by(Ticket.priority)
            .order_by(func.count(Ticket.id).desc())
        )
    ).all()
    # By status
    sta_rows = (
        await db.execute(
            select(Ticket.status, func.count(Ticket.id).label("count"))
            .group_by(Ticket.status)
            .order_by(func.count(Ticket.id).desc())
        )
    ).all()

    result = {
        "totals": {
            "total": total,
            "open": open_count,
            "resolved": resolved,
            "escalated": escalated,
            "critical": critical,
            "resolution_rate": round((resolved / total * 100), 1) if total else 0,
        },
        "by_category": [{"category": r.category, "count": r.count} for r in cat_rows],
        "by_priority": [
            {"priority": str(r.priority).split(".")[-1], "count": r.count}
            for r in pri_rows
        ],
        "by_status": [
            {"status": str(r.status).split(".")[-1], "count": r.count} for r in sta_rows
        ],
    }

    await set_cached_analytics(cache_key, result, expire_seconds=300)
    return result


@router.get("/trends")
async def get_trends(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = f"analytics:trends:{days}"
    cached = await get_cached_analytics(cache_key)
    if cached:
        return cached

    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        await db.execute(
            select(
                func.date_trunc("day", Ticket.created_at).label("day"),
                func.count(Ticket.id).label("created"),
                func.count(Ticket.resolved_at).label("resolved"),
            )
            .where(Ticket.created_at >= since)
            .group_by(func.date_trunc("day", Ticket.created_at))
            .order_by(func.date_trunc("day", Ticket.created_at))
        )
    ).all()

    result = {
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

    await set_cached_analytics(cache_key, result, expire_seconds=300)
    return result


@router.get("/sla")
async def get_sla_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = "analytics:sla"
    cached = await get_cached_analytics(cache_key)
    if cached:
        return cached

    total = (await db.execute(select(func.count(Ticket.id)))).scalar()
    breached = (
        await db.execute(
            select(func.count(Ticket.id)).where(Ticket.sla_breached.is_(True))
        )
    ).scalar()
    with_sla = (
        await db.execute(
            select(func.count(Ticket.id)).where(Ticket.sla_due_at.isnot(None))
        )
    ).scalar()
    # Breach by category
    breach_rows = (
        await db.execute(
            select(Ticket.category, func.count(Ticket.id).label("breached"))
            .where(Ticket.sla_breached.is_(True))
            .where(Ticket.category.isnot(None))
            .group_by(Ticket.category)
            .order_by(func.count(Ticket.id).desc())
        )
    ).all()

    result = {
        "total_tickets": total,
        "with_sla": with_sla,
        "breached": breached,
        "breach_rate": round((breached / total * 100), 2) if total else 0,
        "compliance_rate": round(((total - breached) / total * 100), 2)
        if total
        else 100,
        "breached_by_category": [
            {"category": r.category, "breached": r.breached} for r in breach_rows
        ],
    }

    await set_cached_analytics(cache_key, result, expire_seconds=300)
    return result


@router.get("/agents")
async def get_agent_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = "analytics:agents"
    cached = await get_cached_analytics(cache_key)
    if cached:
        return cached

    rows = (
        await db.execute(
            select(
                Ticket.category, Ticket.priority, func.count(Ticket.id).label("count")
            )
            .where(Ticket.category.isnot(None))
            .group_by(Ticket.category, Ticket.priority)
            .order_by(Ticket.category, func.count(Ticket.id).desc())
        )
    ).all()
    heatmap = {}
    for r in rows:
        heatmap.setdefault(r.category, {})[str(r.priority)] = r.count

    result = {"category_priority_heatmap": heatmap}
    await set_cached_analytics(cache_key, result, expire_seconds=300)
    return result
