import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def seed_hospitals():
    print("Seeding Hospitals...")
    hospitals = [
        {
            "id": "hosp-default",
            "name": "General Hospital Islamabad",
            "city": "Islamabad",
            "latitude": 33.6844,
            "longitude": 73.0479,
            "is_verified": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Lahore Medical Center",
            "city": "Lahore",
            "latitude": 31.5204,
            "longitude": 74.3587,
            "is_verified": True
        }
    ]
    
    for h in hospitals:
        try:
            supabase.table("hospitals").upsert(h).execute()
            print(f"  ✅ Added hospital: {h['name']}")
        except Exception as e:
            print(f"  ❌ Error adding hospital {h['name']}: {e}")

def seed_donors():
    print("\nSeeding Donors...")
    donors = [
        # --- Original 3: updated to include asthma flag ---
        {
            "id": str(uuid.uuid4()),
            "full_name": "Arshad Ahmed",
            "blood_type": "O+",
            "organs_available": ["Kidney", "Liver"],
            "latitude": 33.7297,
            "longitude": 73.0931,
            "phone": "+92 300 1234567",
            "age": 30,
            "diabetic_status": False,
            "hypertension": False,
            "heart_disease": False,
            "asthma": False,
            "is_available": True,
            "approval_status": "verified",
            "donor_type": "organ",
            "city": "Islamabad",
            "is_organ_donor": True,
            "is_blood_donor": False
        },
        {
            "id": str(uuid.uuid4()),
            "full_name": "Sara Ali",
            "blood_type": "A+",
            "organs_available": ["Heart", "Lung"],
            "latitude": 31.5497,
            "longitude": 74.3436,
            "phone": "+92 301 2345678",
            "age": 28,
            "diabetic_status": False,
            "hypertension": False,
            "heart_disease": False,
            "asthma": False,
            "is_available": True,
            "approval_status": "verified",
            "donor_type": "organ",
            "city": "Lahore",
            "is_organ_donor": True,
            "is_blood_donor": False
        },
        {
            "id": str(uuid.uuid4()),
            "full_name": "Usman Khan",
            "blood_type": "B-",
            "organs_available": [],
            "latitude": 33.5651,
            "longitude": 73.0169,
            "phone": "+92 302 3456789",
            "age": 45,
            "diabetic_status": True,
            "hypertension": False,
            "heart_disease": False,
            "asthma": False,
            "is_available": True,
            "approval_status": "verified",
            "donor_type": "blood",
            "city": "Rawalpindi",
            "is_organ_donor": False,
            "is_blood_donor": True
        },
        # --- NEW: Universal donor O- fully healthy (AI should score HIGH) ---
        {
            "id": str(uuid.uuid4()),
            "full_name": "Tariq Mehmood",
            "blood_type": "O-",
            "organs_available": ["Kidney"],
            "latitude": 31.5200,
            "longitude": 74.3600,
            "phone": "+92 303 4567890",
            "age": 34,
            "diabetic_status": False,
            "hypertension": False,
            "heart_disease": False,
            "asthma": False,
            "is_available": True,
            "approval_status": "verified",
            "donor_type": "organ",
            "city": "Lahore",
            "is_organ_donor": True,
            "is_blood_donor": True
        },
        # --- NEW: High-risk: diabetes + hypertension + heart_disease (AI should PENALIZE) ---
        {
            "id": str(uuid.uuid4()),
            "full_name": "Nasreen Bibi",
            "blood_type": "AB+",
            "organs_available": [],
            "latitude": 24.8607,
            "longitude": 67.0011,
            "phone": "+92 304 5678901",
            "age": 58,
            "diabetic_status": True,
            "hypertension": True,
            "heart_disease": True,
            "asthma": False,
            "is_available": True,
            "approval_status": "verified",
            "donor_type": "blood",
            "city": "Karachi",
            "is_organ_donor": False,
            "is_blood_donor": True
        },
        # --- NEW: Young blood donor, asthma only ---
        {
            "id": str(uuid.uuid4()),
            "full_name": "Hamza Raza",
            "blood_type": "B+",
            "organs_available": [],
            "latitude": 31.4504,
            "longitude": 73.1350,
            "phone": "+92 305 6789012",
            "age": 22,
            "diabetic_status": False,
            "hypertension": False,
            "heart_disease": False,
            "asthma": True,
            "is_available": True,
            "approval_status": "approved",
            "donor_type": "blood",
            "city": "Faisalabad",
            "is_organ_donor": False,
            "is_blood_donor": True
        },
        # --- NEW: Organ donor, hypertension only (moderate AI penalty) ---
        {
            "id": str(uuid.uuid4()),
            "full_name": "Zainab Malik",
            "blood_type": "A-",
            "organs_available": ["Kidney", "Liver"],
            "latitude": 33.6938,
            "longitude": 73.0652,
            "phone": "+92 306 7890123",
            "age": 41,
            "diabetic_status": False,
            "hypertension": True,
            "heart_disease": False,
            "asthma": False,
            "is_available": True,
            "approval_status": "verified",
            "donor_type": "organ",
            "city": "Islamabad",
            "is_organ_donor": True,
            "is_blood_donor": False
        },
        # --- NEW: AB- rare blood type, fully healthy ---
        {
            "id": str(uuid.uuid4()),
            "full_name": "Imran Siddiqui",
            "blood_type": "AB-",
            "organs_available": ["Lung"],
            "latitude": 30.1575,
            "longitude": 71.5249,
            "phone": "+92 307 8901234",
            "age": 37,
            "diabetic_status": False,
            "hypertension": False,
            "heart_disease": False,
            "asthma": False,
            "is_available": True,
            "approval_status": "verified",
            "donor_type": "organ",
            "city": "Multan",
            "is_organ_donor": True,
            "is_blood_donor": False
        }
    ]

    for d in donors:
        try:
            supabase.table("donors").upsert(d).execute()
            conditions = (
                f"diabetes={d['diabetic_status']}, "
                f"htn={d['hypertension']}, "
                f"heart={d['heart_disease']}, "
                f"asthma={d['asthma']}"
            )
            print(f"  ✅ {d['full_name']} | {d['blood_type']} | {conditions}")
        except Exception as e:
            print(f"  ❌ Error adding donor {d['full_name']}: {e}")

def seed_requests():
    print("\nSeeding Organ Requests...")
    # Fetch a hospital ID to link
    res = supabase.table("hospitals").select("id").limit(1).execute()
    if not res.data:
        print("No hospitals found, skipping requests.")
        return
    hosp_id = res.data[0]['id']
    
    requests = [
        {
            "id": str(uuid.uuid4()),
            "hospital_id": hosp_id,
            "required_organs": ["Kidney"],
            "patient_blood_type": "O+",
            "urgency_level": "critical",
            "status": "pending",
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "hospital_id": hosp_id,
            "required_organs": ["Liver"],
            "patient_blood_type": "A+",
            "urgency_level": "medium",
            "status": "open",
            "created_at": (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "hospital_id": hosp_id,
            "required_organs": ["Heart"],
            "patient_blood_type": "AB+",
            "urgency_level": "low",
            "status": "completed",
            "created_at": (datetime.now() - timedelta(days=5)).isoformat()
        }
    ]
    
    for r in requests:
        try:
            supabase.table("organ_requests").upsert(r).execute()
            print(f"  ✅ Added request: {r['required_organs']} for {hosp_id}")
        except Exception as e:
            print(f"  ❌ Error adding request: {e}")

if __name__ == "__main__":
    seed_hospitals()
    seed_donors()
    seed_requests()
    print("\n✅ Database Seeding Complete!")
