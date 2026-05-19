import os
import requests
import json
import base64

def check_supabase(url, key):
    print(f"Checking Supabase: {url}")
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    try:
        # Just try to get the health or a simple table count if possible
        # We can try to decode the JWT first
        payload = key.split('.')[1]
        decoded = base64.b64decode(payload + '==').decode('utf-8')
        print(f"Supabase JWT Payload: {decoded}")
        
        # Test request
        response = requests.get(f"{url}/rest/v1/", headers=headers)
        print(f"Supabase Response Status: {response.status_code}")
        if response.status_code == 200:
            print("Supabase Key is VALID and server is UP")
        elif response.status_code == 521:
            print("Supabase project seems to be PAUSED or DOWN (Error 521)")
        else:
            print(f"Supabase Status: {response.status_code}. Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error checking Supabase: {e}")

def check_gemini(key):
    print(f"Checking Gemini API Key: {key[:5]}...{key[-5:]}")
    # Try v1 instead of v1beta
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": "Say hello"}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Gemini Response Status: {response.status_code}")
        if response.status_code == 200:
            print("Gemini API Key is VALID")
        elif response.status_code == 400:
            # If it's 400, it might be an invalid key or bad request. 
            # If it was an invalid key, it would usually be 403 or 401.
            # 400 with "API_KEY_INVALID" means it's invalid.
            print(f"Gemini API Key check returned 400. Response: {response.text}")
        else:
            print(f"Gemini API Key status: {response.status_code}. Response: {response.text}")
    except Exception as e:
        print(f"Error checking Gemini: {e}")

if __name__ == "__main__":
    # From backend/.env
    supabase_url = "https://qsmwlrywrjuudfjooqsz.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFzbXdscnl3cmp1dWRmam9vcXN6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQ2MzYyOSwiZXhwIjoyMDkxMDM5NjI5fQ.jNfTgIzcfXOZZQCBYsovQXWdLZtMegsSqD_gXpyOBs4"
    gemini_key = "AIzaSyCiu47JkLpfl0hP-T-NWCjxYSNruYW9Lws"
    
    check_supabase(supabase_url, supabase_key)
    print("-" * 20)
    check_gemini(gemini_key)
