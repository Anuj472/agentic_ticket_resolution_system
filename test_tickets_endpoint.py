import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run():
    print("Logging in...")
    login_data = json.dumps({
        "email": "admin@company.com",
        "password": "Admin@1234"
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            login_res = json.loads(response.read().decode("utf-8"))
            token = login_res["access_token"]
            print("Login successful.")
    except Exception as e:
        print("Login failed:", e)
        return

    print("Fetching tickets...")
    req2 = urllib.request.Request(
        f"{BASE_URL}/tickets",
        headers={"Authorization": f"Bearer {token}"},
        method="GET"
    )
    
    try:
        with urllib.request.urlopen(req2) as response:
            res_body = response.read().decode("utf-8")
            tickets = json.loads(res_body)
            print("Get tickets successful!")
            print("Total tickets:", tickets.get("total"))
            print("Items count:", len(tickets.get("items", [])))
            if tickets.get("items"):
                print("First ticket:", tickets["items"][0]["ticket_number"], "-", tickets["items"][0]["title"])
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
    except Exception as e:
        print("Fetch failed:", e)

if __name__ == "__main__":
    run()
