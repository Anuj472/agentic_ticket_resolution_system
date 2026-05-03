"""
Seed script: creates admin user, agent groups, and sample KB articles.
Usage: make seed
"""
import asyncio
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus
from app.models.knowledge_base import AgentGroup


async def seed():
    async with AsyncSessionLocal() as db:
        # Admin user
        admin = User(
            employee_id="EMP001",
            email="admin@company.com",
            full_name="System Admin",
            hashed_password=hash_password("Admin@1234"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_agent=True,
        )
        db.add(admin)

        # Agent groups
        for name, skills in [
            ("L1 Support",   ["password_reset", "account_unlock", "basic_hardware"]),
            ("L2 Network",   ["vpn", "firewall", "dns", "routing"]),
            ("L3 Security",  ["incident_response", "forensics", "patch_management"]),
            ("L3 Software",  ["dev_tools", "deployment", "database", "api"]),
        ]:
            db.add(AgentGroup(name=name, skills=skills))

        await db.commit()
        print("✅ Seed complete — admin: admin@company.com / Admin@1234")


if __name__ == "__main__":
    asyncio.run(seed())
