import requests

SERVER_URL = "http://127.0.0.1:8000"

def send_request(endpoint, data):
    url = f"{SERVER_URL}/{endpoint}"
    response = requests.post(url, json=data)
    return response.json()