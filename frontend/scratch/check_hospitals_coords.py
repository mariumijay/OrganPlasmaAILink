import os
from supabase import create_client

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Missing environment variables")
    exit(1)

supabase = create_client(url, key)

res = supabase.table("hospitals").select("id, user_id, name, city, latitude, longitude").execute()
for h in res.data:
    print(f"Hospital: {h['name']} ({h['city']})")
    print(f"  ID: {h['id']}")
    print(f"  User ID: {h['user_id']}")
    print(f"  Coords: ({h['latitude']}, {h['longitude']})")
    print("-" * 20)
