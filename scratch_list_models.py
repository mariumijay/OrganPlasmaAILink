import requests

def list_models(key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    try:
        response = requests.get(url)
        print(f"List Models Status: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print("Available models:")
            for m in models.get('models', []):
                print(f" - {m['name']}")
        else:
            print(f"Error listing models: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    gemini_key = "AIzaSyCiu47JkLpfl0hP-T-NWCjxYSNruYW9Lws"
    list_models(gemini_key)
