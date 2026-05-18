import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

res = client.table('notifications').select('*').eq('user_id', '91ad61f1-5935-485b-8bef-c0d0018cb07e').execute()
print(f"Found {len(res.data)} notifications")
for r in res.data:
    print(f"Notification: {r.get('id')} | Created: {r.get('created_at')}")
