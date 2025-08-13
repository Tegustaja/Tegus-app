import requests
from dotenv import load_dotenv
import os

load_dotenv()
session_id = ""
url = f"http://localhost:8001/execute-step"
api_key = os.getenv("FLASK_API_KEY")  # Replace with your actual env variable name

headers = {
    "x-api-key": api_key,  # Optional, if your API expects this
    "Content-Type": "application/json"
}

data = {
    "session_id": session_id
}

response = requests.post(url, headers=headers, json=data)

print("Status Code:", response.status_code)
print("Response JSON:", response.text)