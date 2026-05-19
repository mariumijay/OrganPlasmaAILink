import os
from supabase import create_client

url = "https://qsmwlrywrjuudfjooqsz.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFzbXdscnl3cmp1dWRmam9vcXN6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQ2MzYyOSwiZXhwIjoyMDkxMDM5NjI5fQ.jNfTgIzcfXOZZQCBYsovQXWdLZtMegsSqD_gXpyOBs4"

supabase = create_client(url, key)

try:
    res = supabase.table("donors").select("full_name, blood_type, donor_type, is_blood_donor, is_organ_donor, approval_status").execute()
    print(f"Total donors: {len(res.data)}")
    for d in res.data:
        print(d)
except Exception as e:
    print(f"Error: {e}")
