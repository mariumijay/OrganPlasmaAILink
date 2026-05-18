import httpx
import logging
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)

# Simple in-memory cache to avoid redundant OSRM calls
# Key: (lat1, lon1, lat2, lon2), Value: (distance_km, duration_mins)
_distance_cache: Dict[Tuple[float, float, float, float], Tuple[float, int]] = {}

async def get_road_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, int]:
    """
    Fetches real road distance and estimated travel time using the OSRM API.
    Returns: (distance_in_km, duration_in_minutes)
    """
    # Round coordinates to 4 decimal places (~11 meters precision) for better cache hits
    coords = (round(lat1, 4), round(lon1, 4), round(lat2, 4), round(lon2, 4))
    
    if coords in _distance_cache:
        return _distance_cache[coords]

    # OSRM expects format: lon,lat;lon,lat
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    distance_km = round(route["distance"] / 1000.0, 2)
                    duration_min = round(route["duration"] / 60.0)
                    
                    _distance_cache[coords] = (distance_km, int(duration_min))
                    return distance_km, int(duration_min)
                
            logger.warning(f"OSRM API returned error: {response.text}")
    except Exception as e:
        logger.error(f"Failed to fetch road distance from OSRM: {e}")

    # Fallback to a very rough approximation (aerial * 1.3) if API fails
    import math
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2-lat1)
    dlambda = math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    aerial_dist = R * c
    
    # 1.3 is a common multiplier for road distance vs aerial distance
    return round(aerial_dist * 1.3, 2), int(aerial_dist * 2) 

async def get_road_distances_batch(hospital_coords: Tuple[float, float], donor_coords_list: list[Tuple[float, float]]) -> Dict[int, Tuple[float, int]]:
    """
    Uses the OSRM Table API to fetch distances and durations for many donors in one request.
    """
    if not donor_coords_list:
        return {}

    try:
        # OSRM expects: lon,lat;lon,lat;...
        h_lat, h_lon = hospital_coords
        coords_str = f"{h_lon},{h_lat}"
        for d_lat, d_lon in donor_coords_list:
            if d_lat is not None and d_lon is not None:
                coords_str += f";{d_lon},{d_lat}"

        url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?sources=0&annotations=distance,duration"
        print(f"[OSRM] Requesting Table API: {url[:100]}...")

        results = {}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            print(f"[OSRM] Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "Ok":
                    distances = data.get("distances", [[]])[0]
                    durations = data.get("durations", [[]])[0]
                    
                    for i in range(1, len(distances)):
                        dist_km = round(distances[i] / 1000.0, 2) if (i < len(distances) and distances[i] is not None) else 0.0
                        dur_min = round(durations[i] / 60.0) if (i < len(durations) and durations[i] is not None) else 0
                        results[i-1] = (dist_km, int(dur_min))
                    
                    print(f"[OSRM] Successfully fetched {len(results)} distances.")
                    return results
            
            print(f"[OSRM] API Error: {response.text[:200]}")
    except Exception as e:
        print(f"[OSRM] Exception in batch request: {str(e)}")

    # Fallback to rough approximations if Table API fails
    print("[OSRM] Falling back to aerial approximations...")
    import math
    R = 6371.0
    results = {}
    for idx, (d_lat, d_lon) in enumerate(donor_coords_list):
        if d_lat is None or d_lon is None:
            results[idx] = (0.0, 0)
            continue
        phi1, phi2 = math.radians(h_lat), math.radians(d_lat)
        dphi = math.radians(d_lat - h_lat)
        dlambda = math.radians(d_lon - h_lon)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        aerial = R * c
        results[idx] = (round(aerial * 2.0, 2), int(aerial * 3))  # 2x SAFETY_PENALTY per diagram
        
    return results
