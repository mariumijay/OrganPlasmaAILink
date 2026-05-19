import requests
import json

url = "http://127.0.0.1:8000/api/chat/ask"
payload = {
    "message": "hello",
    "role": "donor",
    "user_id": "test_user",
    "page_context": "home",
    "conversation_history": []
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
