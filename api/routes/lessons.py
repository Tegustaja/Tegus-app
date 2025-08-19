from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv
import asyncio
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter(prefix="/lessons")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class CreateSessionRequest(BaseModel):
    user_id: str
    topic_id: str
    focus_area: Optional[str] = None
    proficiency_level: Optional[str] = None
    title: Optional[str] = None

class LessonPlanRequest(BaseModel):
    user_id: str
    topic_id: str
    subject: str
    focus_area: Optional[str] = None
    proficiency_level: Optional[str] = None
    custom_prompt: Optional[str] = None

class LessonPlanResponse(BaseModel):
    session_id: str
    status: str
    message: str
    plan_ready: bool = False

class ConfirmLessonPlanRequest(BaseModel):
    session_id: str
    user_id: str

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    topic_id: str
    title: Optional[str] = None
    focus_area: Optional[str] = None
    proficiency_level: Optional[str] = None
    steps: Optional[Dict[str, Any]] = None
    step_statuses: Optional[Dict[str, Any]] = None
    step_responses: Optional[Dict[str, Any]] = None
    steps_feedback: Optional[Dict[str, Any]] = None
    start_time: Optional[str] = None
    last_active: Optional[str] = None
    is_completed: bool = False
    completed_at: Optional[str] = None
    current_database_index: Optional[int] = None
    created_at: Optional[str] = None
    plan_status: Optional[str] = None  # 'creating', 'ready', 'confirmed', 'in_progress'

class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    focus_area: Optional[str] = None
    proficiency_level: Optional[str] = None
    steps: Optional[Dict[str, Any]] = None
    step_statuses: Optional[Dict[str, Any]] = None
    step_responses: Optional[Dict[str, Any]] = None
    steps_feedback: Optional[Dict[str, Any]] = None
    is_completed: Optional[bool] = None
    completed_at: Optional[str] = None
    current_database_index: Optional[int] = None

class ProgressResponse(BaseModel):
    user_id: str
    topic_id: str
    progress: int  # 0-100
    last_accessed: str
    completed_at: Optional[str] = None
    created_at: str

class SessionMessage(BaseModel):
    id: str
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    created_at: str

@router.post("/sessions", response_model=SessionResponse)
async def create_lesson_session(request: CreateSessionRequest):
    """
    Create new lesson session
    """
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create session data
        session_data = {
            "session_id": session_id,
            "user_id": request.user_id,
            "topic_id": request.topic_id,
            "title": request.title,
            "focus_area": request.focus_area,
            "proficiency_level": request.proficiency_level,
            "steps": {},
            "step_statuses": {},
            "step_responses": {},
            "steps_feedback": {},
            "start_time": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
            "is_completed": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert into lessons table
        response = supabase.table("Lessons").insert(session_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create lesson session"
            )
        
        created_session = response.data[0]
        
        # Create or update user progress for this topic
        progress_data = {
            "user_id": request.user_id,
            "topic_id": request.topic_id,
            "progress": 0,
            "last_accessed": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Check if progress record exists
        existing_progress = supabase.table("user_progress").select("*").eq("user_id", request.user_id).eq("topic_id", request.topic_id).execute()
        
        if existing_progress.data:
            # Update existing progress
            supabase.table("user_progress").update({
                "last_accessed": datetime.utcnow().isoformat()
            }).eq("user_id", request.user_id).eq("topic_id", request.topic_id).execute()
        else:
            # Create new progress record
            supabase.table("user_progress").insert(progress_data).execute()
        
        return SessionResponse(**created_session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lesson session: {str(e)}"
        )

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_lesson_session(session_id: str):
    """
    Get lesson session details
    """
    try:
        response = supabase.table("Lessons").select("*").eq("session_id", session_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson session with ID {session_id} not found"
            )
        
        return SessionResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch lesson session: {str(e)}"
        )

@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_lesson_session(session_id: str, request: UpdateSessionRequest):
    """
    Update lesson session progress
    """
    try:
        # First verify the session exists
        existing_session = supabase.table("Lessons").select("session_id").eq("session_id", session_id).execute()
        
        if not existing_session.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson session with ID {session_id} not found"
            )
        
        # Prepare update data
        update_data = {
            "last_active": datetime.utcnow().isoformat()
        }
        
        # Add fields that were provided
        if request.title is not None:
            update_data["title"] = request.title
        if request.focus_area is not None:
            update_data["focus_area"] = request.focus_area
        if request.proficiency_level is not None:
            update_data["proficiency_level"] = request.proficiency_level
        if request.steps is not None:
            update_data["steps"] = request.steps
        if request.step_statuses is not None:
            update_data["step_statuses"] = request.step_statuses
        if request.step_responses is not None:
            update_data["step_responses"] = request.step_responses
        if request.steps_feedback is not None:
            update_data["steps_feedback"] = request.steps_feedback
        if request.is_completed is not None:
            update_data["is_completed"] = request.is_completed
            if request.is_completed:
                update_data["completed_at"] = datetime.utcnow().isoformat()
        if request.current_database_index is not None:
            update_data["current_database_index"] = request.current_database_index
        
        # Update the session
        response = supabase.table("Lessons").update(update_data).eq("session_id", session_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update lesson session"
            )
        
        # If session is completed, update user progress
        if request.is_completed:
            session_data = response.data[0]
            user_id = session_data.get("user_id")
            topic_id = session_data.get("topic_id")
            
            if user_id and topic_id:
                # Update progress to 100% when completed
                supabase.table("user_progress").update({
                    "progress": 100,
                    "completed_at": datetime.utcnow().isoformat(),
                    "last_accessed": datetime.utcnow().isoformat()
                }).eq("user_id", user_id).eq("topic_id", topic_id).execute()
        
        return SessionResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lesson session: {str(e)}"
        )

@router.get("/sessions/{session_id}/progress", response_model=ProgressResponse)
async def get_session_progress(session_id: str):
    """
    Get user progress for a topic from a session
    """
    try:
        # First get the session to find user_id and topic_id
        session_response = supabase.table("Lessons").select("user_id, topic_id").eq("session_id", session_id).execute()
        
        if not session_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson session with ID {session_id} not found"
            )
        
        session = session_response.data[0]
        user_id = session["user_id"]
        topic_id = session["topic_id"]
        
        # Get user progress for this topic
        progress_response = supabase.table("user_progress").select("*").eq("user_id", user_id).eq("topic_id", topic_id).execute()
        
        if not progress_response.data:
            # Create default progress record if none exists
            progress_data = {
                "user_id": user_id,
                "topic_id": topic_id,
                "progress": 0,
                "last_accessed": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("user_progress").insert(progress_data).execute()
            
            return ProgressResponse(**progress_data)
        
        return ProgressResponse(**progress_response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session progress: {str(e)}"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[SessionMessage])
async def get_session_messages(session_id: str):
    """
    Get all messages for a lesson session
    """
    try:
        # Verify session exists
        session_response = supabase.table("Lessons").select("session_id").eq("session_id", session_id).execute()
        
        if not session_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson session with ID {session_id} not found"
            )
        
        # Get messages for this session
        messages_response = supabase.table("session_messages").select("*").eq("session_id", session_id).order("created_at").execute()
        
        if not messages_response.data:
            return []
        
        return [SessionMessage(**message) for message in messages_response.data]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session messages: {str(e)}"
        )

@router.post("/sessions/{session_id}/messages")
async def add_session_message(session_id: str, role: str, content: str):
    """
    Add a message to a lesson session
    """
    try:
        # Verify session exists
        session_response = supabase.table("Lessons").select("session_id").eq("session_id", session_id).execute()
        
        if not session_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson session with ID {session_id} not found"
            )
        
        # Validate role
        if role not in ["user", "assistant"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be either 'user' or 'assistant'"
            )
        
        # Create message
        message_data = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("session_messages").insert(message_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add message"
            )
        
        return {"message": "Message added successfully", "id": response.data[0]["id"]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )

@router.post("/create-plan", response_model=LessonPlanResponse)
async def create_lesson_plan(request: LessonPlanRequest):
    """
    Create a lesson plan using the manus process
    This endpoint starts the openmanus process to create an adaptive lesson plan
    """
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create initial session data
        session_data = {
            "session_id": session_id,
            "user_id": request.user_id,
            "topic_id": request.topic_id,
            "title": f"Lesson Plan for {request.subject} - {request.topic_id}",
            "focus_area": request.focus_area,
            "proficiency_level": request.proficiency_level,
            "plan_status": "creating",
            "start_time": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
            "is_completed": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert into lessons table
        response = supabase.table("Lessons").insert(session_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create lesson session"
            )
        
        # Create or update user progress for this topic
        progress_data = {
            "user_id": request.user_id,
            "topic_id": request.topic_id,
            "progress": 0,
            "last_accessed": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Check if progress record exists
        existing_progress = supabase.table("user_progress").select("*").eq("user_id", request.user_id).eq("topic_id", request.topic_id).execute()
        
        if existing_progress.data:
            # Update existing progress
            supabase.table("user_progress").update({
                "last_accessed": datetime.utcnow().isoformat()
            }).eq("user_id", request.user_id).eq("topic_id", request.topic_id).execute()
        else:
            # Create new progress record
            supabase.table("user_progress").insert(progress_data).execute()
        
        # Start the manus process to create the lesson plan
        # This will run asynchronously in the background
        asyncio.create_task(_create_lesson_plan_background(session_id, request))
        
        return LessonPlanResponse(
            session_id=session_id,
            status="creating",
            message="Lesson plan creation started. The plan will be ready shortly.",
            plan_ready=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lesson plan: {str(e)}"
        )

async def _create_lesson_plan_background(session_id: str, request: LessonPlanRequest):
    """
    Background task to create the lesson plan using the manus process
    """
    try:
        # Import the planning flow here to avoid circular imports
        from app.flow.planning import PlanningFlow
        from app.agent.manus import Manus
        
        # Create the planning flow with manus agent
        agents = {"manus": Manus()}
        flow = PlanningFlow(agents=agents, session_id=session_id)
        
        # Create the prompt for lesson plan creation
        prompt = f"""
        Create a personalized lesson plan for learning {request.topic_id} in {request.subject}.
        
        Student Information:
        - Focus Area: {request.focus_area or 'General understanding'}
        - Proficiency Level: {request.proficiency_level or 'Beginner'}
        
        Custom Requirements: {request.custom_prompt or 'None'}
        
        Please create a comprehensive lesson plan with clear steps that will help the student learn this topic effectively.
        Focus on practical understanding rather than just memorization.
        """
        
        # Execute the planning flow
        result = await flow.execute(prompt, session_id)
        
        # Update the session status to indicate plan is ready
        supabase.table("Lessons").update({
            "plan_status": "ready",
            "last_active": datetime.utcnow().isoformat()
        }).eq("session_id", session_id).execute()
        
        logger.info(f"Lesson plan created successfully for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error creating lesson plan for session {session_id}: {str(e)}")
        # Update session status to indicate error
        try:
            supabase.table("Lessons").update({
                "plan_status": "error",
                "last_active": datetime.utcnow().isoformat()
            }).eq("session_id", session_id).execute()
        except Exception as update_error:
            logger.error(f"Failed to update error status: {update_error}")

@router.post("/confirm-plan", response_model=LessonPlanResponse)
async def confirm_lesson_plan(request: ConfirmLessonPlanRequest):
    """
    Confirm the lesson plan and start the lesson process
    This endpoint is called when the user presses the "KINNITA TUNNI PLAAN" button
    """
    try:
        # Verify the session exists and plan is ready
        session_response = supabase.table("Lessons").select("*").eq("session_id", request.session_id).execute()
        
        if not session_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson session with ID {request.session_id} not found"
            )
        
        session_data = session_response.data[0]
        
        # Verify the user owns this session
        if session_data.get("user_id") != request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only confirm your own lesson plans"
            )
        
        # Check if plan is ready
        if session_data.get("plan_status") != "ready":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lesson plan is not ready. Current status: {session_data.get('plan_status')}"
            )
        
        # Update session status to confirmed and start lesson
        supabase.table("Lessons").update({
            "plan_status": "confirmed",
            "last_active": datetime.utcnow().isoformat()
        }).eq("session_id", request.session_id).execute()
        
        # Start the lesson execution process
        asyncio.create_task(_start_lesson_execution(request.session_id))
        
        return LessonPlanResponse(
            session_id=request.session_id,
            status="confirmed",
            message="Lesson plan confirmed! Starting the lesson process.",
            plan_ready=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm lesson plan: {str(e)}"
        )

async def _start_lesson_execution(session_id: str):
    """
    Background task to start the lesson execution process
    """
    try:
        # Import the planning flow here to avoid circular imports
        from app.flow.planning import PlanningFlow
        from app.agent.manus import Manus
        
        # Get the lesson data
        session_response = supabase.table("Lessons").select("*").eq("session_id", session_id).execute()
        if not session_response.data:
            logger.error(f"No lesson data found for session {session_id}")
            return
        
        lesson_data = session_response.data[0]
        steps = lesson_data.get("steps", [])
        
        if not steps:
            logger.error(f"No steps found in lesson plan for session {session_id}")
            return
        
        # Create the planning flow with manus agent
        agents = {"manus": Manus()}
        flow = PlanningFlow(agents=agents, session_id=session_id)
        
        # Update status to in progress
        supabase.table("Lessons").update({
            "plan_status": "in_progress",
            "last_active": datetime.utcnow().isoformat()
        }).eq("session_id", session_id).execute()
        
        # Execute the first step to start the lesson
        if steps:
            first_step_result = await flow._execute_step(flow.get_executor(), session_id, 0)
            logger.info(f"Started lesson execution for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error starting lesson execution for session {session_id}: {str(e)}")
        # Update session status to indicate error
        try:
            supabase.table("Lessons").update({
                "plan_status": "error",
                "last_active": datetime.utcnow().isoformat()
            }).eq("session_id", session_id).execute()
        except Exception as update_error:
            logger.error(f"Failed to update error status: {update_error}")

@router.get("/plan-status/{session_id}")
async def get_plan_status(session_id: str):
    """
    Get the current status of a lesson plan
    """
    try:
        response = supabase.table("Lessons").select("plan_status, steps, step_statuses, step_responses").eq("session_id", session_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson session with ID {session_id} not found"
            )
        
        lesson_data = response.data[0]
        
        return {
            "session_id": session_id,
            "plan_status": lesson_data.get("plan_status", "unknown"),
            "steps": lesson_data.get("steps", []),
            "step_statuses": lesson_data.get("step_statuses", []),
            "step_responses": lesson_data.get("step_responses", []),
            "plan_ready": lesson_data.get("plan_status") == "ready"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plan status: {str(e)}"
        )
