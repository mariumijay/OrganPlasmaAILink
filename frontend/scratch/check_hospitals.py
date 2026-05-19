import os
from supabase import create_client
from dotenv import load_dotenv

# Load env
load_dotenv('.env.local')

url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    print("Missing Supabase credentials")
    exit(1)

supabase = create_client(url, key)

print("--- LAHORE HOSPITALS ---")
res_lh = supabase.table('hospitals').select('name, city, contact_email').ilike('name', '%Lahore%').execute()
for r in res_lh.data:
    print(f"{r['name']} | {r['city']} | {r['contact_email']}")

print("\n--- ALL RECENT HOSPITALS ---")
res = supabase.table('hospitals').select('name, city, contact_email, created_at').order('created_at', desc=True).limit(10).execute()
for r in res.data:
    print(f"{r['name']} | {r['city']} | {r['contact_email']} | {r['created_at']}")
