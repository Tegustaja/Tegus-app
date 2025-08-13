import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from app.tool.answering import chatbot_response

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get API key from .env file
API_KEY = os.getenv("FLASK_API_KEY", "default-key")

def verify_api_key(api_key):
    if api_key != API_KEY:
        return False
    return True

@app.route('/secure-endpoint', methods=['GET'])
def secure_route():
    api_key = request.headers.get("X-API-Key")  # Get API key from headers
    if not api_key or not verify_api_key(api_key):
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({"message": "Access granted"})


@app.route('/rag-response', methods=['GET'])
def get_response():
    if secure_route:
        query = request.args.get('query')
        return chatbot_response(query)
