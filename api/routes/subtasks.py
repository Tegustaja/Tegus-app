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
router = APIRouter(prefix="/subtasks")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class CreateSubtaskRequest(BaseModel):
    exercise_id: str
    title: str
    content: str
    subtask_type: str = Field(..., description="explanation, practice, reinforcement, extension")
    subtask_order: int = Field(gt=0, description="Order within the exercise")
    is_optional: bool = Field(default=True, description="Whether this subtask is required")

class UpdateSubtaskRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    subtask_type: Optional[str] = Field(None, description="explanation, practice, reinforcement, extension")
    subtask_order: Optional[int] = Field(None, gt=0, description="Order within the exercise")
    is_optional: Optional[bool] = None
    is_completed: Optional[bool] = None

class SubtaskResponse(BaseModel):
    id: str
    exercise_id: str
    title: str
    content: str
    subtask_type: str
    subtask_order: int
    is_optional: bool
    is_completed: bool
    completed_at: Optional[str] = None
    created_at: str
    updated_at: str

@router.post("/", response_model=SubtaskResponse)
async def create_subtask(request: CreateSubtaskRequest):
    """
    Create a new subtask under an exercise
    """
    try:
        # Check if exercise exists
        exercise_response = supabase.table("exercises").select("id").eq("id", request.exercise_id).execute()
        if not exercise_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        # Check if subtask_order already exists for this exercise
        existing_subtask = supabase.table("subtasks").select("id").eq("exercise_id", request.exercise_id).eq("subtask_order", request.subtask_order).execute()
        if existing_subtask.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subtask order {request.subtask_order} already exists for this exercise"
            )
        
        # Validate subtask type
        valid_types = ["explanation", "practice", "reinforcement", "extension"]
        if request.subtask_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subtask type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Create subtask data
        subtask_data = {
            "id": str(uuid.uuid4()),
            "exercise_id": request.exercise_id,
            "title": request.title,
            "content": request.content,
            "subtask_type": request.subtask_type,
            "subtask_order": request.subtask_order,
            "is_optional": request.is_optional,
            "is_completed": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        response = supabase.table("subtasks").insert(subtask_data).execute()
        
        if response.data:
            return SubtaskResponse(**response.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subtask"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{subtask_id}", response_model=SubtaskResponse)
async def get_subtask(subtask_id: str):
    """
    Get a specific subtask by ID
    """
    try:
        response = supabase.table("subtasks").select("*").eq("id", subtask_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found"
            )
        
        return SubtaskResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/{subtask_id}", response_model=SubtaskResponse)
async def update_subtask(subtask_id: str, request: UpdateSubtaskRequest):
    """
    Update a subtask
    """
    try:
        # Check if subtask exists
        existing_subtask = supabase.table("subtasks").select("id, exercise_id").eq("id", subtask_id).execute()
        if not existing_subtask.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found"
            )
        
        # Prepare update data
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.content is not None:
            update_data["content"] = request.content
        if request.subtask_type is not None:
            valid_types = ["explanation", "practice", "reinforcement", "extension"]
            if request.subtask_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid subtask type. Must be one of: {', '.join(valid_types)}"
                )
            update_data["subtask_type"] = request.subtask_type
        if request.subtask_order is not None:
            # Check if new subtask_order conflicts with existing
            existing_order = supabase.table("subtasks").select("id").eq("exercise_id", existing_subtask.data[0]["exercise_id"]).eq("subtask_order", request.subtask_order).execute()
            if existing_order.data and existing_order.data[0]["id"] != subtask_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Subtask order {request.subtask_order} already exists for this exercise"
                )
            update_data["subtask_order"] = request.subtask_order
        if request.is_optional is not None:
            update_data["is_optional"] = request.is_optional
        if request.is_completed is not None:
            update_data["is_completed"] = request.is_completed
            if request.is_completed:
                update_data["completed_at"] = datetime.utcnow().isoformat()
            else:
                update_data["completed_at"] = None
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update in database
        response = supabase.table("subtasks").update(update_data).eq("id", subtask_id).execute()
        
        if response.data:
            return SubtaskResponse(**response.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update subtask"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/{subtask_id}")
async def delete_subtask(subtask_id: str):
    """
    Delete a subtask
    """
    try:
        # Check if subtask exists
        existing_subtask = supabase.table("subtasks").select("id").eq("id", subtask_id).execute()
        if not existing_subtask.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found"
            )
        
        # Delete the subtask
        response = supabase.table("subtasks").delete().eq("id", subtask_id).execute()
        
        if response.data:
            return {"message": "Subtask deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete subtask"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/exercise/{exercise_id}", response_model=List[SubtaskResponse])
async def get_subtasks_by_exercise(exercise_id: str):
    """
    Get all subtasks for a specific exercise, ordered by subtask_order
    """
    try:
        response = supabase.table("subtasks").select("*").eq("exercise_id", exercise_id).order("subtask_order").execute()
        
        return [SubtaskResponse(**subtask) for subtask in response.data] if response.data else []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/type/{subtask_type}", response_model=List[SubtaskResponse])
async def get_subtasks_by_type(subtask_type: str):
    """
    Get all subtasks of a specific type
    """
    try:
        # Validate subtask type
        valid_types = ["explanation", "practice", "reinforcement", "extension"]
        if subtask_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subtask type. Must be one of: {', '.join(valid_types)}"
            )
        
        response = supabase.table("subtasks").select("*").eq("subtask_type", subtask_type).order("created_at").execute()
        
        return [SubtaskResponse(**subtask) for subtask in response.data] if response.data else []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/optional/{is_optional}", response_model=List[SubtaskResponse])
async def get_subtasks_by_optional_status(is_optional: bool):
    """
    Get all subtasks by their optional status
    """
    try:
        response = supabase.table("subtasks").select("*").eq("is_optional", is_optional).order("created_at").execute()
        
        return [SubtaskResponse(**subtask) for subtask in response.data] if response.data else []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/{subtask_id}/complete")
async def complete_subtask(subtask_id: str):
    """
    Mark a subtask as completed
    """
    try:
        # Check if subtask exists
        existing_subtask = supabase.table("subtasks").select("id").eq("id", subtask_id).execute()
        if not existing_subtask.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found"
            )
        
        # Update completion status
        update_data = {
            "is_completed": True,
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("subtasks").update(update_data).eq("id", subtask_id).execute()
        
        if response.data:
            return {"message": "Subtask marked as completed"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update subtask"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/{subtask_id}/toggle-optional")
async def toggle_subtask_optional(subtask_id: str):
    """
    Toggle the optional status of a subtask
    """
    try:
        # Check if subtask exists
        existing_subtask = supabase.table("subtasks").select("id, is_optional").eq("id", subtask_id).execute()
        if not existing_subtask.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found"
            )
        
        # Toggle the optional status
        current_status = existing_subtask.data[0]["is_optional"]
        new_status = not current_status
        
        update_data = {
            "is_optional": new_status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("subtasks").update(update_data).eq("id", subtask_id).execute()
        
        if response.data:
            return {
                "message": f"Subtask optional status updated to {new_status}",
                "is_optional": new_status
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update subtask optional status"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
