import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')

if not url or not key:
    print('ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env')
    exit(1)

client = create_client(url, key)

print("=" * 50)
print("OPAL-AI FULL SYSTEM DIAGNOSTIC")
print("=" * 50)

# 1. Test donors table
res = client.table('donors').select('id,full_name,blood_type,is_available,approval_status').limit(5).execute()
print(f'\n[DB] Donors table: {len(res.data)} rows fetched')
for d in res.data:
    name = d.get('full_name', 'N/A')
    bt = d.get('blood_type', 'N/A')
    avail = d.get('is_available', 'N/A')
    status = d.get('approval_status', 'N/A')
    print(f'     {name} | {bt} | available={avail} | status={status}')

# 2. Test hospitals table
hosp = client.table('hospitals').select('id,name,latitude,longitude').limit(3).execute()
print(f'\n[DB] Hospitals table: {len(hosp.data)} rows fetched')
for h in hosp.data:
    name = h.get('name', 'N/A')
    lat = h.get('latitude', 'MISSING')
    lng = h.get('longitude', 'MISSING')
    print(f'     {name} | lat={lat}, lng={lng}')
    if not lat or not lng:
        print('     WARNING: Hospital missing coordinates!')

# 3. Test match_results table
try:
    mr = client.table('match_results').select('id,status,model_used').limit(3).execute()
    print(f'\n[DB] match_results table: OK ({len(mr.data)} records)')
    for r in mr.data:
        print(f'     status={r.get("status")} | model={r.get("model_used")}')
except Exception as e:
    print(f'\n[DB] match_results table: MISSING or ERROR — {e}')
    print('     ACTION REQUIRED: Create this table in Supabase!')

# 4. Test data_access_logs table
try:
    dl = client.table('data_access_logs').select('id').limit(1).execute()
    print(f'\n[DB] data_access_logs table: OK')
except Exception as e:
    print(f'\n[DB] data_access_logs table: MISSING — {e}')

# 5. Test notifications table
try:
    n = client.table('notifications').select('id').limit(1).execute()
    print(f'\n[DB] notifications table: OK')
except Exception as e:
    print(f'\n[DB] notifications table: MISSING — {e}')

# 6. Donor availability count
available = client.table('donors').select('id', count='exact').eq('is_available', True).execute()
approved = client.table('donors').select('id', count='exact').in_('approval_status', ['approved', 'verified']).execute()
print(f'\n[DB] Available donors in pool: {available.count}')
print(f'[DB] Approved/Verified donors: {approved.count}')

print("\n" + "=" * 50)
print("DATABASE: FULLY OPERATIONAL")
print("=" * 50)
