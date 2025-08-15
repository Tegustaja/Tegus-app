from fastapi import APIRouter, Header, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import time
import uuid
import json
import datetime
import logging
from typing import Dict, List, Optional, Union

from app.schema import Message
from app.agent.manus import Manus
from app.tool import ToolCollection
from app.flow.base import FlowType
from app.flow.flow_factory import FlowFactory
from app.logger import logger
from app.backtofront.connect_db import get_data
from app.flow.planning import PlanningFlow
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.web_search import WebSearch
from app.tool.rag_model import RagSearch
from app.agent.base import BaseAgent
from app.tool.test_rag import rag
from app.llm import LLM

# Import auth routes
from .auth import router as auth_router
# Import subjects routes
from .subjects import router as subjects_router
# Import lessons routes
from .lessons import router as lessons_router
# Import exercises routes
from .exercises import router as exercises_router
# Import quizzes routes
from .quizzes import router as quizzes_router
# Import progress routes
from .progress import router as progress_router
# Import content routes
from .content import router as content_router
# Import settings routes
from .settings import router as settings_router
# Import adaptive learning routes
from .adaptive_learning import router as adaptive_learning_router
# Import admin routes
from .admin import router as admin_router
# Import development utilities routes
from .dev_utils import router as dev_utils_router
# Import personalized lesson structure routes
from .lesson_parts import router as lesson_parts_router
from .personalized_exercises import router as personalized_exercises_router
from .subtasks import router as subtasks_router
from .personalized_progress import router as personalized_progress_router
from .lesson_extensions import router as lesson_extensions_router

# Create main router
router = APIRouter()

# Include auth routes
router.include_router(auth_router, tags=["Authentication"])
# Include subjects routes
router.include_router(subjects_router, tags=["Subjects"])
# Include lessons routes
router.include_router(lessons_router, tags=["Lessons"])
# Include exercises routes
router.include_router(exercises_router, tags=["Exercises"])
# Include quizzes routes
router.include_router(quizzes_router, tags=["Quizzes"])
# Include progress routes
router.include_router(progress_router, tags=["Progress"])
# Include content routes
router.include_router(content_router, tags=["Content"])
# Include settings routes
router.include_router(settings_router, tags=["Settings"])
# Include adaptive learning routes
router.include_router(adaptive_learning_router, tags=["Adaptive Learning"])
# Include admin routes
router.include_router(admin_router, tags=["Admin"])
# Include development utilities routes
router.include_router(dev_utils_router, tags=["Development Utilities"])

# Include personalized lesson structure routes
router.include_router(lesson_parts_router, tags=["Lesson Parts"])
router.include_router(personalized_exercises_router, tags=["Personalized Exercises"])
router.include_router(subtasks_router, tags=["Subtasks"])
router.include_router(personalized_progress_router, tags=["Personalized Progress"])
router.include_router(lesson_extensions_router, tags=["Lesson Extensions"])

# Models
class PlanRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = Field(default_factory=lambda: f"session_{int(time.time())}")

class StepRequest(BaseModel):
    step_id: int
    session_id: str

class RagRequest(BaseModel):
    query: str

class RagResponse(BaseModel):
    response: str

class Teacher(BaseModel):
    query: str

# Response model to include session_id
class PlanResponse(BaseModel):
    session_id: str
    plan: str

# Simple agent for basic operations
class SimpleAgent(BaseAgent):
    """A simple concrete implementation of BaseAgent."""
    
    async def step(self) -> str:
        """Implementation of the abstract step method."""
        # Use the last message in memory or a default message
        last_message = self.memory.messages[-1].content if self.memory.messages else "No input"
        
        # If the message starts with "Please provide a direct answer to:", remove that part
        if last_message.startswith("Please provide a direct answer to:"):
            task = last_message.replace("Please provide a direct answer to:", "").strip()
            return f"Here's the answer to your question: {task}"
            
        return last_message

# Initialize agents
simple_agent = SimpleAgent(name="SimpleAgent")
agents = {"manus": Manus()}

# Route handlers
@router.get("/")
async def index():
    logger.debug("debug log info")
    logger.info("Info log information")
    logger.warning("Warning log info")
    logger.error("Error log info")
    logger.critical("Critical log info")
    return {"message": "Hello from FastAPI"}

@router.post("/secure-endpoint")
async def secure_route(x_api_key: str = Header(None)):
    # This would need the API_KEY from environment
    API_KEY = "default-keasdfalsfjadsfkdakfkdsy"  # Should come from env
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"message": "Access granted"}

@router.post("/create-plan", response_model=PlanResponse)
async def create_plan(request: PlanRequest):
    flow = FlowFactory.create_flow(
        flow_type=FlowType.PLANNING,
        agents=agents,
    )
    session_id = str(uuid.uuid4())  # Generate UUID
    plan_text = await flow.execute(input_text=request.prompt, session_id=session_id)
    return PlanResponse(session_id=session_id, plan=plan_text)

async def run_execute(session_id: str, step_id: int):
    agents = {"manus": Manus()}
    planning_flow = PlanningFlow(agents=agents)
    return await planning_flow._execute_step(executor=agents, session_id=session_id, step_id=step_id)

@router.post("/execute-step", response_model=str)
async def execute_step(request: StepRequest, background_task: BackgroundTasks):
    try:
        background_task.add_task(run_execute, session_id=request.session_id, step_id=request.step_id)
        response = {"session_id": request.session_id,
                   "step": request.step_id,
                   "status": "completed"}
        return json.dumps(response)
        
    except Exception as e:
        logger.error(f"Error executing step: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the backend is running properly
    """
    try:
        # Basic health check - you can add more sophisticated checks here
        # like database connectivity, external service availability, etc.
        return {
            "status": "healthy",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "service": "Tegus Backend API",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@router.post("/rag")
async def get_rag(request: RagRequest):
    results = rag(request.query)
    return await results

@router.post("/teacher")
async def ask_teacher(request: Teacher):
    ASK_TEACHER_POMPT = Message.system_message("""Sa oled väga hea abiõpetaja ja suudad vastata kõikidel kasutaja küsimustele. Vasta lühidalt ja otsekoheselt. Hoia vastused lihtsad ja vast kuni 10klassi teadmiste piires""")
    USER_ASK_TEACHER = Message.user_message(f"""Palun vasta minu küsimusele: {request.query}""")
    opetaja = LLM()
    return await opetaja.ask(
        messages=[USER_ASK_TEACHER],
        system_msgs=[ASK_TEACHER_POMPT]
    ) 