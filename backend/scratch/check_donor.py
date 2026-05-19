from supabase import create_client
import os

url = "https://qsmwlrywrjuudfjooqsz.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFzbXdscnl3cmp1dWRmam9vcXN6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQ2MzYyOSwiZXhwIjoyMDkxMDM5NjI5fQ.jNfTgIzcfXOZZQCBYsovQXWdLZtMegsSqD_gXpyOBs4"
supabase = create_client(url, key)

res = supabase.table("donors").select("full_name, approval_status, status, donating_items, is_blood_donor").ilike("full_name", "%Sarah Butt%").execute()
print(res.data)
