import os
from dotenv import load_dotenv
import requests

load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def get_columns(table):
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    spec_url = f"{SUPABASE_URL}/rest/v1/"
    res = requests.get(spec_url, headers=headers)
    if res.status_code == 200:
        spec = res.json()
        definitions = spec.get("definitions", {})
        table_def = definitions.get(table, {})
        properties = table_def.get("properties", {})
        return list(properties.keys())
    return []

if __name__ == "__main__":
    print(f"organ_requests columns: {get_columns('organ_requests')}")
