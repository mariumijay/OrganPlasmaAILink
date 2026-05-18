import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def count_and_purge():
    # 1. Count Pending
    donors = supabase.table("donors").select("id", count="exact").eq("approval_status", "pending").execute()
    hospitals = supabase.table("hospitals").select("id", count="exact").eq("is_verified", False).execute()
    
    donor_count = donors.count or 0
    hosp_count = hospitals.count or 0
    
    print(f"Current Pending Donors: {donor_count}")
    print(f"Current Unverified Hospitals: {hosp_count}")
    
    if donor_count > 100 or hosp_count > 100:
        print("DETECTED MASSIVE FAKE DATA. Purging...")
        
        # We only purge records that don't have a matching auth user if possible, 
        # or just purge ALL pending if the user asked.
        # Given "thousands of fake approvals", we'll purge all pending.
        
        if donor_count > 0:
            res_d = supabase.table("donors").delete().eq("approval_status", "pending").execute()
            print(f"Purged {donor_count} pending donors.")
            
        if hosp_count > 0:
            res_h = supabase.table("hospitals").delete().eq("is_verified", False).execute()
            print(f"Purged {hosp_count} unverified hospitals.")
            
        print("System Cleared. Ready for real registrations.")
    else:
        print("No massive fake data detected (count < 100). Manual review recommended.")

if __name__ == "__main__":
    count_and_purge()
