import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

from httpx import Client
user_id = None
email = None
headers = {'apikey': os.getenv('SUPABASE_SERVICE_KEY'), 'Authorization': 'Bearer ' + os.getenv('SUPABASE_SERVICE_KEY')}
with Client() as c:
    auth_resp = c.get(os.getenv('SUPABASE_URL') + '/auth/v1/admin/users', headers=headers)
    if auth_resp.status_code == 200:
        for u in auth_resp.json().get('users', []):
            role = u.get('user_metadata', {}).get('role')
            if role == 'hospital':
                user_id = u['id']
                email = u['email']
                break

if user_id:
    print(f'Found hospital user: {email} with ID {user_id}')
    hosp_res = client.table('hospitals').select('id, name, user_id').execute()
    assigned = False
    for h in hosp_res.data:
        if h['name'] == 'Hospital Account':
            client.table('hospitals').update({'user_id': user_id}).eq('id', h['id']).execute()
            print(f"Assigned Hospital Account to {user_id}")
            assigned = True
            break
    if not assigned and hosp_res.data:
        client.table('hospitals').update({'user_id': user_id}).eq('id', hosp_res.data[0]['id']).execute()
        print(f"Assigned {hosp_res.data[0]['name']} to {user_id}")
else:
    print('No hospital user found')
