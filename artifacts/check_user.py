import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def check_profiles_schema():
    print("Inspecting 'profiles' table schema...")
    res = supabase.table("profiles").select("*").limit(1).execute()
    if res.data:
        print(f"Sample Profile Record: {res.data[0]}")
        print(f"Columns found: {list(res.data[0].keys())}")
    else:
        print("No records in 'profiles' table to inspect columns.")

if __name__ == "__main__":
    check_profiles_schema()
