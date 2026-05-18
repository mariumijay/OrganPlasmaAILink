import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

res = client.table('notifications').select('user_id, title, created_at').order('created_at', desc=True).limit(10).execute()
for r in res.data:
    title = r.get('title', '').encode('ascii', 'ignore').decode()
    print(f"User: {r.get('user_id')} | Title: {title} | Date: {r.get('created_at')}")
