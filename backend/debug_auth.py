import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

print('=== HOSPITALS TABLE ===')
res = client.table('hospitals').select('id, user_id, name').execute()
for r in res.data:
    print(r)

print('\n=== AUTH USERS ===')
from httpx import Client
headers = {'apikey': os.getenv('SUPABASE_SERVICE_KEY'), 'Authorization': 'Bearer ' + os.getenv('SUPABASE_SERVICE_KEY')}
with Client() as c:
    auth_resp = c.get(os.getenv('SUPABASE_URL') + '/auth/v1/admin/users', headers=headers)
    if auth_resp.status_code == 200:
        for u in auth_resp.json().get('users', []):
            role = u.get('user_metadata', {}).get('role')
            print(f"User: {u.get('email')} | ID: {u.get('id')} | Role: {role}")
    else:
        print('Could not fetch auth users', auth_resp.text)
