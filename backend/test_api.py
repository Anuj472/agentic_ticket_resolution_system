
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test():
    # Login
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@company.com",
        "password": "Admin@1234"
    })
    print(f"LOGIN: {resp.status_code}")
    if resp.status_code != 200:
        print(resp.text)
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # List tickets
    resp = requests.get(f"{BASE_URL}/tickets", headers=headers)
    print(f"TICKETS: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"TOTAL: {data['total']}")
        print(f"ITEMS: {len(data['items'])}")
    else:
        print(resp.text)

if __name__ == "__main__":
    test()
