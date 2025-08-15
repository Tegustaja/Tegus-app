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
router = APIRouter(prefix="/lesson-extensions")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class CreateLessonExtensionRequest(BaseModel):
    lesson_id: str
    user_id: str
    extension_type: str = Field(..., description="lesson_part, exercise, subtask")
    parent_id: Optional[str] = None  # ID of the parent component being extended
    extension_reason: Optional[str] = None

class LessonExtensionResponse(BaseModel):
    id: str
    lesson_id: str
    user_id: str
    extension_type: str
    parent_id: Optional[str] = None
    extension_reason: Optional[str] = None
    created_at: str

class ExtensionWithContentResponse(BaseModel):
    id: str
    lesson_id: str
    user_id: str
    extension_type: str
    parent_id: Optional[str] = None
    extension_reason: Optional[str] = None
    created_at: str
    content: Optional[Dict[str, Any]] = None

@router.post("/", response_model=LessonExtensionResponse)
async def create_lesson_extension(request: CreateLessonExtensionRequest):
    """
    Create a new lesson extension request
    """
    try:
        # Check if lesson exists
        lesson_response = supabase.table("Lessons").select("session_id").eq("session_id", request.lesson_id).execute()
        if not lesson_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Validate extension type
        valid_types = ["lesson_part", "exercise", "subtask"]
        if request.extension_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid extension type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Validate parent_id based on extension type
        if request.extension_type == "exercise" and not request.parent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent ID (lesson_part_id) is required for exercise extensions"
            )
        elif request.extension_type == "subtask" and not request.parent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent ID (exercise_id) is required for subtask extensions"
            )
        
        # If parent_id is provided, validate it exists
        if request.parent_id:
            if request.extension_type == "exercise":
                # Check if lesson part exists
                part_response = supabase.table("lesson_parts").select("id").eq("id", request.parent_id).execute()
                if not part_response.data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Parent lesson part not found"
                    )
            elif request.extension_type == "subtask":
                # Check if exercise exists
                exercise_response = supabase.table("exercises").select("id").eq("id", request.parent_id).execute()
                if not exercise_response.data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Parent exercise not found"
                    )
        
        # Create extension data
        extension_data = {
            "id": str(uuid.uuid4()),
            "lesson_id": request.lesson_id,
            "user_id": request.user_id,
            "extension_type": request.extension_type,
            "parent_id": request.parent_id,
            "extension_reason": request.extension_reason,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        response = supabase.table("lesson_extensions").insert(extension_data).execute()
        
        if response.data:
            return LessonExtensionResponse(**response.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create lesson extension"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{extension_id}", response_model=LessonExtensionResponse)
async def get_lesson_extension(extension_id: str):
    """
    Get a specific lesson extension by ID
    """
    try:
        response = supabase.table("lesson_extensions").select("*").eq("id", extension_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson extension not found"
            )
        
        return LessonExtensionResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/lesson/{lesson_id}", response_model=List[LessonExtensionResponse])
async def get_extensions_by_lesson(lesson_id: str):
    """
    Get all extensions for a specific lesson
    """
    try:
        response = supabase.table("lesson_extensions").select("*").eq("lesson_id", lesson_id).order("created_at").execute()
        
        return [LessonExtensionResponse(**extension) for extension in response.data] if response.data else []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=List[LessonExtensionResponse])
async def get_extensions_by_user(user_id: str):
    """
    Get all extensions created by a specific user
    """
    try:
        response = supabase.table("lesson_extensions").select("*").eq("user_id", user_id).order("created_at").execute()
        
        return [LessonExtensionResponse(**extension) for extension in response.data] if response.data else []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/type/{extension_type}", response_model=List[LessonExtensionResponse])
async def get_extensions_by_type(extension_type: str):
    """
    Get all extensions of a specific type
    """
    try:
        # Validate extension type
        valid_types = ["lesson_part", "exercise", "subtask"]
        if extension_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid extension type. Must be one of: {', '.join(valid_types)}"
            )
        
        response = supabase.table("lesson_extensions").select("*").eq("extension_type", extension_type).order("created_at").execute()
        
        return [LessonExtensionResponse(**extension) for extension in response.data] if response.data else []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{extension_id}/with-content", response_model=ExtensionWithContentResponse)
async def get_extension_with_content(extension_id: str):
    """
    Get a lesson extension with its associated content
    """
    try:
        # Get the extension
        extension_response = supabase.table("lesson_extensions").select("*").eq("id", extension_id).execute()
        
        if not extension_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson extension not found"
            )
        
        extension = extension_response.data[0]
        
        # Get the associated content based on extension type
        content = None
        if extension["extension_type"] == "lesson_part" and extension["parent_id"]:
            # For lesson part extensions, get the lesson part details
            part_response = supabase.table("lesson_parts").select("*").eq("id", extension["parent_id"]).execute()
            if part_response.data:
                content = part_response.data[0]
        elif extension["extension_type"] == "exercise" and extension["parent_id"]:
            # For exercise extensions, get the exercise details
            exercise_response = supabase.table("exercises").select("*").eq("id", extension["parent_id"]).execute()
            if exercise_response.data:
                content = exercise_response.data[0]
        elif extension["extension_type"] == "subtask" and extension["parent_id"]:
            # For subtask extensions, get the subtask details
            subtask_response = supabase.table("subtasks").select("*").eq("id", extension["parent_id"]).execute()
            if subtask_response.data:
                content = subtask_response.data[0]
        
        # Combine data
        result = extension.copy()
        result["content"] = content
        
        return ExtensionWithContentResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/{extension_id}")
async def delete_lesson_extension(extension_id: str):
    """
    Delete a lesson extension
    """
    try:
        # Check if extension exists
        existing_extension = supabase.table("lesson_extensions").select("id").eq("id", extension_id).execute()
        if not existing_extension.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson extension not found"
            )
        
        # Delete the extension
        response = supabase.table("lesson_extensions").delete().eq("id", extension_id).execute()
        
        if response.data:
            return {"message": "Lesson extension deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete lesson extension"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/lesson/{lesson_id}/user/{user_id}", response_model=List[LessonExtensionResponse])
async def get_user_extensions_for_lesson(lesson_id: str, user_id: str):
    """
    Get all extensions created by a specific user for a specific lesson
    """
    try:
        response = supabase.table("lesson_extensions").select("*").eq("lesson_id", lesson_id).eq("user_id", user_id).order("created_at").execute()
        
        return [LessonExtensionResponse(**extension) for extension in response.data] if response.data else []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/analytics/extension-types")
async def get_extension_type_analytics():
    """
    Get analytics on extension types across all lessons
    """
    try:
        # Get all extensions
        response = supabase.table("lesson_extensions").select("extension_type, created_at").execute()
        
        if not response.data:
            return {
                "total_extensions": 0,
                "extension_types": {},
                "recent_extensions": 0
            }
        
        extensions = response.data
        
        # Count by type
        type_counts = {}
        for ext in extensions:
            ext_type = ext["extension_type"]
            type_counts[ext_type] = type_counts.get(ext_type, 0) + 1
        
        # Count recent extensions (last 30 days)
        thirty_days_ago = (datetime.utcnow() - datetime.timedelta(days=30)).isoformat()
        recent_extensions = len([ext for ext in extensions if ext["created_at"] >= thirty_days_ago])
        
        return {
            "total_extensions": len(extensions),
            "extension_types": type_counts,
            "recent_extensions": recent_extensions,
            "most_common_type": max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/analytics/user/{user_id}")
async def get_user_extension_analytics(user_id: str):
    """
    Get analytics on extensions created by a specific user
    """
    try:
        # Get all extensions for the user
        response = supabase.table("lesson_extensions").select("extension_type, created_at, lesson_id").eq("user_id", user_id).execute()
        
        if not response.data:
            return {
                "user_id": user_id,
                "total_extensions": 0,
                "extension_types": {},
                "lessons_extended": 0,
                "recent_extensions": 0
            }
        
        extensions = response.data
        
        # Count by type
        type_counts = {}
        for ext in extensions:
            ext_type = ext["extension_type"]
            type_counts[ext_type] = type_counts.get(ext_type, 0) + 1
        
        # Count unique lessons extended
        unique_lessons = len(set(ext["lesson_id"] for ext in extensions))
        
        # Count recent extensions (last 30 days)
        thirty_days_ago = (datetime.utcnow() - datetime.timedelta(days=30)).isoformat()
        recent_extensions = len([ext for ext in extensions if ext["created_at"] >= thirty_days_ago])
        
        return {
            "user_id": user_id,
            "total_extensions": len(extensions),
            "extension_types": type_counts,
            "lessons_extended": unique_lessons,
            "recent_extensions": recent_extensions,
            "most_common_type": max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
