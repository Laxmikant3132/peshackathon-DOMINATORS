import requests
import json

def test_api():
    url = "http://127.0.0.1:8000/api/analyze-abuse"
    payload = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    try:
        print(f"Testing {url}...")
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
