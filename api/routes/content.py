from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter(prefix="/content")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class LearningMaterial(BaseModel):
    id: str
    topic_id: str
    title: str
    description: str
    content_type: str  # 'text', 'video', 'interactive', 'exercise', 'quiz'
    content_url: Optional[str] = None
    content_text: Optional[str] = None
    difficulty_level: str  # 'beginner', 'intermediate', 'advanced'
    estimated_duration_minutes: int
    tags: List[str]
    is_active: bool
    created_at: str
    updated_at: str

class ContentFeedback(BaseModel):
    id: str
    user_id: str
    content_id: str
    content_type: str  # 'topic', 'material', 'exercise', 'quiz'
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = None
    difficulty_feedback: Optional[str] = None  # 'too_easy', 'just_right', 'too_hard'
    content_quality: Optional[str] = None  # 'excellent', 'good', 'fair', 'poor'
    created_at: str

class SubmitFeedbackRequest(BaseModel):
    user_id: str
    content_id: str
    content_type: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None
    difficulty_feedback: Optional[str] = None
    content_quality: Optional[str] = None

class ContentRecommendation(BaseModel):
    content_id: str
    content_type: str
    title: str
    description: str
    topic_id: str
    topic_name: str
    subject_id: str
    subject_name: str
    difficulty_level: str
    estimated_duration_minutes: int
    match_score: float  # 0.0 to 1.0
    reason: str  # Why this content was recommended
    tags: List[str]

class RecommendationsRequest(BaseModel):
    user_id: str
    limit: int = Field(default=10, ge=1, le=50)
    content_types: Optional[List[str]] = None  # Filter by content types
    difficulty_levels: Optional[List[str]] = None  # Filter by difficulty
    topics: Optional[List[str]] = None  # Filter by specific topics

@router.get("/topics/{topic_id}/materials", response_model=List[LearningMaterial])
async def get_topic_materials(topic_id: str, difficulty_level: Optional[str] = Query(None), content_type: Optional[str] = Query(None)):
    """
    Get learning materials for a specific topic
    """
    try:
        # First verify the topic exists
        topic_response = supabase.table("topics").select("id, name, subject_id").eq("id", topic_id).execute()
        
        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with ID {topic_id} not found"
            )
        
        # Build query for materials
        query = supabase.table("learning_materials").select("*").eq("topic_id", topic_id).eq("is_active", True)
        
        # Apply filters if provided
        if difficulty_level:
            query = query.eq("difficulty_level", difficulty_level)
        
        if content_type:
            query = query.eq("content_type", content_type)
        
        # Execute query
        response = query.order("difficulty_level").order("created_at").execute()
        
        if not response.data:
            # Return empty list if no materials found
            return []
        
        # Convert to response models
        materials = []
        for material in response.data:
            # Parse tags if they're stored as JSON
            tags = material.get("tags", [])
            if isinstance(tags, str):
                try:
                    import json
                    tags = json.loads(tags)
                except:
                    tags = []
            
            material_data = {
                **material,
                "tags": tags if isinstance(tags, list) else []
            }
            materials.append(LearningMaterial(**material_data))
        
        return materials
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch topic materials: {str(e)}"
        )

@router.post("/feedback", response_model=ContentFeedback)
async def submit_content_feedback(request: SubmitFeedbackRequest):
    """
    Submit user feedback on content
    """
    try:
        # Validate content type
        valid_content_types = ['topic', 'material', 'exercise', 'quiz']
        if request.content_type not in valid_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content type. Must be one of: {valid_content_types}"
            )
        
        # Validate difficulty feedback if provided
        if request.difficulty_feedback:
            valid_difficulty_feedback = ['too_easy', 'just_right', 'too_hard']
            if request.difficulty_feedback not in valid_difficulty_feedback:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid difficulty feedback. Must be one of: {valid_difficulty_feedback}"
                )
        
        # Validate content quality if provided
        if request.content_quality:
            valid_content_quality = ['excellent', 'good', 'fair', 'poor']
            if request.content_quality not in valid_content_quality:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid content quality. Must be one of: {valid_content_quality}"
                )
        
        # Create feedback record
        feedback_data = {
            "user_id": request.user_id,
            "content_id": request.content_id,
            "content_type": request.content_type,
            "rating": request.rating,
            "feedback_text": request.feedback_text,
            "difficulty_feedback": request.difficulty_feedback,
            "content_quality": request.content_quality,
            "created_at": datetime.now().isoformat()
        }
        
        # Insert into database
        response = supabase.table("content_feedback").insert(feedback_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit feedback"
            )
        
        return ContentFeedback(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/recommendations", response_model=List[ContentRecommendation])
async def get_content_recommendations(
    user_id: str,
    limit: int = 10,
    content_types: Optional[str] = None,
    difficulty_levels: Optional[str] = None,
    topics: Optional[str] = None
):
    """
    Get personalized content recommendations based on user preferences and progress
    """
    try:
        # Parse query parameters
        content_types_list = content_types.split(',') if content_types else None
        difficulty_levels_list = difficulty_levels.split(',') if difficulty_levels else None
        topics_list = topics.split(',') if topics else None
        
        # Get user progress and preferences
        progress_response = supabase.table("user_progress").select("*").eq("user_id", user_id).execute()
        user_progress = {p["topic_id"]: p["progress"] for p in progress_response.data} if progress_response.data else {}
        
        # Get user's completed topics (progress = 100%)
        completed_topics = [topic_id for topic_id, progress in user_progress.items() if progress == 100]
        
        # Get user's current learning topics (progress > 0 but < 100)
        current_topics = [topic_id for topic_id, progress in user_progress.items() if 0 < progress < 100]
        
        # Get user's preferred difficulty level based on progress
        user_difficulty = "intermediate"  # Default
        if user_progress:
            avg_progress = sum(user_progress.values()) / len(user_progress.values())
            if avg_progress < 30:
                user_difficulty = "beginner"
            elif avg_progress > 70:
                user_difficulty = "advanced"
        
        # Build recommendations query
        query = supabase.table("learning_materials").select("*, topics(name, subject_id), subjects(name)").eq("is_active", True)
        
        # Apply filters
        if content_types_list:
            query = query.in_("content_type", content_types_list)
        
        if difficulty_levels_list:
            query = query.in_("difficulty_level", difficulty_levels_list)
        else:
            # Default to user's preferred difficulty
            query = query.eq("difficulty_level", user_difficulty)
        
        if topics_list:
            query = query.in_("topic_id", topics_list)
        
        # Execute query
        response = query.order("created_at", desc=True).limit(limit * 2).execute()  # Get more to filter
        
        if not response.data:
            return []
        
        # Process and score recommendations
        recommendations = []
        for material in response.data:
            # Calculate match score based on user preferences
            match_score = 0.0
            reason = ""
            
            # Topic progress scoring
            topic_id = material["topic_id"]
            if topic_id in current_topics:
                match_score += 0.4  # High score for topics user is currently learning
                reason = "Currently learning this topic"
            elif topic_id in completed_topics:
                match_score += 0.2  # Lower score for completed topics
                reason = "Topic completed - review material"
            else:
                match_score += 0.1  # Base score for new topics
                reason = "New topic to explore"
            
            # Difficulty matching
            if material["difficulty_level"] == user_difficulty:
                match_score += 0.3
                reason += " - Matches your skill level"
            elif material["difficulty_level"] == "beginner" and user_difficulty == "intermediate":
                match_score += 0.2
                reason += " - Good for review"
            elif material["difficulty_level"] == "advanced" and user_difficulty == "beginner":
                match_score += 0.1
                reason += " - Challenge yourself"
            
            # Content type preference (assume user prefers variety)
            if material["content_type"] not in ['exercise', 'quiz']:  # Prefer learning materials over assessments
                match_score += 0.2
                reason += " - Learning material"
            
            # Duration preference (prefer shorter materials for engagement)
            if material["estimated_duration_minutes"] <= 15:
                match_score += 0.1
                reason += " - Quick to complete"
            
            # Normalize score to 0.0-1.0 range
            match_score = min(match_score, 1.0)
            
            # Create recommendation
            recommendation = ContentRecommendation(
                content_id=material["id"],
                content_type=material["content_type"],
                title=material["title"],
                description=material["description"],
                topic_id=material["topic_id"],
                topic_name=material["topics"]["name"] if material["topics"] else "Unknown Topic",
                subject_id=material["topics"]["subject_id"] if material["topics"] else "Unknown Subject",
                subject_name=material["subjects"]["name"] if material["subjects"] else "Unknown Subject",
                difficulty_level=material["difficulty_level"],
                estimated_duration_minutes=material["estimated_duration_minutes"],
                match_score=round(match_score, 2),
                reason=reason,
                tags=material.get("tags", []) if isinstance(material.get("tags"), list) else []
            )
            
            recommendations.append(recommendation)
        
        # Sort by match score and return top results
        recommendations.sort(key=lambda x: x.match_score, reverse=True)
        return recommendations[:limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )

@router.get("/materials/{material_id}")
async def get_material_details(material_id: str):
    """
    Get detailed information about a specific learning material
    """
    try:
        response = supabase.table("learning_materials").select("*, topics(name, subject_id), subjects(name)").eq("id", material_id).eq("is_active", True).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning material with ID {material_id} not found"
            )
        
        material = response.data[0]
        
        # Parse tags
        tags = material.get("tags", [])
        if isinstance(tags, str):
            try:
                import json
                tags = json.loads(tags)
            except:
                tags = []
        
        return {
            **material,
            "tags": tags if isinstance(tags, list) else [],
            "topic_name": material["topics"]["name"] if material["topics"] else "Unknown Topic",
            "subject_name": material["subjects"]["name"] if material["subjects"] else "Unknown Subject"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch material details: {str(e)}"
        )

@router.get("/topics/{topic_id}/overview")
async def get_topic_overview(topic_id: str):
    """
    Get overview information for a topic including available materials count
    """
    try:
        # Get topic information
        topic_response = supabase.table("topics").select("*, subjects(name)").eq("id", topic_id).execute()
        
        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with ID {topic_id} not found"
            )
        
        topic = topic_response.data[0]
        
        # Count materials by type
        materials_response = supabase.table("learning_materials").select("content_type").eq("topic_id", topic_id).eq("is_active", True).execute()
        
        material_counts = {}
        if materials_response.data:
            for material in materials_response.data:
                content_type = material["content_type"]
                material_counts[content_type] = material_counts.get(content_type, 0) + 1
        
        # Get difficulty distribution
        difficulty_response = supabase.table("learning_materials").select("difficulty_level").eq("topic_id", topic_id).eq("is_active", True).execute()
        
        difficulty_distribution = {}
        if difficulty_response.data:
            for material in difficulty_response.data:
                difficulty = material["difficulty_level"]
                difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1
        
        return {
            "topic_id": topic["id"],
            "topic_name": topic["name"],
            "description": topic["description"],
            "subject_name": topic["subjects"]["name"] if topic["subjects"] else "Unknown Subject",
            "is_locked": topic["is_locked"],
            "total_materials": len(materials_response.data) if materials_response.data else 0,
            "material_counts": material_counts,
            "difficulty_distribution": difficulty_distribution,
            "estimated_total_duration": sum(
                material.get("estimated_duration_minutes", 0) 
                for material in (materials_response.data or [])
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch topic overview: {str(e)}"
        )
