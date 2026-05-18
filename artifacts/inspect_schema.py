import os
from dotenv import load_dotenv
import requests

load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def get_columns(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*&limit=1"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Prefer": "return=minimal"
    }
    # We use a trick to get column names by requesting the OpenAPI spec
    spec_url = f"{SUPABASE_URL}/rest/v1/"
    res = requests.get(spec_url, headers=headers)
    if res.status_code == 200:
        spec = res.json()
        definitions = spec.get("definitions", {})
        print(f"Total tables found: {len(definitions)}")
        print(f"Tables: {list(definitions.keys())}")
        table_def = definitions.get(table, {})
        properties = table_def.get("properties", {})
        return list(properties.keys())
    return []

if __name__ == "__main__":
    print(f"Donors columns: {get_columns('donors')}")
    print(f"Donor Profiles columns: {get_columns('donor_profiles')}")
    print(f"Hospitals columns: {get_columns('hospitals')}")
