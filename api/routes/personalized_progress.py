from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter(prefix="/personalized-progress")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class CreateLessonPartProgressRequest(BaseModel):
    lesson_part_id: str
    user_id: str
    status: str = Field(default="not_started", description="not_started, in_progress, completed")
    progress_percentage: int = Field(default=0, ge=0, le=100, description="0-100 progress")
    time_spent_minutes: int = Field(default=0, ge=0, description="Time spent in minutes")

class UpdateLessonPartProgressRequest(BaseModel):
    status: Optional[str] = Field(None, description="not_started, in_progress, completed")
    progress_percentage: Optional[int] = Field(None, ge=0, le=100, description="0-100 progress")
    time_spent_minutes: Optional[int] = Field(None, ge=0, description="Time spent in minutes")

class CreateExerciseProgressRequest(BaseModel):
    exercise_id: str
    user_id: str
    status: str = Field(default="not_started", description="not_started, in_progress, completed, failed")
    attempts: int = Field(default=0, ge=0, description="Number of attempts")
    correct_attempts: int = Field(default=0, ge=0, description="Number of correct attempts")
    time_spent_minutes: int = Field(default=0, ge=0, description="Time spent in minutes")
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None

class UpdateExerciseProgressRequest(BaseModel):
    status: Optional[str] = Field(None, description="not_started, in_progress, completed, failed")
    attempts: Optional[int] = Field(None, ge=0, description="Number of attempts")
    correct_attempts: Optional[int] = Field(None, ge=0, description="Number of correct attempts")
    time_spent_minutes: Optional[int] = Field(None, ge=0, description="Time spent in minutes")
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    feedback_received: Optional[bool] = None

class CreateSubtaskProgressRequest(BaseModel):
    subtask_id: str
    user_id: str
    status: str = Field(default="not_started", description="not_started, in_progress, completed")
    time_spent_minutes: int = Field(default=0, ge=0, description="Time spent in minutes")

class UpdateSubtaskProgressRequest(BaseModel):
    status: Optional[str] = Field(None, description="not_started, in_progress, completed")
    time_spent_minutes: Optional[int] = Field(None, ge=0, description="Time spent in minutes")

class LessonPartProgressResponse(BaseModel):
    id: str
    lesson_part_id: str
    user_id: str
    status: str
    progress_percentage: int
    time_spent_minutes: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str
    updated_at: str

class ExerciseProgressResponse(BaseModel):
    id: str
    exercise_id: str
    user_id: str
    status: str
    attempts: int
    correct_attempts: int
    time_spent_minutes: int
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    feedback_received: bool
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str
    updated_at: str

class SubtaskProgressResponse(BaseModel):
    id: str
    subtask_id: str
    user_id: str
    status: str
    time_spent_minutes: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str
    updated_at: str

class UserProgressSummary(BaseModel):
    user_id: str
    lesson_id: str
    total_parts: int
    completed_parts: int
    total_exercises: int
    completed_exercises: int
    total_subtasks: int
    completed_subtasks: int
    overall_progress: int
    total_time_spent_minutes: int

# Lesson Part Progress Endpoints
@router.post("/lesson-part", response_model=LessonPartProgressResponse)
async def create_lesson_part_progress(request: CreateLessonPartProgressRequest):
    """
    Create or update progress for a lesson part
    """
    try:
        # Check if lesson part exists
        part_response = supabase.table("lesson_parts").select("id").eq("id", request.lesson_part_id).execute()
        if not part_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson part not found"
            )
        
        # Check if progress already exists
        existing_progress = supabase.table("lesson_part_progress").select("*").eq("lesson_part_id", request.lesson_part_id).eq("user_id", request.user_id).execute()
        
        if existing_progress.data:
            # Update existing progress
            progress_id = existing_progress.data[0]["id"]
            update_data = {
                "status": request.status,
                "progress_percentage": request.progress_percentage,
                "time_spent_minutes": request.time_spent_minutes,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if request.status == "in_progress" and not existing_progress.data[0]["started_at"]:
                update_data["started_at"] = datetime.utcnow().isoformat()
            elif request.status == "completed":
                update_data["completed_at"] = datetime.utcnow().isoformat()
            
            response = supabase.table("lesson_part_progress").update(update_data).eq("id", progress_id).execute()
        else:
            # Create new progress
            progress_data = {
                "id": str(uuid.uuid4()),
                "lesson_part_id": request.lesson_part_id,
                "user_id": request.user_id,
                "status": request.status,
                "progress_percentage": request.progress_percentage,
                "time_spent_minutes": request.time_spent_minutes,
                "started_at": datetime.utcnow().isoformat() if request.status != "not_started" else None,
                "completed_at": datetime.utcnow().isoformat() if request.status == "completed" else None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = supabase.table("lesson_part_progress").insert(progress_data).execute()
        
        if response.data:
            return LessonPartProgressResponse(**response.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create/update lesson part progress"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/lesson-part/{lesson_part_id}/user/{user_id}", response_model=LessonPartProgressResponse)
async def get_lesson_part_progress(lesson_part_id: str, user_id: str):
    """
    Get progress for a specific lesson part and user
    """
    try:
        response = supabase.table("lesson_part_progress").select("*").eq("lesson_part_id", lesson_part_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Progress not found"
            )
        
        return LessonPartProgressResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Exercise Progress Endpoints
@router.post("/exercise", response_model=ExerciseProgressResponse)
async def create_exercise_progress(request: CreateExerciseProgressRequest):
    """
    Create or update progress for an exercise
    """
    try:
        # Check if exercise exists
        exercise_response = supabase.table("exercises").select("id").eq("id", request.exercise_id).execute()
        if not exercise_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        # Check if progress already exists
        existing_progress = supabase.table("exercise_progress").select("*").eq("exercise_id", request.exercise_id).eq("user_id", request.user_id).execute()
        
        if existing_progress.data:
            # Update existing progress
            progress_id = existing_progress.data[0]["id"]
            update_data = {
                "status": request.status,
                "attempts": request.attempts,
                "correct_attempts": request.correct_attempts,
                "time_spent_minutes": request.time_spent_minutes,
                "user_answer": request.user_answer,
                "is_correct": request.is_correct,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if request.status == "in_progress" and not existing_progress.data[0]["started_at"]:
                update_data["started_at"] = datetime.utcnow().isoformat()
            elif request.status == "completed":
                update_data["completed_at"] = datetime.utcnow().isoformat()
            
            response = supabase.table("exercise_progress").update(update_data).eq("id", progress_id).execute()
        else:
            # Create new progress
            progress_data = {
                "id": str(uuid.uuid4()),
                "exercise_id": request.exercise_id,
                "user_id": request.user_id,
                "status": request.status,
                "attempts": request.attempts,
                "correct_attempts": request.correct_attempts,
                "time_spent_minutes": request.time_spent_minutes,
                "user_answer": request.user_answer,
                "is_correct": request.is_correct,
                "feedback_received": False,
                "started_at": datetime.utcnow().isoformat() if request.status != "not_started" else None,
                "completed_at": datetime.utcnow().isoformat() if request.status == "completed" else None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = supabase.table("exercise_progress").insert(progress_data).execute()
        
        if response.data:
            return ExerciseProgressResponse(**response.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create/update exercise progress"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/exercise/{exercise_id}/user/{user_id}", response_model=ExerciseProgressResponse)
async def get_exercise_progress(exercise_id: str, user_id: str):
    """
    Get progress for a specific exercise and user
    """
    try:
        response = supabase.table("exercise_progress").select("*").eq("exercise_id", exercise_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Progress not found"
            )
        
        return ExerciseProgressResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Subtask Progress Endpoints
@router.post("/subtask", response_model=SubtaskProgressResponse)
async def create_subtask_progress(request: CreateSubtaskProgressRequest):
    """
    Create or update progress for a subtask
    """
    try:
        # Check if subtask exists
        subtask_response = supabase.table("subtasks").select("id").eq("id", request.subtask_id).execute()
        if not subtask_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found"
            )
        
        # Check if progress already exists
        existing_progress = supabase.table("subtask_progress").select("*").eq("subtask_id", request.subtask_id).eq("user_id", request.user_id).execute()
        
        if existing_progress.data:
            # Update existing progress
            progress_id = existing_progress.data[0]["id"]
            update_data = {
                "status": request.status,
                "time_spent_minutes": request.time_spent_minutes,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if request.status == "in_progress" and not existing_progress.data[0]["started_at"]:
                update_data["started_at"] = datetime.utcnow().isoformat()
            elif request.status == "completed":
                update_data["completed_at"] = datetime.utcnow().isoformat()
            
            response = supabase.table("subtask_progress").update(update_data).eq("id", progress_id).execute()
        else:
            # Create new progress
            progress_data = {
                "id": str(uuid.uuid4()),
                "subtask_id": request.subtask_id,
                "user_id": request.user_id,
                "status": request.status,
                "time_spent_minutes": request.time_spent_minutes,
                "started_at": datetime.utcnow().isoformat() if request.status != "not_started" else None,
                "completed_at": datetime.utcnow().isoformat() if request.status == "completed" else None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = supabase.table("subtask_progress").insert(progress_data).execute()
        
        if response.data:
            return SubtaskProgressResponse(**response.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create/update subtask progress"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/subtask/{subtask_id}/user/{user_id}", response_model=SubtaskProgressResponse)
async def get_subtask_progress(subtask_id: str, user_id: str):
    """
    Get progress for a specific subtask and user
    """
    try:
        response = supabase.table("subtask_progress").select("*").eq("subtask_id", subtask_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Progress not found"
            )
        
        return SubtaskProgressResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Progress Summary Endpoints
@router.get("/user/{user_id}/lesson/{lesson_id}/summary", response_model=UserProgressSummary)
async def get_user_lesson_progress_summary(user_id: str, lesson_id: str):
    """
    Get overall progress summary for a user in a specific lesson
    """
    try:
        # Get all lesson parts for this lesson
        parts_response = supabase.table("lesson_parts").select("id").eq("lesson_id", lesson_id).execute()
        if not parts_response.data:
            return UserProgressSummary(
                user_id=user_id,
                lesson_id=lesson_id,
                total_parts=0,
                completed_parts=0,
                total_exercises=0,
                completed_exercises=0,
                total_subtasks=0,
                completed_subtasks=0,
                overall_progress=0,
                total_time_spent_minutes=0
            )
        
        part_ids = [part["id"] for part in parts_response.data]
        total_parts = len(part_ids)
        
        # Get progress for lesson parts
        parts_progress_response = supabase.table("lesson_part_progress").select("*").eq("user_id", user_id).in_("lesson_part_id", part_ids).execute()
        parts_progress = parts_progress_response.data if parts_progress_response.data else []
        completed_parts = len([p for p in parts_progress if p["status"] == "completed"])
        
        # Get all exercises for this lesson
        exercises_response = supabase.table("exercises").select("id").in_("lesson_part_id", part_ids).execute()
        exercise_ids = [ex["id"] for ex in exercises_response.data] if exercises_response.data else []
        total_exercises = len(exercise_ids)
        
        # Get progress for exercises
        exercises_progress_response = supabase.table("exercise_progress").select("*").eq("user_id", user_id).in_("exercise_id", exercise_ids).execute()
        exercises_progress = exercises_progress_response.data if exercises_progress_response.data else []
        completed_exercises = len([e for e in exercises_progress if e["status"] == "completed"])
        
        # Get all subtasks for this lesson
        subtasks_response = supabase.table("subtasks").select("id").in_("exercise_id", exercise_ids).execute()
        subtask_ids = [st["id"] for st in subtasks_response.data] if subtasks_response.data else []
        total_subtasks = len(subtask_ids)
        
        # Get progress for subtasks
        subtasks_progress_response = supabase.table("subtask_progress").select("*").eq("user_id", user_id).in_("subtask_id", subtask_ids).execute()
        subtasks_progress = subtasks_progress_response.data if subtasks_progress_response.data else []
        completed_subtasks = len([s for s in subtasks_progress if s["status"] == "completed"])
        
        # Calculate overall progress
        total_items = total_parts + total_exercises + total_subtasks
        completed_items = completed_parts + completed_exercises + completed_subtasks
        overall_progress = int((completed_items / total_items * 100) if total_items > 0 else 0)
        
        # Calculate total time spent
        total_time = sum(p.get("time_spent_minutes", 0) for p in parts_progress)
        total_time += sum(e.get("time_spent_minutes", 0) for e in exercises_progress)
        total_time += sum(s.get("time_spent_minutes", 0) for s in subtasks_progress)
        
        return UserProgressSummary(
            user_id=user_id,
            lesson_id=lesson_id,
            total_parts=total_parts,
            completed_parts=completed_parts,
            total_exercises=total_exercises,
            completed_exercises=completed_exercises,
            total_subtasks=total_subtasks,
            completed_subtasks=completed_subtasks,
            overall_progress=overall_progress,
            total_time_spent_minutes=total_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/user/{user_id}/overview")
async def get_user_progress_overview(user_id: str):
    """
    Get overview of all user progress across all lessons
    """
    try:
        # Get all lesson part progress for user
        parts_progress_response = supabase.table("lesson_part_progress").select("*").eq("user_id", user_id).execute()
        parts_progress = parts_progress_response.data if parts_progress_response.data else []
        
        # Get all exercise progress for user
        exercises_progress_response = supabase.table("exercise_progress").select("*").eq("user_id", user_id).execute()
        exercises_progress = exercises_progress_response.data if exercises_progress_response.data else []
        
        # Get all subtask progress for user
        subtasks_progress_response = supabase.table("subtask_progress").select("*").eq("user_id", user_id).execute()
        subtasks_progress = subtasks_progress_response.data if subtasks_progress_response.data else []
        
        # Calculate statistics
        total_parts = len(parts_progress)
        completed_parts = len([p for p in parts_progress if p["status"] == "completed"])
        
        total_exercises = len(exercises_progress)
        completed_exercises = len([e for e in exercises_progress if e["status"] == "completed"])
        
        total_subtasks = len(subtasks_progress)
        completed_subtasks = len([s for s in subtasks_progress if s["status"] == "completed"])
        
        total_time = sum(p.get("time_spent_minutes", 0) for p in parts_progress)
        total_time += sum(e.get("time_spent_minutes", 0) for e in exercises_progress)
        total_time += sum(s.get("time_spent_minutes", 0) for s in subtasks_progress)
        
        return {
            "user_id": user_id,
            "total_parts": total_parts,
            "completed_parts": completed_parts,
            "total_exercises": total_exercises,
            "completed_exercises": completed_exercises,
            "total_subtasks": total_subtasks,
            "completed_subtasks": completed_subtasks,
            "total_time_spent_minutes": total_time,
            "overall_completion_rate": {
                "parts": f"{(completed_parts / total_parts * 100):.1f}%" if total_parts > 0 else "0%",
                "exercises": f"{(completed_exercises / total_exercises * 100):.1f}%" if total_exercises > 0 else "0%",
                "subtasks": f"{(completed_subtasks / total_subtasks * 100):.1f}%" if total_subtasks > 0 else "0%"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
