import requests
from dotenv import load_dotenv
import os
load_dotenv()
url = "http://localhost:8000/manus_response"
api_key = os.getenv("FLASK_API_KEY")  # Replace with your real API key
session_id = ""

headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

response = requests.post(
    f"{url}?session_id={session_id}",  # session_id as query parameter
    headers=headers
)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
