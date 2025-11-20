import requests
import json

def test_api():
    url = "http://localhost:8000/api/v1/ask"
    payload = {
        "question": "What is DGFT?",
        "user_id": "test"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = test_api()
    if result:
        print("SUCCESS!")
        print(json.dumps(result, indent=2))
    else:
        print("FAILED!")