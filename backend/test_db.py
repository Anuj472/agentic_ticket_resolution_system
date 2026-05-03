import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test_conn():
    engine = create_async_engine("postgresql+asyncpg://ticket_user:ticket_pass@127.0.0.1:5432/ticket_db")
    try:
        async with engine.begin() as conn:
            print("Successfully connected via asyncpg!")
    except Exception as e:
        print(f"Asyncpg connection failed: {e}")
    finally:
        await engine.dispose()

asyncio.run(test_conn())
