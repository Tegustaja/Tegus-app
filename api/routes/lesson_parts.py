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
router = APIRouter(prefix="/lesson-parts")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class CreateLessonPartRequest(BaseModel):
    lesson_id: str
    title: str
    description: Optional[str] = None
    part_order: int = Field(gt=0, description="Order within the lesson")

class UpdateLessonPartRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    part_order: Optional[int] = Field(None, gt=0, description="Order within the lesson")
    is_completed: Optional[bool] = None

class LessonPartResponse(BaseModel):
    id: str
    lesson_id: str
    title: str
    description: Optional[str] = None
    part_order: int
    is_completed: bool
    completed_at: Optional[str] = None
    created_at: str
    updated_at: str

class LessonPartWithExercisesResponse(BaseModel):
    id: str
    lesson_id: str
    title: str
    description: Optional[str] = None
    part_order: int
    is_completed: bool
    completed_at: Optional[str] = None
    created_at: str
    updated_at: str
    exercises: List[Dict[str, Any]] = []

@router.post("/", response_model=LessonPartResponse)
async def create_lesson_part(request: CreateLessonPartRequest):
    """
    Create a new lesson part
    """
    try:
        # Check if lesson exists
        lesson_response = supabase.table("Lessons").select("session_id").eq("session_id", request.lesson_id).execute()
        if not lesson_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Check if part_order already exists for this lesson
        existing_part = supabase.table("lesson_parts").select("id").eq("lesson_id", request.lesson_id).eq("part_order", request.part_order).execute()
        if existing_part.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Part order {request.part_order} already exists for this lesson"
            )
        
        # Create lesson part data
        lesson_part_data = {
            "id": str(uuid.uuid4()),
            "lesson_id": request.lesson_id,
            "title": request.title,
            "description": request.description,
            "part_order": request.part_order,
            "is_completed": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        response = supabase.table("lesson_parts").insert(lesson_part_data).execute()
        
        if response.data:
            return LessonPartResponse(**response.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create lesson part"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{lesson_part_id}", response_model=LessonPartResponse)
async def get_lesson_part(lesson_part_id: str):
    """
    Get a specific lesson part by ID
    """
    try:
        response = supabase.table("lesson_parts").select("*").eq("id", lesson_part_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson part not found"
            )
        
        return LessonPartResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{lesson_part_id}/with-exercises", response_model=LessonPartWithExercisesResponse)
async def get_lesson_part_with_exercises(lesson_part_id: str):
    """
    Get a lesson part with all its exercises
    """
    try:
        # Get lesson part
        part_response = supabase.table("lesson_parts").select("*").eq("id", lesson_part_id).execute()
        
        if not part_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson part not found"
            )
        
        lesson_part = part_response.data[0]
        
        # Get exercises for this part
        exercises_response = supabase.table("exercises").select("*").eq("lesson_part_id", lesson_part_id).order("exercise_order").execute()
        exercises = exercises_response.data if exercises_response.data else []
        
        # Combine data
        result = lesson_part.copy()
        result["exercises"] = exercises
        
        return LessonPartWithExercisesResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/{lesson_part_id}", response_model=LessonPartResponse)
async def update_lesson_part(lesson_part_id: str, request: UpdateLessonPartRequest):
    """
    Update a lesson part
    """
    try:
        # Check if lesson part exists
        existing_part = supabase.table("lesson_parts").select("id").eq("id", lesson_part_id).execute()
        if not existing_part.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson part not found"
            )
        
        # Prepare update data
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.description is not None:
            update_data["description"] = request.description
        if request.part_order is not None:
            # Check if new part_order conflicts with existing
            existing_order = supabase.table("lesson_parts").select("id").eq("lesson_id", existing_part.data[0]["lesson_id"]).eq("part_order", request.part_order).execute()
            if existing_order.data and existing_order.data[0]["id"] != lesson_part_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Part order {request.part_order} already exists for this lesson"
                )
            update_data["part_order"] = request.part_order
        if request.is_completed is not None:
            update_data["is_completed"] = request.is_completed
            if request.is_completed:
                update_data["completed_at"] = datetime.utcnow().isoformat()
            else:
                update_data["completed_at"] = None
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update in database
        response = supabase.table("lesson_parts").update(update_data).eq("id", lesson_part_id).execute()
        
        if response.data:
            return LessonPartResponse(**response.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update lesson part"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/{lesson_part_id}")
async def delete_lesson_part(lesson_part_id: str):
    """
    Delete a lesson part (this will also delete all associated exercises and subtasks)
    """
    try:
        # Check if lesson part exists
        existing_part = supabase.table("lesson_parts").select("id").eq("id", lesson_part_id).execute()
        if not existing_part.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson part not found"
            )
        
        # Delete the lesson part (cascade will handle exercises and subtasks)
        response = supabase.table("lesson_parts").delete().eq("id", lesson_part_id).execute()
        
        if response.data:
            return {"message": "Lesson part deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete lesson part"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/lesson/{lesson_id}", response_model=List[LessonPartResponse])
async def get_lesson_parts_by_lesson(lesson_id: str):
    """
    Get all lesson parts for a specific lesson, ordered by part_order
    """
    try:
        response = supabase.table("lesson_parts").select("*").eq("lesson_id", lesson_id).order("part_order").execute()
        
        return [LessonPartResponse(**part) for part in response.data] if response.data else []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/{lesson_part_id}/complete")
async def complete_lesson_part(lesson_part_id: str):
    """
    Mark a lesson part as completed
    """
    try:
        # Check if lesson part exists
        existing_part = supabase.table("lesson_parts").select("id").eq("id", lesson_part_id).execute()
        if not existing_part.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson part not found"
            )
        
        # Update completion status
        update_data = {
            "is_completed": True,
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("lesson_parts").update(update_data).eq("id", lesson_part_id).execute()
        
        if response.data:
            return {"message": "Lesson part marked as completed"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update lesson part"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
