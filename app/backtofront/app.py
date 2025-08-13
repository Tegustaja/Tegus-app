import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv, find_dotenv
import asyncio

from app.agent.manus import Manus
from app.flow.base import FlowType
from app.flow.flow_factory import FlowFactory
from app.logger import logger





# Load environment variables from .env file
load_dotenv(find_dotenv())

import logging

logging.basicConfig(filename='/opt/logs/record.log', level=logging.DEBUG)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


# Get API key from .env file
API_KEY = os.getenv("FLASK_API_KEY", "default-keasdfalsfjadsfkdakfkdsy")

def verify_api_key(api_key):
    if api_key != API_KEY:
        return False
    return True


@app.route('/', methods=['GET'])
def indes():
    app.logger.debug("debug log info")
    app.logger.info("Info log information")
    app.logger.warning("Warning log info")
    app.logger.error("Error log info")
    app.logger.critical("Critical log info")

    return 'hello'

@app.route('/secure-endpoint', methods=['GET','POST'])
def secure_route():
    api_key = request.headers.get("X-API-Key")  # Get API key from headers
    if not api_key or not verify_api_key(api_key):
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({"message": "Access granted"})


@app.route('/manus_response', methods=['GET','POST'])
async def run_flow(prompt:str):
    if secure_route():
        agents = {
            "manus": Manus(),
        }
        flow = FlowFactory.create_flow(
            flow_type=FlowType.PLANNING,
            agents=agents,
        )
        result = await asyncio.wait_for(
                    flow.execute(prompt),
                    timeout=3600,  # 60 minute timeout for the entire execution
                )
        return jsonify({"message": "Response has been completed succesfuly!"})