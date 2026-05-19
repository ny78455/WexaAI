import asyncio
import httpx
import uuid

API_URL = "http://localhost:8000/api/v1"

async def test_auth_and_dashboards():
    print("Testing Backend APIs...")
    async with httpx.AsyncClient() as client:
        # 1. Test Health
        try:
            r = await client.get("http://localhost:8000/health")
            print(f"Health Check: {r.status_code}")
        except Exception as e:
            print(f"Health Check failed: {e}")
            return

        # Generate unique user
        uid = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"test_{uid}@example.com",
            "password": "Password123!",
            "full_name": "Test User",
            "organization_name": "Test Org"
        }

        # 2. Signup
        print(f"\n--- Testing Signup with {user_data['email']} ---")
        r = await client.post(f"{API_URL}/auth/signup", json=user_data)
        print(f"Signup status: {r.status_code}")
        print(r.text)
        if r.status_code not in (200, 201):
            return
        
        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Double Signup (Test Integrity Error Catch user added)
        print("\n--- Testing Double Signup (Should return 400) ---")
        r = await client.post(f"{API_URL}/auth/signup", json=user_data)
        print(f"Double Signup status: {r.status_code} (Expected 400)")
        print(r.text)

        # 4. Get ME
        print("\n--- Testing GET /auth/me ---")
        r = await client.get(f"{API_URL}/auth/me", headers=headers)
        print(f"Get ME status: {r.status_code}")

        # 5. Create Dashboard
        print("\n--- Testing Create Dashboard ---")
        dash_data = {"name": f"Test Dash {uid}"}
        r = await client.post(f"{API_URL}/dashboards/", json=dash_data, headers=headers)
        print(f"Create DB status: {r.status_code}")
        if r.status_code in (200, 201):
            dash_id = r.json().get("id")
            
            # 6. List Dashboards
            print("\n--- Testing List Dashboards ---")
            r = await client.get(f"{API_URL}/dashboards/", headers=headers)
            print(f"List DB status: {r.status_code}, Count: len(r.json())= {len(r.json())}")

            # 7. Add Widget
            print("\n--- Testing Add Widget ---")
            widget_data = {
                "title": "Test Widget",
                "type": "table",
                "position": {"x": 0, "y": 0, "w": 4, "h": 4},
                "time_range": "24h",
                "query_config": {}
            }
            r = await client.post(f"{API_URL}/dashboards/{dash_id}/widgets", json=widget_data, headers=headers)
            print(f"Add Widget status: {r.status_code}")
            
            # 8. Delete Dashboard
            print("\n--- Testing Delete Dashboard ---")
            r = await client.delete(f"{API_URL}/dashboards/{dash_id}", headers=headers)
            print(f"Delete DB status: {r.status_code}")

if __name__ == "__main__":
    asyncio.run(test_auth_and_dashboards())
