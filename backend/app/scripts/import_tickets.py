import csv, uuid, asyncio, random, string
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
PRIORITY_MAP = {"critical":"CRITICAL","high":"HIGH","medium":"MEDIUM","low":"LOW"}
CHANNEL_MAP  = {"chat":"web","email":"email","phone":"phone","portal":"web","api":"api","web":"web"}
STATUS_MAP   = {"resolved":"resolved","closed":"closed"}
def gen_ticket_number(ticket_id: str) -> str:
    num = ticket_id.replace("INC-","")
    return f"TKT-{num.zfill(6)}"
async def import_csv():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    from app.models.ticket import Ticket, TicketStatus, TicketPriority, TicketChannel
    from app.models.user import User
    from sqlalchemy import select
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == "admin@company.com"))
        admin = result.scalar_one()
        rows = []
        with open("/app/tickets_import.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                priority_raw = row["priority"].strip().lower()
                channel_raw  = row["source_channel"].strip().lower()
                created_raw  = row["created_at"].strip()
                try:
                    created_dt = datetime.strptime(created_raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except:
                    created_dt = datetime.now(timezone.utc)
                ticket = Ticket(
                    ticket_number        = gen_ticket_number(row["ticket_id"]),
                    title                = row["title"][:500],
                    description          = row["description"],
                    status               = TicketStatus.RESOLVED if row.get("resolution","").strip() else TicketStatus.NEW,
                    priority             = TicketPriority[PRIORITY_MAP.get(priority_raw,"MEDIUM")],
                    channel              = TicketChannel[CHANNEL_MAP.get(channel_raw,"web").upper()],
                    category             = row.get("category","").strip() or None,
                    sub_category         = row.get("subcategory","").strip() or None,
                    category_confidence  = float(row["confidence_score"]) if row.get("confidence_score") else None,
                    ai_suggested_solution= row.get("resolution","").strip() or None,
                    ai_summary           = row.get("resolution_steps","").strip() or None,
                    is_escalated         = row.get("escalation_required","false").strip().lower() == "true",
                    submitter_id         = admin.id,
                    sla_breached         = False,
                    rag_kb_articles      = [],
                    tags                 = [],
                    custom_fields        = {
                        "department":      row.get("department",""),
                        "environment":     row.get("environment",""),
                        "affected_service":row.get("affected_service",""),
                        "sentiment":       row.get("sentiment",""),
                        "user_impact":     row.get("user_impact",""),
                        "kb_article":      row.get("kb_article",""),
                        "resolver_group":  row.get("resolver_group",""),
                        "original_id":     row.get("ticket_id",""),
                    },
                    created_at = created_dt,
                    updated_at = created_dt,
                )
                rows.append(ticket)
        db.add_all(rows)
        await db.commit()
        print(f"✅ Imported {len(rows)} tickets successfully!")
asyncio.run(import_csv())
