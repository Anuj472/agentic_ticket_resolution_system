import asyncio, httpx

async def test():
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60.0) as c:
        r = await c.post("/api/v1/auth/login", json={"email": "admin@company.com", "password": "Admin@1234"})
        print(f"LOGIN: {r.status_code}")
        token = r.json()["access_token"]
        r2 = await c.get("/api/v1/tickets?page_size=5", headers={"Authorization": f"Bearer {token}"})
        data = r2.json()
        print(f"STATUS={r2.status_code}")
        print(f"TOTAL={data['total']}")
        print(f"ITEMS={len(data['items'])}")
        if data["items"]:
            print(f"FIRST={data['items'][0]['ticket_number']}")

asyncio.run(test())
