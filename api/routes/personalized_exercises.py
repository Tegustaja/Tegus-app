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
router = APIRouter(prefix="/personalized-exercises")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class CreateExerciseRequest(BaseModel):
    lesson_part_id: str
    exercise_type: str = Field(..., description="multiple_choice, true_false, calculation, explanation, interactive")
    title: str
    content: str
    instructions: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty_level: str = Field(default="medium", description="easy, medium, hard")
    exercise_order: int = Field(gt=0, description="Order within the lesson part")

class UpdateExerciseRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    instructions: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty_level: Optional[str] = Field(None, description="easy, medium, hard")
    exercise_order: Optional[int] = Field(None, gt=0, description="Order within the lesson part")
    is_completed: Optional[bool] = None

class ExerciseResponse(BaseModel):
    id: str
    lesson_part_id: str
    exercise_type: str
    title: str
    content: str
    instructions: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty_level: str
    exercise_order: int
    is_completed: bool
    completed_at: Optional[str] = None
    created_at: str
    updated_at: str

class ExerciseWithSubtasksResponse(BaseModel):
    id: str
    lesson_part_id: str
    exercise_type: str
    title: str
    content: str
    instructions: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty_level: str
    exercise_order: int
    is_completed: bool
    completed_at: Optional[str] = None
    created_at: str
    updated_at: str
    subtasks: List[Dict[str, Any]] = []

@router.post("/", response_model=ExerciseResponse)
async def create_exercise(request: CreateExerciseRequest):
    """
    Create a new exercise within a lesson part
    """
    try:
        # Check if lesson part exists
        part_response = supabase.table("lesson_parts").select("id").eq("id", request.lesson_part_id).execute()
        if not part_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson part not found"
            )
        
        # Check if exercise_order already exists for this lesson part
        existing_exercise = supabase.table("exercises").select("id").eq("lesson_part_id", request.lesson_part_id).eq("exercise_order", request.exercise_order).execute()
        if existing_exercise.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exercise order {request.exercise_order} already exists for this lesson part"
            )
        
        # Validate exercise type
        valid_types = ["multiple_choice", "true_false", "calculation", "explanation", "interactive"]
        if request.exercise_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid exercise type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Validate difficulty level
        valid_difficulties = ["easy", "medium", "hard"]
        if request.difficulty_level not in valid_difficulties:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid difficulty level. Must be one of: {', '.join(valid_difficulties)}"
            )
        
        # Create exercise data
        exercise_data = {
            "id": str(uuid.uuid4()),
            "lesson_part_id": request.lesson_part_id,
            "exercise_type": request.exercise_type,
            "title": request.title,
            "content": request.content,
            "instructions": request.instructions,
            "correct_answer": request.correct_answer,
            "explanation": request.explanation,
            "difficulty_level": request.difficulty_level,
            "exercise_order": request.exercise_order,
            "is_completed": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        response = supabase.table("exercises").insert(exercise_data).execute()
        
        if response.data:
            return ExerciseResponse(**response.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create exercise"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(exercise_id: str):
    """
    Get a specific exercise by ID
    """
    try:
        response = supabase.table("exercises").select("*").eq("id", exercise_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        return ExerciseResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{exercise_id}/with-subtasks", response_model=ExerciseWithSubtasksResponse)
async def get_exercise_with_subtasks(exercise_id: str):
    """
    Get an exercise with all its subtasks
    """
    try:
        # Get exercise
        exercise_response = supabase.table("exercises").select("*").eq("id", exercise_id).execute()
        
        if not exercise_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        exercise = exercise_response.data[0]
        
        # Get subtasks for this exercise
        subtasks_response = supabase.table("subtasks").select("*").eq("exercise_id", exercise_id).order("subtask_order").execute()
        subtasks = subtasks_response.data if subtasks_response.data else []
        
        # Combine data
        result = exercise.copy()
        result["subtasks"] = subtasks
        
        return ExerciseWithSubtasksResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(exercise_id: str, request: UpdateExerciseRequest):
    """
    Update an exercise
    """
    try:
        # Check if exercise exists
        existing_exercise = supabase.table("exercises").select("id, lesson_part_id").eq("id", exercise_id).execute()
        if not existing_exercise.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        # Prepare update data
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.content is not None:
            update_data["content"] = request.content
        if request.instructions is not None:
            update_data["instructions"] = request.instructions
        if request.correct_answer is not None:
            update_data["correct_answer"] = request.correct_answer
        if request.explanation is not None:
            update_data["explanation"] = request.explanation
        if request.difficulty_level is not None:
            valid_difficulties = ["easy", "medium", "hard"]
            if request.difficulty_level not in valid_difficulties:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid difficulty level. Must be one of: {', '.join(valid_difficulties)}"
                )
            update_data["difficulty_level"] = request.difficulty_level
        if request.exercise_order is not None:
            # Check if new exercise_order conflicts with existing
            existing_order = supabase.table("exercises").select("id").eq("lesson_part_id", existing_exercise.data[0]["lesson_part_id"]).eq("exercise_order", request.exercise_order).execute()
            if existing_order.data and existing_order.data[0]["id"] != exercise_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Exercise order {request.exercise_order} already exists for this lesson part"
                )
            update_data["exercise_order"] = request.exercise_order
        if request.is_completed is not None:
            update_data["is_completed"] = request.is_completed
            if request.is_completed:
                update_data["completed_at"] = datetime.utcnow().isoformat()
            else:
                update_data["completed_at"] = None
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update in database
        response = supabase.table("exercises").update(update_data).eq("id", exercise_id).execute()
        
        if response.data:
            return ExerciseResponse(**response.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update exercise"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/{exercise_id}")
async def delete_exercise(exercise_id: str):
    """
    Delete an exercise (this will also delete all associated subtasks)
    """
    try:
        # Check if exercise exists
        existing_exercise = supabase.table("exercises").select("id").eq("id", exercise_id).execute()
        if not existing_exercise.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        # Delete the exercise (cascade will handle subtasks)
        response = supabase.table("exercises").delete().eq("id", exercise_id).execute()
        
        if response.data:
            return {"message": "Exercise deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete exercise"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/lesson-part/{lesson_part_id}", response_model=List[ExerciseResponse])
async def get_exercises_by_lesson_part(lesson_part_id: str):
    """
    Get all exercises for a specific lesson part, ordered by exercise_order
    """
    try:
        response = supabase.table("exercises").select("*").eq("lesson_part_id", lesson_part_id).order("exercise_order").execute()
        
        return [ExerciseResponse(**exercise) for exercise in response.data] if response.data else []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/type/{exercise_type}", response_model=List[ExerciseResponse])
async def get_exercises_by_type(exercise_type: str):
    """
    Get all exercises of a specific type
    """
    try:
        # Validate exercise type
        valid_types = ["multiple_choice", "true_false", "calculation", "explanation", "interactive"]
        if exercise_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid exercise type. Must be one of: {', '.join(valid_types)}"
            )
        
        response = supabase.table("exercises").select("*").eq("exercise_type", exercise_type).order("created_at").execute()
        
        return [ExerciseResponse(**exercise) for exercise in response.data] if response.data else []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/difficulty/{difficulty_level}", response_model=List[ExerciseResponse])
async def get_exercises_by_difficulty(difficulty_level: str):
    """
    Get all exercises of a specific difficulty level
    """
    try:
        # Validate difficulty level
        valid_difficulties = ["easy", "medium", "hard"]
        if difficulty_level not in valid_difficulties:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid difficulty level. Must be one of: {', '.join(valid_difficulties)}"
            )
        
        response = supabase.table("exercises").select("*").eq("difficulty_level", difficulty_level).order("created_at").execute()
        
        return [ExerciseResponse(**exercise) for exercise in response.data] if response.data else []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/{exercise_id}/complete")
async def complete_exercise(exercise_id: str):
    """
    Mark an exercise as completed
    """
    try:
        # Check if exercise exists
        existing_exercise = supabase.table("exercises").select("id").eq("id", exercise_id).execute()
        if not existing_exercise.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        # Update completion status
        update_data = {
            "is_completed": True,
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("exercises").update(update_data).eq("id", exercise_id).execute()
        
        if response.data:
            return {"message": "Exercise marked as completed"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update exercise"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
