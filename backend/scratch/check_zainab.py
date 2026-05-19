from supabase import create_client
import os

url = "https://qsmwlrywrjuudfjooqsz.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFzbXdscnl3cmp1dWRmam9vcXN6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQ2MzYyOSwiZXhwIjoyMDkxMDM5NjI5fQ.jNfTgIzcfXOZZQCBYsovQXWdLZtMegsSqD_gXpyOBs4"
supabase = create_client(url, key)

res = supabase.table("donors").select("full_name, donating_items").ilike("full_name", "%Zainab Mirza%").execute()
print(res.data)
