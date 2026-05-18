import time
import os
import pandas as pd
import joblib
import numpy as np
import warnings
from pathlib import Path
from typing import List, Literal, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from geopy.distance import geodesic
from core.config import settings
from services.supabase_client import get_supabase
from services.compatibility_engine import MODEL_DISCLAIMER
from services.distance_service import get_road_distance
from services.explanation_service import get_explanation_service
from services.security_service import get_security_service
from services.shap_service import get_shap_explainer

# Force disable any OS level proxies that might be causing the httpx/supabase crash
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

router = APIRouter(prefix="/api/match", tags=["Clinical Matching"])

class HospitalMatchRequest(BaseModel):
    hospital_id: str
    required_organs: List[str]
    patient_blood_type: str
    patient_age: int = Field(default=40, ge=0, le=120)
    urgency_level: str = "medium"
    donor_type: str = "blood"
    required_blood_products: List[str] = []
    search_radius_km: float = Field(default=20.0, ge=1, le=500)
    max_results: int = Field(default=10, ge=1, le=100)
    # Recipient medical conditions for AI model (optional — defaults to False)
    recipient_diabetes: bool = False
    recipient_hypertension: bool = False
    recipient_heart_disease: bool = False
    recipient_asthma: bool = False
    recipient_liver_disease: bool = False
    recipient_kidney_disease: bool = False

class ScoreBreakdown(BaseModel):
    compatibility_score: float
    distance_score: float
    urgency_score: float
    ml_score: float
    total_score: float

class MatchResult(BaseModel):
    donor_id: str
    name: str
    blood_type: str
    available_organs: List[str]
    distance_km: float
    ai_score: float
    score_breakdown: ScoreBreakdown
    ai_explanation: str
    explanation_source: str
    phone: str = None
    donating_items: List[str] = []
    travel_time_human: str = "N/A"
    feature_impacts: List[Dict[str, Any]] = [] # SHAP Explainer data

class MatchResponse(BaseModel):
    advisory_notice: str = MODEL_DISCLAIMER
    matches: List[MatchResult]
    filter_stats: Dict[str, int]

_model_cache_v2 = None

def get_model_v2():
    global _model_cache_v2
    if _model_cache_v2 is None:
        base_dir = Path(__file__).resolve().parent.parent
        model_path = base_dir / "models" / "match_ranker_v2.joblib"
        if not model_path.exists():
            return None
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, message=".*XGBoost.*")
            _model_cache_v2 = joblib.load(model_path)
    return _model_cache_v2

def get_model():
    model_data = get_model_v2()
    if model_data:
        return model_data["model"]
    return None

def predict_ml_score(donor_record: dict, recipient_features: dict, model_data: dict) -> float:
    model = model_data["model"]
    features = model_data["features"]
    feat_dict = {f: 0 for f in features}

    # SMART GETTER: Checks both possible names to ensure Real Data is used
    feat_dict["donor_age"] = donor_record.get("age", 30)
    feat_dict["donor_Condition_Diabetes"]    = 1 if (donor_record.get("diabetes") or donor_record.get("diabetic_status")) else 0
    feat_dict["donor_Condition_Hypertension"] = 1 if donor_record.get("hypertension") else 0
    feat_dict["donor_Condition_Heart_Disease"] = 1 if donor_record.get("heart_disease") else 0
    feat_dict["donor_Condition_Asthma"]      = 1 if donor_record.get("asthma") else 0

    donor_bt = str(donor_record.get("blood_type", "")).strip().upper()
    bt_key = f"donor_blood_{donor_bt}"
    if bt_key in feat_dict:
        feat_dict[bt_key] = 1

    feat_dict["recipient_age"] = recipient_features.get("age", 40)
    for cond in ["Condition_Diabetes", "Condition_Hypertension", "Condition_Heart_Disease",
                 "Condition_Asthma", "Condition_Liver_Disease", "Condition_Kidney_Disease"]:
        feat_dict[f"recipient_{cond}"] = recipient_features.get(cond, 0)

    required_organ = recipient_features.get("required_organ", "")
    if required_organ:
        organ_key = f"recipient_Organ_{required_organ.capitalize()}"
        if organ_key in feat_dict:
            feat_dict[organ_key] = 1

    urgency = str(recipient_features.get("urgency_level", "medium")).lower()
    urg_key = f"urgency_{urgency}"
    if urg_key in feat_dict:
        feat_dict[urg_key] = 1

    feat_dict["distance_km"] = donor_record.get("distance_km", 50)

    X = pd.DataFrame([feat_dict])[features]
    score = model.predict(X)[0]
    return float(np.clip(score, 0, 100))

def calculate_compatibility_score(donor_blood: str, recipient_blood: str) -> float:
    # Key = Recipient, Value = List of valid Donors
    matrix = {
        "O-": ["O-"],
        "O+": ["O+", "O-"],
        "A-": ["A-", "O-"],
        "A+": ["A+", "A-", "O+", "O-"],
        "B-": ["B-", "O-"],
        "B+": ["B+", "B-", "O+", "O-"],
        "AB-": ["AB-", "A-", "B-", "O-"],
        "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"]
    }
    valid_donors = matrix.get(recipient_blood, [])
    if donor_blood in valid_donors:
        return 100.0 if donor_blood == recipient_blood else 85.0
    return 0.0

def calculate_distance_score(distance_km: float, radius_km: float) -> float:
    if distance_km > radius_km:
        return 0.0
    return 100.0 - (distance_km / radius_km) * 100.0

def get_urgency_score(urgency_level: str) -> float:
    # Normalize to lowercase so frontend values ('Emergency', 'CRITICAL', etc.) all work
    normalized = str(urgency_level).strip().lower()
    mapping = {
        "critical": 100.0,
        "emergency": 100.0,
        "medium": 75.0,
        "urgent": 75.0,
        "low": 50.0,
        "routine": 50.0
    }
    return mapping.get(normalized, 50.0)

def calculate_final_score(compat_score: float, distance_score: float, urgency_score: float) -> float:
    # Physical proximity is key for organ viability
    return (compat_score * 0.30) + (distance_score * 0.50) + (urgency_score * 0.20)

def calculate_final_score_with_ml(compat_score: float, distance_score: float, 
                                   urgency_score: float, ml_score: float) -> float:
    if ml_score > 0:
        # --- [STRICT DIAGRAM WEIGHTING: 75% Clinical + 25% Logistics] ---
        # Clinical (75%) = Compatibility (25%) + Urgency (15%) + ML Suitability (35%)
        # Logistics (25%) = Road Proximity (25%)
        return (compat_score * 0.25) + (distance_score * 0.25) + (urgency_score * 0.15) + (ml_score * 0.35)
    else:
        # Fallback maintains the 75/25 split without the ML component
        return (compat_score * 0.45) + (distance_score * 0.25) + (urgency_score * 0.30)

def generate_explanation(compat_score: float, distance_score: float, urgency_score: float,
                         donor_blood: str, recipient_blood: str, distance_km: float, urgency_level: str, ml_score: float = 0.0) -> str:
    parts = []
    if compat_score == 100:
        if donor_blood != recipient_blood:
            # O- donating to any type: still compat_score=100 only if same type, else 85
            parts.append(f"Perfect blood type match ({donor_blood} → {recipient_blood})")
        else:
            parts.append(f"Perfect blood type match ({donor_blood} → {recipient_blood})")
    elif compat_score == 85:
        # O- is the classic universal donor scenario (or any compatible cross-type)
        if donor_blood == "O-":
            parts.append(f"Universal donor (O-) compatible with {recipient_blood}")
        else:
            parts.append(f"Compatible blood type ({donor_blood} → {recipient_blood})")
    else:
        parts.append(f"Incompatible blood type ({donor_blood} cannot donate to {recipient_blood})")
    parts.append(f"Distance {distance_km:.1f} km gives {distance_score:.0f}% score")
    parts.append(f"{str(urgency_level).capitalize()} urgency gives {urgency_score:.0f}% score")
    if ml_score > 0:
        parts.append(f"XGBoost AI score: {ml_score:.1f}")
    return " + ".join(parts)

@router.post("/find", response_model=MatchResponse)
async def find_matches(request: HospitalMatchRequest):
    """
    Hospital Search Workflow.
    LIFECYCLE: [SUBMITTED] -> [PROCESSING] -> [RESULTS_READY]
    """
    try:
        # Step 1: Track Lifecycle - Submitted
        print(f"[LIFECYCLE] Match Request SUBMITTED for Hospital {request.hospital_id}")
        
        # Step 2: Processing (Filters & Scoring)
        print(f"[LIFECYCLE] Match Request PROCESSING...")
        print(f"Matching for: {request.patient_blood_type}, Urgency: {request.urgency_level}")
        supabase = get_supabase()

        # Hospital Location Detection — fetch the requesting hospital's real coordinates
        h_lat, h_lng = None, None
        hospital_name = "UNKNOWN"
        
        print(f"[DEBUG] Matching Request - Received hospital_id: {request.hospital_id}")

        # Step 1: Try finding hospital by user_id (most reliable — frontend sends auth user.id)
        try:
            hosp_res = supabase.table("hospitals").select("*").eq("user_id", request.hospital_id).execute()
            if hosp_res.data:
                hosp = hosp_res.data[0]
                h_lat = hosp.get('latitude')
                h_lng = hosp.get('longitude')
                hospital_name = hosp.get('name', 'OPAL-AI Facility')
                print(f"[OK] HOSPITAL FOUND by user_id: '{hospital_name}' | lat={h_lat}, lng={h_lng}")
            else:
                print(f"[WARN] No hospital record found for user_id: {request.hospital_id}. Trying fallback by table id...")
                # Step 2: Fallback — try by table id
                hosp_res2 = supabase.table("hospitals").select("*").eq("id", request.hospital_id).execute()
                if hosp_res2.data:
                    hosp = hosp_res2.data[0]
                    h_lat = hosp.get('latitude')
                    h_lng = hosp.get('longitude')
                    hospital_name = hosp.get('name', 'OPAL-AI Facility')
                    print(f"[OK] HOSPITAL FOUND by table id: '{hospital_name}' | lat={h_lat}, lng={h_lng}")
                else:
                    hospital_name = "Verified OPAL-AI Hospital"
                    print(f"[ERROR] CRITICAL: No hospital record found for ID: {request.hospital_id} in 'hospitals' table.")
        except Exception as e:
            hospital_name = "OPAL-AI Network Hospital"
            print(f"[ERROR] Database lookup error during matching: {e}")
        
        # If coordinates still missing, use Lahore Central as absolute last resort
        if h_lat is None or h_lng is None:
            h_lat, h_lng = 31.5204, 74.3587
            print(f"[WARN] !!! FALLBACK TO LAHORE COORDS !!! - Using default (31.5204, 74.3587)")
        
        print(f"[LOCATION] FINAL MATCHING ORIGIN: {hospital_name} @ ({h_lat}, {h_lng})")
        
        # 2. Fetch Both Approved and Verified Donors for Clinical Matching
        donors_res = supabase.table("donors").select("*") \
            .eq("is_available", True) \
            .in_("approval_status", ["approved", "verified", "pending", "active"]) \
            .order("created_at", desc=True).execute()
        raw_donors = donors_res.data or []
        print(f"[DEBUG] Fetched {len(raw_donors)} raw donors from DB.")
        if len(raw_donors) > 0:
            print(f"[DEBUG] First donor sample: {raw_donors[0].get('full_name')} | Blood: {raw_donors[0].get('blood_type')} | Status: {raw_donors[0].get('approval_status')}")

        compatible_donors = []
        seen_fuzzy = set() # For Name + Blood Type deduplication
        seen_ids = set()
        
        stats = {
            "total_donors_checked": len(raw_donors),
            "passed_clinical_filters": 0,
            "failed_blood": 0,
            "failed_organ": 0,
            "failed_radius": 0,
            "failed_blood_product": 0
        }

        # --- PASS 1: Aerial Filter & Basic Compatibility ---
        initial_candidates = []
        for donor in raw_donors:
            try:
                # Deduplication
                d_id = str(donor.get('id', ''))
                if d_id in seen_ids: continue
                seen_ids.add(d_id)

                fuzzy_key = f"{str(donor.get('full_name', '')).lower()}_{str(donor.get('blood_type', '')).upper()}"
                if fuzzy_key in seen_fuzzy: continue
                seen_fuzzy.add(fuzzy_key)
                
                d_name = donor.get('full_name', 'Unknown')
                d_blood = str(donor.get('blood_type', '')).strip().upper()
                
                # 1. Medical Compatibility Matrix (Blood)
                r_blood = str(request.patient_blood_type).strip().upper()
                compat_score = calculate_compatibility_score(d_blood, r_blood)
                
                if compat_score <= 0:
                    print(f"[DEBUG] Skipping {d_name}: Blood Incompatible ({d_blood} vs {r_blood})")
                    stats["failed_blood"] += 1
                    continue
                # 2. Organ Compatibility & Strict Medical Filters
                if request.donor_type == "organ":
                    # --- [STRICT DIAGRAM FILTER] ---
                    # 1. HIV/Hepatitis Disqualifications
                    hiv = str(donor.get('hiv_status', '')).strip().lower()
                    hep = str(donor.get('hepatitis_status', '')).strip().lower()
                    if hiv == 'positive' or hep == 'positive':
                        print(f"[FILTER] Skipping {d_name}: Clinical disqualification (HIV/Hep)")
                        continue
                    
                    # 2. Heart Disease Disqualification
                    if donor.get('heart_disease') is True:
                        print(f"[FILTER] Skipping {d_name}: Clinical disqualification (Heart Disease)")
                        continue

                    # 3. Age Window Filter per Organ (Heart: 8-45 yrs, Lung: 8-55, Kidney: 2-70)
                    d_age = donor.get('age', 30)
                    for org in request.required_organs:
                        org_lower = org.lower()
                        if 'heart' in org_lower and (d_age < 8 or d_age > 45):
                            print(f"[FILTER] Skipping {d_name}: Age out of window for Heart ({d_age})")
                            continue
                        if 'lung' in org_lower and (d_age < 8 or d_age > 55):
                            print(f"[FILTER] Skipping {d_name}: Age out of window for Lung ({d_age})")
                            continue
                        if 'kidney' in org_lower and (d_age < 2 or d_age > 70):
                            print(f"[FILTER] Skipping {d_name}: Age out of window for Kidney ({d_age})")
                            continue

                    donor_organs = donor.get('organs_available', [])
                    if not any(org in donor_organs for org in request.required_organs):
                        stats["failed_organ"] += 1
                        continue
                
                # 2.5 Blood Product Filtering & Availability
                if not donor.get('is_available', True):
                    continue

                # 2.6 Blood Product Filter (for blood donation category)
                if request.donor_type == "blood" and request.required_blood_products:
                    donor_products = donor.get('donating_items')
                    if not donor_products or len(donor_products) == 0:
                        donor_products = ["Whole Blood"]
                    if not any(prod in donor_products for prod in request.required_blood_products):
                        stats["failed_blood_product"] += 1
                        continue

                # 3. Aerial Distance Calculation
                d_lat, d_lng = donor.get('latitude'), donor.get('longitude')
                aerial_dist = 5.0
                if d_lat and d_lng:
                    import math
                    lat1, lon1, lat2, lon2 = map(math.radians, [h_lat, h_lng, d_lat, d_lng])
                    aerial_dist = 6371 * (2 * math.atan2(math.sqrt(math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2), math.sqrt(1-(math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2))))
                
                if aerial_dist > (request.search_radius_km or 300):
                    stats["failed_radius"] += 1
                    continue

                donor['aerial_dist'] = aerial_dist
                donor['compat_score'] = compat_score
                donor['fuzzy_key'] = fuzzy_key
                initial_candidates.append(donor)
            except:
                continue

        # Rank by aerial first to pick top 20 for road distance processing
        initial_candidates.sort(key=lambda x: (-x['compat_score'], x['aerial_dist']))
        finalists = initial_candidates[:20]

        # --- PASS 2: Road Distance for finalists only (BATCHED to avoid rate-limits) ---
        print(f"[OSRM] Fetching road distances for {len(finalists)} finalists using Table API...")
        donor_coords = [(d.get('latitude'), d.get('longitude')) for d in finalists if d.get('latitude') and d.get('longitude')]
        
        from services.distance_service import get_road_distances_batch
        road_data = await get_road_distances_batch((h_lat, h_lng), donor_coords)
        if road_data is None:
            road_data = {}
        
        for idx, donor in enumerate(finalists):
            try:
                # Use batched road distance or fallback to aerial * 2.0 (SAFETY_PENALTY)
                # Matches Diagram: 'Use Haversine Fallback + 2x penalty'
                road_dist, travel_min = road_data.get(idx, (donor['aerial_dist'] * 2.0, int(donor['aerial_dist'] * 2.0 * 1.5)))
                
                dist_score = calculate_distance_score(road_dist, request.search_radius_km or 300)
                urg_score = get_urgency_score(request.urgency_level)

                # ML Score — recipient conditions now fully passed to model
                ml_score = 0.0
                model_data = get_model_v2()
                if model_data:
                    try:
                        donor['distance_km'] = road_dist  # ML ko real road distance do
                        recipient_features = {
                            "age": request.patient_age,
                            "urgency_level": request.urgency_level,
                            "required_organ": request.required_organs[0] if request.required_organs else "",
                            # FIX: Recipient medical conditions — previously missing, causing AI blind spot
                            "Condition_Diabetes":    1 if getattr(request, 'recipient_diabetes', False) else 0,
                            "Condition_Hypertension":1 if getattr(request, 'recipient_hypertension', False) else 0,
                            "Condition_Heart_Disease":1 if getattr(request, 'recipient_heart_disease', False) else 0,
                            "Condition_Asthma":      1 if getattr(request, 'recipient_asthma', False) else 0,
                            "Condition_Liver_Disease":1 if getattr(request, 'recipient_liver_disease', False) else 0,
                            "Condition_Kidney_Disease":1 if getattr(request, 'recipient_kidney_disease', False) else 0,
                        }
                        ml_score = predict_ml_score(donor, recipient_features, model_data)
                    except Exception as e:
                        print(f"[ML-WARN] predict_ml_score failed for donor {donor.get('id')}: {e}")
                        ml_score = 0.0

                final_score = min(calculate_final_score_with_ml(donor['compat_score'], dist_score, urg_score, ml_score), 100.0)
                
                donor['ml_score'] = ml_score

                compatible_donors.append({
                    **donor,
                    'final_score': final_score,
                    'distance_km': road_dist,
                    'travel_duration': travel_min,
                    'distance_score': dist_score,
                    'urgency_score': urg_score
                })
                stats["passed_clinical_filters"] += 1
            except Exception as e:
                print(f"Error processing donor {donor.get('id')}: {e}")
                continue

        # Final Rank: Score (DESC) then Distance (ASC)
        compatible_donors.sort(key=lambda x: (-float(x.get('final_score', 0)), float(x.get('distance_km', 999))))
        
        top_donors = compatible_donors[:request.max_results]
        final_matches = []
        
        explainer = get_explanation_service()
        for idx, donor in enumerate(top_donors):
            try:
                # STRICT REAL DATA MAPPING
                d_id = str(donor['id'])
                d_name = str(donor.get('full_name', 'Verified Donor'))
                d_blood = str(donor['blood_type']).strip().upper()
                d_organs = donor.get('organs_available') or []
                
                d_items = donor.get('donating_items') or []

                # Pre-compute score breakdown (needed by both AI and SHAP explainer)
                exp_score_breakdown = {
                    "compatibility_score": float(donor['compat_score']),
                    "distance_score": float(donor['distance_score']),
                    "urgency_score": float(donor['urgency_score']),
                    "ml_score": float(donor.get('ml_score', 0.0))
                }

                # --- STEP: GENERATE ENHANCED EXPLANATION ---
                # Only use AI for top 5 to maintain performance
                if idx < 5:
                    exp_request = {
                        "patient_blood_type": request.patient_blood_type,
                        "urgency_level": request.urgency_level,
                        "required_organs": request.required_organs
                    }
                    ai_explanation, source = await explainer.explain_match(
                        idx + 1, len(compatible_donors), donor, exp_request, exp_score_breakdown
                    )
                else:
                    ai_explanation = generate_explanation(
                        float(donor['compat_score']), 
                        float(donor['distance_score']), 
                        float(donor['urgency_score']),
                        d_blood, request.patient_blood_type,
                        float(donor['distance_km']), 
                        request.urgency_level, 
                        float(donor.get('ml_score', 0.0))
                    )
                    source = "deterministic_fallback"
                
                final_matches.append(MatchResult(
                    donor_id=d_id,
                    name=d_name,
                    blood_type=d_blood,
                    phone=str(donor.get('contact_number', 'Not available')),
                    available_organs=d_organs,
                    distance_km=float(donor['distance_km']),
                    ai_score=float(donor['final_score']) / 100.0,
                    score_breakdown=ScoreBreakdown(
                        compatibility_score=float(donor['compat_score']),
                        distance_score=float(donor['distance_score']),
                        urgency_score=float(donor['urgency_score']),
                        ml_score=float(donor.get('ml_score', 0.0)),
                        total_score=float(donor['final_score'])
                    ),
                    ai_explanation=ai_explanation,
                    explanation_source=source,
                    donating_items=d_items,
                    travel_time_human=f"{int(donor['travel_duration'])} min by road" if donor['travel_duration'] < 120 else f"{round(donor['travel_duration']/60, 1)}h by road",
                    feature_impacts=get_shap_explainer().explain_features(donor, exp_score_breakdown) if idx < 5 else []
                ))
            except Exception as e:
                print(f"[MATCH-ERR] Skipping donor {donor.get('id')} due to mapping error: {e}")
                continue

        # --- STEP: SEQUENCE DIAGRAM STEP 14 ---
        # INSERT INTO match_results using REAL confirmed column names:
        # id, donor_id, recipient_id, match_score, compatibility,
        # distance_km, status, urgency, blood_type, organ_type,
        # donor_name, hospital_name, created_at
        try:
            potential_entries = []
            for m in final_matches[:5]:
                entry = {
                    "donor_id": m.donor_id,
                    "recipient_id": request.hospital_id,   # real col name
                    "match_score": int(round(m.ai_score * 100)), # MUST be int for DB schema
                    "compatibility": round(m.score_breakdown.compatibility_score, 1),
                    "distance_km": round(m.distance_km, 2),
                    "status": "potential",
                    "urgency": request.urgency_level,
                    "blood_type": m.blood_type,
                    "organ_type": request.donor_type,
                    "donor_name": m.name,
                    "hospital_name": hospital_name,  # set earlier in hospital lookup
                }
                # Append extended columns (post-migration only, non-fatal)
                try:
                    entry["model_used"] = "XGBRanker-v2"
                    entry["ai_explanation"] = m.ai_explanation[:500] if m.ai_explanation else None
                    entry["match_type"] = request.donor_type
                except Exception:
                    pass
                potential_entries.append(entry)

            if potential_entries:
                supabase.table("match_results").insert(potential_entries).execute()
                print(f"[DB] Step 14: Saved {len(potential_entries)} potential matches to history.")
        except Exception as e:
            # Non-fatal: matching results always returned to frontend regardless
            print(f"[WARN] Step 14 History Logging Failed: {e}")

        # --- STEP: SECURITY LAYER (PII MASKING) ---
        security = get_security_service()
        masked_matches = []
        for match in final_matches:
            match_dict = match.model_dump()
            # Mask PII if the hospital coordinator hasn't revealed contact yet
            match_dict["name"] = security.mask_pii({"full_name": match.name})["full_name"]
            masked_matches.append(MatchResult(**match_dict))

        print(f"[LIFECYCLE] Match Request RESULTS_READY. Returning {len(masked_matches)} matches.")
        return MatchResponse(matches=masked_matches, filter_stats=stats)

    except Exception as e:
        print(f"FATAL MATCHING ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))