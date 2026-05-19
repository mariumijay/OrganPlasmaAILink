import os
from supabase import create_client

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(url, key)

res = supabase.table("donors").select("*").ilike("full_name", "%Haseeb Iftikhar%").execute()
if not res.data:
    print("Donor 'Haseeb Iftikhar' not found.")
else:
    for d in res.data:
        print(f"Donor: {d['full_name']}")
        print(f"  City: {d['city']}")
        print(f"  Blood Type: {d['blood_type']}")
        print(f"  Coords: ({d['latitude']}, {d['longitude']})")
        print(f"  Is Approved: {d['is_approved']}")
        print(f"  Is Available: {d['is_available']}")
        print(f"  Created At: {d['created_at']}")
        print("-" * 20)
