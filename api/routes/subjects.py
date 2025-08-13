from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter(prefix="/subjects")

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

class Subject(BaseModel):
    id: str
    title: str
    description: str
    color: str
    icon: str
    is_unlocked: bool
    created_at: Optional[str] = None

class SubjectWithTopics(BaseModel):
    id: str
    title: str
    description: str
    color: str
    icon: str
    is_unlocked: bool
    created_at: Optional[str] = None
    topics: List[Topic]

class UnlockSubjectRequest(BaseModel):
    user_id: str

class UnlockSubjectResponse(BaseModel):
    message: str
    subject_id: str
    is_unlocked: bool

@router.get("/", response_model=List[Subject])
async def get_subjects():
    """
    Fetch all subjects
    """
    try:
        response = supabase.table("subjects").select("*").order("created_at").execute()
        
        if not response.data:
            return []
        
        return [Subject(**subject) for subject in response.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subjects: {str(e)}"
        )

@router.get("/{subject_id}", response_model=Subject)
async def get_subject(subject_id: str):
    """
    Get specific subject by ID
    """
    try:
        response = supabase.table("subjects").select("*").eq("id", subject_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with ID {subject_id} not found"
            )
        
        return Subject(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subject: {str(e)}"
        )

@router.get("/{subject_id}/topics", response_model=List[Topic])
async def get_subject_topics(subject_id: str):
    """
    Get topics for a specific subject
    """
    try:
        # First verify the subject exists
        subject_response = supabase.table("subjects").select("id").eq("id", subject_id).execute()
        
        if not subject_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with ID {subject_id} not found"
            )
        
        # Get topics for this subject
        topics_response = supabase.table("topics").select("*").eq("subject_id", subject_id).order("topic_order").execute()
        
        if not topics_response.data:
            return []
        
        return [Topic(**topic) for topic in topics_response.data]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch topics: {str(e)}"
        )

@router.get("/{subject_id}/with-topics", response_model=SubjectWithTopics)
async def get_subject_with_topics(subject_id: str):
    """
    Get subject with all its topics
    """
    try:
        # Get subject
        subject_response = supabase.table("subjects").select("*").eq("id", subject_id).execute()
        
        if not subject_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with ID {subject_id} not found"
            )
        
        subject = subject_response.data[0]
        
        # Get topics for this subject
        topics_response = supabase.table("topics").select("*").eq("subject_id", subject_id).order("topic_order").execute()
        
        topics = []
        if topics_response.data:
            topics = [Topic(**topic) for topic in topics_response.data]
        
        return SubjectWithTopics(
            **subject,
            topics=topics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subject with topics: {str(e)}"
        )

@router.put("/{subject_id}/unlock", response_model=UnlockSubjectResponse)
async def unlock_subject(subject_id: str, request: UnlockSubjectRequest):
    """
    Unlock a subject for a user
    """
    try:
        # First verify the subject exists
        subject_response = supabase.table("subjects").select("id, is_unlocked").eq("id", subject_id).execute()
        
        if not subject_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with ID {subject_id} not found"
            )
        
        subject = subject_response.data[0]
        
        # Check if already unlocked
        if subject["is_unlocked"]:
            return UnlockSubjectResponse(
                message="Subject is already unlocked",
                subject_id=subject_id,
                is_unlocked=True
            )
        
        # Unlock the subject
        update_response = supabase.table("subjects").update({
            "is_unlocked": True
        }).eq("id", subject_id).execute()
        
        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unlock subject"
            )
        
        # Also unlock the first topic for this subject (if it exists)
        topics_response = supabase.table("topics").select("id").eq("subject_id", subject_id).order("topic_order").limit(1).execute()
        
        if topics_response.data:
            first_topic_id = topics_response.data[0]["id"]
            supabase.table("topics").update({
                "is_locked": False
            }).eq("id", first_topic_id).execute()
        
        return UnlockSubjectResponse(
            message="Subject unlocked successfully",
            subject_id=subject_id,
            is_unlocked=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlock subject: {str(e)}"
        )

@router.get("/{subject_id}/topics/{topic_id}/unlock", response_model=dict)
async def unlock_topic(subject_id: str, topic_id: str):
    """
    Unlock a specific topic within a subject
    """
    try:
        # Verify the subject exists
        subject_response = supabase.table("subjects").select("id").eq("id", subject_id).execute()
        
        if not subject_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with ID {subject_id} not found"
            )
        
        # Verify the topic exists and belongs to this subject
        topic_response = supabase.table("topics").select("id, is_locked").eq("id", topic_id).eq("subject_id", subject_id).execute()
        
        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with ID {topic_id} not found in subject {subject_id}"
            )
        
        topic = topic_response.data[0]
        
        # Check if already unlocked
        if not topic["is_locked"]:
            return {"message": "Topic is already unlocked", "topic_id": topic_id, "is_locked": False}
        
        # Unlock the topic
        update_response = supabase.table("topics").update({
            "is_locked": False
        }).eq("id", topic_id).execute()
        
        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unlock topic"
            )
        
        return {
            "message": "Topic unlocked successfully",
            "topic_id": topic_id,
            "is_locked": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlock topic: {str(e)}"
        )
