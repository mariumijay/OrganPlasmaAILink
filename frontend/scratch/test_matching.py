"""
Test matching results for two different hospitals to verify 
they get different distances and scores.
"""
import requests
import json

# Hospital 1: Haseeb hospital (user_id: 72bf96be-cb46-4d1b-aba5-73ec7547d371)
# Hospital 2: FOUJI FOUNDATION (user_id: f8819ab7-7b79-4eed-a9ec-75620d32e40a)

BASE_URL = "http://localhost:8000/api/match/find"

def test_hospital(hospital_id, hospital_name):
    payload = {
        "hospital_id": hospital_id,
        "required_organs": ["Kidney"],
        "patient_blood_type": "O+",
        "urgency_level": "medium",
        "donor_type": "organ",
        "max_results": 5
    }
    
    print(f"\n{'='*60}")
    print(f"  HOSPITAL: {hospital_name}")
    print(f"  hospital_id: {hospital_id}")
    print(f"{'='*60}")
    
    resp = requests.post(BASE_URL, json=payload)
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code} - {resp.text}")
        return
    
    data = resp.json()
    matches = data.get("matches", [])
    print(f"  Found {len(matches)} matches:")
    
    for i, m in enumerate(matches):
        print(f"  #{i+1} {m['name']:<25} | {m['distance_km']:>7.1f} km | {m['travel_time_human']:<20} | Score: {m['ai_score']:.2f}")

# Test both hospitals
test_hospital("72bf96be-cb46-4d1b-aba5-73ec7547d371", "Haseeb Hospital (Lahore)")
test_hospital("f8819ab7-7b79-4eed-a9ec-75620d32e40a", "FOUJI FOUNDATION (Al-Faisal Town)")
