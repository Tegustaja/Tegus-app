from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter(prefix="/topics")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class Topic(BaseModel):
    id: str
    name: str
    description: str
    subject_id: str
    topic_order: int
    is_locked: bool
    icon: str
    position: str  # 'left', 'center', 'right'
    created_at: Optional[str] = None

class TopicCreate(BaseModel):
    name: str
    description: str
    subject_id: str
    topic_order: int
    icon: str
    position: str

class TopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    topic_order: Optional[int] = None
    is_locked: Optional[bool] = None
    icon: Optional[str] = None
    position: Optional[str] = None

@router.get("/", response_model=List[Topic])
async def get_topics():
    """
    Fetch all topics
    """
    try:
        response = supabase.table("topics").select("*").order("topic_order").execute()
        
        if not response.data:
            return []
        
        return [Topic(**topic) for topic in response.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch topics: {str(e)}"
        )

@router.get("/{topic_id}", response_model=Topic)
async def get_topic(topic_id: str):
    """
    Get specific topic by ID
    """
    try:
        response = supabase.table("topics").select("*").eq("id", topic_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with ID {topic_id} not found"
            )
        
        return Topic(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch topic: {str(e)}"
        )

@router.post("/", response_model=Topic)
async def create_topic(topic: TopicCreate):
    """
    Create a new topic
    """
    try:
        response = supabase.table("topics").insert(topic.dict()).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create topic"
            )
        
        return Topic(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create topic: {str(e)}"
        )

@router.put("/{topic_id}", response_model=Topic)
async def update_topic(topic_id: str, topic_update: TopicUpdate):
    """
    Update a topic
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in topic_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        response = supabase.table("topics").update(update_data).eq("id", topic_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with ID {topic_id} not found"
            )
        
        return Topic(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update topic: {str(e)}"
        )

@router.delete("/{topic_id}")
async def delete_topic(topic_id: str):
    """
    Delete a topic
    """
    try:
        response = supabase.table("topics").delete().eq("id", topic_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with ID {topic_id} not found"
            )
        
        return {"message": "Topic deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete topic: {str(e)}"
        )

@router.put("/{topic_id}/unlock")
async def unlock_topic(topic_id: str):
    """
    Unlock a specific topic
    """
    try:
        response = supabase.table("topics").update({
            "is_locked": False
        }).eq("id", topic_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with ID {topic_id} not found"
            )
        
        return {"message": "Topic unlocked successfully", "topic_id": topic_id, "is_locked": False}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlock topic: {str(e)}"
        )
