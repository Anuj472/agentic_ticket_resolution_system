from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_ok, redis_ok = False, False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    try:
        r = await get_redis()
        await r.ping()
        redis_ok = True
    except Exception:
        pass
    return {
        "status": "healthy" if (db_ok and redis_ok) else "degraded",
        "services": {"database": db_ok, "redis": redis_ok},
        "version": "1.0.0",
    }
