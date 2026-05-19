
import os
from supabase import create_client

url = "https://qsmwlrywrjuudfjooqsz.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFzbXdscnl3cmp1dWRmam9vcXN6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQ2MzYyOSwiZXhwIjoyMDkxMDM5NjI5fQ.jNfTgIzcfXOZZQCBYsovQXWdLZtMegsSqD_gXpyOBs4"

supabase = create_client(url, key)

try:
    res = supabase.table("hospitals").select("*").execute()
    for h in res.data:
        print(f"Name: {h.get('name')}, Lat: {h.get('latitude')}, Lon: {h.get('longitude')}, UserID: {h.get('user_id')}")
except Exception as e:
    print(f"Error: {e}")
