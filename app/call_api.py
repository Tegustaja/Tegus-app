import requests
from dotenv import load_dotenv
import os

load_dotenv()
#session_id = "7960679d-a571-4cd7-b7ea-f41ceb2ac784"
url = f"http://localhost:8000/create-plan"
api_key = os.getenv("FLASK_API_KEY")  # Replace with your actual env variable name

headers = {
    "x-api-key": api_key,  # Optional, if your API expects this
    "Content-Type": "application/json"
}

data = {
    "prompt": "Seleta mulle mis vahe on nõgusläätsel ja kumerläätsel?",
}

response = requests.post(url, headers=headers, json=data)

print("Status Code:", response.status_code)
print("Response JSON:", response.text)


