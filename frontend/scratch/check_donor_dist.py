import os
from supabase import create_client

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(url, key)

res = supabase.table("donors").select("city, latitude, longitude").execute()
cities = {}
for d in res.data:
    city = d.get('city', 'Unknown')
    cities[city] = cities.get(city, 0) + 1

print("Donor Distribution by City:")
for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True):
    print(f"  {city}: {count}")

# Check sample coords for Karachi
karachi = [d for d in res.data if d.get('city') == 'Karachi']
if karachi:
    print(f"\nSample Karachi Coords: {karachi[0]['latitude']}, {karachi[0]['longitude']}")
