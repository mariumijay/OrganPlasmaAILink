import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Get all donors with a user_id
donors = client.table('donors').select('id, full_name, user_id').not_.is_('user_id', 'null').execute().data

# Get all auth users
from httpx import Client
headers = {'apikey': os.getenv('SUPABASE_SERVICE_KEY'), 'Authorization': 'Bearer ' + os.getenv('SUPABASE_SERVICE_KEY')}
with Client() as c:
    auth_resp = c.get(os.getenv('SUPABASE_URL') + '/auth/v1/admin/users', headers=headers)
    auth_users = {u['id']: u['email'] for u in auth_resp.json().get('users', [])}

print('=== LINKED DONORS ===')
for d in donors:
    uid = d.get('user_id')
    if uid in auth_users:
        print(f"Donor: {d['full_name']} | UserID: {uid} | Email: {auth_users[uid]}")
