"""
Seed script: creates admin user, agent groups, and sample KB articles.
Usage: make seed
"""

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus
from app.models.knowledge_base import AgentGroup


async def seed():
    async with AsyncSessionLocal() as db:
        # Admin user
        result = await db.execute(select(User).where(User.email == "admin@company.com"))
        existing_admin = result.scalar_one_or_none()
        if not existing_admin:
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
            print("👤 Seeding admin user...")
        else:
            print("👤 Admin user already exists, skipping.")

        # Agent groups
        for name, skills in [
            ("L1 Support", ["password_reset", "account_unlock", "basic_hardware"]),
            ("L2 Network", ["vpn", "firewall", "dns", "routing"]),
            ("L3 Security", ["incident_response", "forensics", "patch_management"]),
            ("L3 Software", ["dev_tools", "deployment", "database", "api"]),
        ]:
            result = await db.execute(select(AgentGroup).where(AgentGroup.name == name))
            existing_group = result.scalar_one_or_none()
            if not existing_group:
                db.add(AgentGroup(name=name, skills=skills))
                print(f"👥 Seeding agent group '{name}'...")
            else:
                print(f"👥 Agent group '{name}' already exists, skipping.")

        await db.commit()
        print("✅ Seed complete — admin: admin@company.com / Admin@1234")


if __name__ == "__main__":
    asyncio.run(seed())
