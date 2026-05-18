
import os
from supabase import create_client

url = "https://qsmwlrywrjuudfjooqsz.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFzbXdscnl3cmp1dWRmam9vcXN6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQ2MzYyOSwiZXhwIjoyMDkxMDM5NjI5fQ.jNfTgIzcfXOZZQCBYsovQXWdLZtMegsSqD_gXpyOBs4"

supabase = create_client(url, key)

try:
    res = supabase.auth.admin.list_users()
    users = res if isinstance(res, list) else getattr(res, 'users', [])
    
    for user in users:
        if user.email in ['ranahaseeb101@gmail.com', 'ranahaseeb1@gmail.com']:
            print(f"Purging target user: {user.email}")
            supabase.auth.admin.delete_user(user.id)
            supabase.table('hospitals').delete().eq('contact_email', user.email).execute()
    print("Purge complete.")
except Exception as e:
    print(f"Error: {e}")
