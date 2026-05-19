import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def debug_broadcast():
    print("--- Hospital Table Check ---")
    hospitals = supabase.table("hospitals").select("id, user_id, name").execute()
    for h in hospitals.data:
        print(f"Hospital ID: {h['id']}, User ID: {h['user_id']}, Name: {h['name']}")
    
    print("\n--- Organ Requests Table Check ---")
    try:
        # Check if table exists and columns
        res = supabase.table("organ_requests").select("*").limit(1).execute()
        print("organ_requests table exists.")
        print(f"Sample data: {res.data}")
    except Exception as e:
        print(f"Error accessing organ_requests: {e}")

if __name__ == "__main__":
    debug_broadcast()
