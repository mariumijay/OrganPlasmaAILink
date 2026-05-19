"""
Fix donor coordinates to match their actual registered city.
Currently ALL donors have Lahore-area coordinates regardless of their city.
"""
import os
import random
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('.env.local')
url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Actual city center coordinates for Pakistan's major cities
CITY_COORDS = {
    'lahore':     (31.5204, 74.3587),
    'karachi':    (24.8607, 67.0011),
    'islamabad':  (33.6844, 73.0479),
    'rawalpindi': (33.5651, 73.0169),
    'faisalabad': (31.4504, 73.1350),
    'multan':     (30.1575, 71.5249),
    'peshawar':   (34.0151, 71.5249),
    'quetta':     (30.1798, 66.9750),
    'hyderabad':  (25.3960, 68.3578),
    'sialkot':    (32.4945, 74.5229),
    'gujranwala': (32.1877, 74.1945),
}

def add_jitter(lat, lng, range_km=8):
    """Add random offset within range_km to make donors spread realistically."""
    # ~0.009 degrees per km
    deg_per_km = 0.009
    max_deg = deg_per_km * range_km
    return (
        lat + random.uniform(-max_deg, max_deg),
        lng + random.uniform(-max_deg, max_deg)
    )

# Fetch ALL approved/verified donors
res = supabase.table('donors').select('id, full_name, city, latitude, longitude').in_('approval_status', ['approved', 'verified']).execute()

updated = 0
skipped = 0

for donor in res.data:
    city = (donor.get('city') or '').strip().lower()
    
    if city not in CITY_COORDS:
        print(f"  [SKIP] {donor['full_name']} - unknown city '{city}'")
        skipped += 1
        continue
    
    base_lat, base_lng = CITY_COORDS[city]
    current_lat = donor.get('latitude')
    current_lng = donor.get('longitude')
    
    # Check if coordinates are already correct for this city (within ~50km)
    if current_lat and current_lng:
        dist = ((current_lat - base_lat)**2 + (current_lng - base_lng)**2)**0.5
        if dist < 0.5:  # Already close enough to their city (~55km)
            print(f"  [OK] {donor['full_name']} ({city}) - coords already correct")
            skipped += 1
            continue
    
    # Generate realistic coordinates for their actual city
    new_lat, new_lng = add_jitter(base_lat, base_lng)
    
    supabase.table('donors').update({
        'latitude': new_lat,
        'longitude': new_lng
    }).eq('id', donor['id']).execute()
    
    print(f"  [FIXED] {donor['full_name']} ({city}): ({current_lat}, {current_lng}) -> ({new_lat:.4f}, {new_lng:.4f})")
    updated += 1

print(f"\nDone! Updated: {updated}, Skipped: {skipped}, Total: {len(res.data)}")
