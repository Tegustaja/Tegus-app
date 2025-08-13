import asyncio
import time
from flask import jsonify

from app.agent.manus import Manus
from app.flow.base import FlowType
from app.flow.flow_factory import FlowFactory
from app.logger import logger



async def run_flow(prompt:str):
    agents = {
        "manus": Manus(),
    }
    flow = FlowFactory.create_flow(
        flow_type=FlowType.PLANNING,
        agents=agents,
    )
    logger.warning("Processing your request...")
    try:
        await asyncio.wait_for(
        flow.execute(prompt),
        timeout=3600,
        )
        return "User request has been processed"
    except Exception as e:
        logger.error(f"Error: {str(e)}")

