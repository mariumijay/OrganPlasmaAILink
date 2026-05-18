import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def test_insert():
    # Fetch a valid hospital ID
    hospitals = supabase.table("hospitals").select("id").limit(1).execute()
    if not hospitals.data:
        print("No hospitals found.")
        return
    
    h_id = hospitals.data[0]['id']
    print(f"Using Hospital ID: {h_id}")
    
    # Try inserting exactly what the frontend sends
    data = {
        "hospital_id": h_id,
        "patient_blood_type": "A-",
        "required_organs": ["Whole Blood"],
        "urgency_level": "Routine",
        "status": "open"
    }
    
    print(f"Attempting to insert: {data}")
    res = supabase.table("organ_requests").insert(data).execute()
    print(f"Response: {res}")

if __name__ == "__main__":
    try:
        test_insert()
    except Exception as e:
        print(f"EXCEPTION: {e}")
