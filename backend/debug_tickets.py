import asyncio
from app.core.database import AsyncSessionLocal
from app.models.ticket import Ticket
from sqlalchemy import select, func

async def debug():
    print("Connecting to DB...")
    try:
        async with AsyncSessionLocal() as db:
            print("Running count query...")
            count_q = select(func.count(Ticket.id))
            res = await db.execute(count_q)
            print("Count:", res.scalar())
            
            print("Running select query...")
            from sqlalchemy.orm import noload
            q = select(Ticket).options(noload("*")).limit(10)
            res2 = await db.execute(q)
            items = res2.scalars().all()
            print("Items count:", len(items))
            for item in items:
                print(f" - {item.ticket_number}: {item.title[:30]}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(debug())
