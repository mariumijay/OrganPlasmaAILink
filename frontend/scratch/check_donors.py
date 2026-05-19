import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('.env.local')
url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== DONOR COORDINATES CHECK ===")
res = supabase.table('donors').select('full_name, latitude, longitude, blood_type, city').in_('approval_status', ['approved', 'verified']).limit(15).execute()

has_coords = 0
no_coords = 0
for r in res.data:
    lat = r.get('latitude')
    lng = r.get('longitude')
    name = r.get('full_name', '?')
    city = r.get('city', '?')
    bt = r.get('blood_type', '?')
    if lat and lng:
        has_coords += 1
        print(f"  [OK] {name} | {bt} | {city} | lat={lat}, lng={lng}")
    else:
        no_coords += 1
        print(f"  [NO COORDS] {name} | {bt} | {city}")

print(f"\nSummary: {has_coords} with coords, {no_coords} without coords out of {len(res.data)} donors")

print("\n=== HOSPITAL COORDINATES CHECK ===")
res2 = supabase.table('hospitals').select('name, city, latitude, longitude, user_id').execute()
for h in res2.data:
    print(f"  {h['name']} | {h['city']} | lat={h.get('latitude')}, lng={h.get('longitude')} | user_id={h.get('user_id')}")
