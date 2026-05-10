
import asyncio
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.ticket import Ticket

async def check():
    async with AsyncSessionLocal() as db:
        count = await db.execute(select(func.count(Ticket.id)))
        print(f"COUNT: {count.scalar()}")
        
        first = await db.execute(select(Ticket).limit(1))
        ticket = first.scalar_one_or_none()
        if ticket:
            print(f"SAMPLE: {ticket.ticket_number}, {ticket.status}, {ticket.priority}")
        else:
            print("NO TICKETS IN DB")

if __name__ == "__main__":
    asyncio.run(check())
