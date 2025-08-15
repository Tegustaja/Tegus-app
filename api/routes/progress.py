from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from datetime import datetime, date
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter(prefix="/progress")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class TopicProgress(BaseModel):
    topic_id: str
    topic_name: Optional[str] = None
    progress: int  # 0-100
    last_accessed: str
    completed_at: Optional[str] = None
    created_at: str

class UserStatistics(BaseModel):
    total_lessons: int
    total_study_time_minutes: int
    total_tests_completed: int
    updated_at: str

class UserStreaks(BaseModel):
    current_streak: int
    longest_streak: int
    last_study_date: Optional[str] = None
    points: int
    hearts: int
    created_at: str

class UserActivity(BaseModel):
    id: str
    date: str
    activity_type: str
    minutes_spent: int
    created_at: str

class OverallProgress(BaseModel):
    user_id: str
    total_topics: int
    completed_topics: int
    total_progress_percentage: float
    total_study_time_minutes: int
    current_streak: int
    longest_streak: int
    total_points: int
    topics_progress: List[TopicProgress]
    statistics: UserStatistics
    streaks: UserStreaks
    recent_activity: List[UserActivity]

class UpdateProgressRequest(BaseModel):
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    minutes_spent: Optional[int] = Field(None, ge=0, description="Minutes spent on topic")
    activity_type: Optional[str] = Field(None, description="Type of activity (lesson, quiz, exercise)")

class LeaderboardEntry(BaseModel):
    user_id: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    total_points: int
    current_streak: int
    longest_streak: int
    total_study_time_minutes: int
    total_lessons: int
    rank: int

class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardEntry]
    total_participants: int
    user_rank: Optional[int] = None
    updated_at: str

@router.get("/{user_id}", response_model=OverallProgress)
async def get_user_overall_progress(user_id: str):
    """
    Get user's overall progress across all topics
    """
    try:
        # Get user progress for all topics
        progress_response = supabase.table("user_progress").select("*").eq("user_id", user_id).execute()
        
        # Get user statistics
        stats_response = supabase.table("user_statistics").select("*").eq("user_id", user_id).execute()
        
        # Get user streaks
        streaks_response = supabase.table("user_streaks").select("*").eq("user_id", user_id).execute()
        
        # Get recent user activity (last 7 days)
        seven_days_ago = (datetime.now() - datetime.timedelta(days=7)).date().isoformat()
        activity_response = supabase.table("user_activity").select("*").eq("user_id", user_id).gte("date", seven_days_ago).order("date", desc=True).execute()
        
        # Calculate overall progress
        topics_progress = []
        total_progress = 0
        completed_topics = 0
        
        if progress_response.data:
            for progress in progress_response.data:
                topic_progress = TopicProgress(**progress)
                topics_progress.append(topic_progress)
                total_progress += progress["progress"]
                if progress["progress"] == 100:
                    completed_topics += 1
        
        total_topics = len(topics_progress)
        total_progress_percentage = (total_progress / total_topics * 100) if total_topics > 0 else 0
        
        # Get user statistics
        statistics = UserStatistics(**stats_response.data[0]) if stats_response.data else UserStatistics(
            total_lessons=0,
            total_study_time_minutes=0,
            total_tests_completed=0,
            updated_at=datetime.now().isoformat()
        )
        
        # Get user streaks
        streaks = UserStreaks(**streaks_response.data[0]) if streaks_response.data else UserStreaks(
            current_streak=0,
            longest_streak=0,
            last_study_date=None,
            points=0,
            hearts=5,
            created_at=datetime.now().isoformat()
        )
        
        # Get recent activity
        recent_activity = []
        if activity_response.data:
            for activity in activity_response.data:
                recent_activity.append(UserActivity(**activity))
        
        return OverallProgress(
            user_id=user_id,
            total_topics=total_topics,
            completed_topics=completed_topics,
            total_progress_percentage=round(total_progress_percentage, 2),
            total_study_time_minutes=statistics.total_study_time_minutes,
            current_streak=streaks.current_streak,
            longest_streak=streaks.longest_streak,
            total_points=streaks.points,
            topics_progress=topics_progress,
            statistics=statistics,
            streaks=streaks,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user progress: {str(e)}"
        )

@router.get("/{user_id}/topics/{topic_id}", response_model=TopicProgress)
async def get_topic_progress(user_id: str, topic_id: str):
    """
    Get progress for specific topic
    """
    try:
        response = supabase.table("user_progress").select("*").eq("user_id", user_id).eq("topic_id", topic_id).execute()
        
        if not response.data:
            # Create default progress record if none exists
            default_progress = {
                "user_id": user_id,
                "topic_id": topic_id,
                "progress": 0,
                "last_accessed": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            supabase.table("user_progress").insert(default_progress).execute()
            
            return TopicProgress(**default_progress)
        
        return TopicProgress(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch topic progress: {str(e)}"
        )

@router.put("/{user_id}/topics/{topic_id}", response_model=TopicProgress)
async def update_topic_progress(user_id: str, topic_id: str, request: UpdateProgressRequest):
    """
    Update topic progress
    """
    try:
        # Update progress
        update_data = {
            "progress": request.progress,
            "last_accessed": datetime.now().isoformat()
        }
        
        if request.progress == 100:
            update_data["completed_at"] = datetime.now().isoformat()
        
        response = supabase.table("user_progress").update(update_data).eq("user_id", user_id).eq("topic_id", topic_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update topic progress"
            )
        
        # Update user statistics if minutes_spent is provided
        if request.minutes_spent:
            stats_response = supabase.table("user_statistics").select("total_study_time_minutes").eq("user_id", user_id).execute()
            
            if stats_response.data:
                current_minutes = stats_response.data[0]["total_study_time_minutes"] or 0
                new_total = current_minutes + request.minutes_spent
                
                supabase.table("user_statistics").update({
                    "total_study_time_minutes": new_total,
                    "updated_at": datetime.now().isoformat()
                }).eq("user_id", user_id).execute()
        
        # Record user activity
        if request.activity_type:
            activity_data = {
                "user_id": user_id,
                "date": datetime.now().date().isoformat(),
                "activity_type": request.activity_type,
                "minutes_spent": request.minutes_spent or 0,
                "created_at": datetime.now().isoformat()
            }
            
            supabase.table("user_activity").insert(activity_data).execute()
        
        # Update streaks if progress was made
        if request.progress > 0:
            streaks_response = supabase.table("user_streaks").select("*").eq("user_id", user_id).execute()
            
            if streaks_response.data:
                current_streak = streaks_response.data[0]["current_streak"] or 0
                longest_streak = streaks_response.data[0]["longest_streak"] or 0
                last_study_date = streaks_response.data[0]["last_study_date"]
                today = datetime.now().date().isoformat()
                
                # Check if this is a consecutive day
                if last_study_date != today:
                    if last_study_date:
                        last_date = datetime.strptime(last_study_date, "%Y-%m-%d").date()
                        yesterday = datetime.now().date() - datetime.timedelta(days=1)
                        
                        if last_date == yesterday:
                            # Consecutive day
                            new_streak = current_streak + 1
                        else:
                            # Break in streak
                            new_streak = 1
                    else:
                        # First study day
                        new_streak = 1
                    
                    # Update streaks
                    supabase.table("user_streaks").update({
                        "current_streak": new_streak,
                        "longest_streak": max(new_streak, longest_streak),
                        "last_study_date": today,
                        "points": (streaks_response.data[0]["points"] or 0) + 10,  # 10 points per day
                        "updated_at": datetime.now().isoformat()
                    }).eq("user_id", user_id).execute()
        
        return TopicProgress(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update topic progress: {str(e)}"
        )

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(user_id: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=100)):
    """
    Get leaderboard data
    """
    try:
        # Get all users with their statistics and streaks
        stats_response = supabase.table("user_statistics").select("user_id, total_lessons, total_study_time_minutes, total_tests_completed").execute()
        streaks_response = supabase.table("user_streaks").select("user_id, current_streak, longest_streak, points").execute()
        profiles_response = supabase.table("profiles").select("id, email, avatar_url").execute()
        
        # Create lookup dictionaries
        stats_lookup = {stat["user_id"]: stat for stat in stats_response.data} if stats_response.data else {}
        streaks_lookup = {streak["user_id"]: streak for streak in streaks_response.data} if streaks_response.data else {}
        profiles_lookup = {profile["id"]: profile for profile in profiles_response.data} if profiles_response.data else {}
        
        # Combine data and calculate scores
        leaderboard_entries = []
        
        for user_id_key in set(list(stats_lookup.keys()) + list(streaks_lookup.keys())):
            stats = stats_lookup.get(user_id_key, {})
            streaks = streaks_lookup.get(user_id_key, {})
            profile = profiles_lookup.get(user_id_key, {})
            
            # Calculate total score (you can adjust this formula)
            total_score = (
                (stats.get("total_lessons", 0) * 10) +
                (stats.get("total_study_time_minutes", 0) * 0.1) +
                (streaks.get("points", 0) * 2) +
                (streaks.get("longest_streak", 0) * 50)
            )
            
            leaderboard_entries.append({
                "user_id": user_id_key,
                "email": profile.get("email"),
                "avatar_url": profile.get("avatar_url"),
                "total_points": int(total_score),
                "current_streak": streaks.get("current_streak", 0),
                "longest_streak": streaks.get("longest_streak", 0),
                "total_study_time_minutes": stats.get("total_study_time_minutes", 0),
                "total_lessons": stats.get("total_lessons", 0),
                "rank": 0  # Will be set after sorting
            })
        
        # Sort by total points (descending) and assign ranks
        leaderboard_entries.sort(key=lambda x: x["total_points"], reverse=True)
        
        for i, entry in enumerate(leaderboard_entries):
            entry["rank"] = i + 1
        
        # Limit results
        limited_entries = leaderboard_entries[:limit]
        
        # Find user's rank if user_id is provided
        user_rank = None
        if user_id:
            for entry in leaderboard_entries:
                if entry["user_id"] == user_id:
                    user_rank = entry["rank"]
                    break
        
        return LeaderboardResponse(
            leaderboard=limited_entries,
            total_participants=len(leaderboard_entries),
            user_rank=user_rank,
            updated_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leaderboard: {str(e)}"
        )

@router.get("/{user_id}/activity")
async def get_user_activity(user_id: str, days: int = Query(30, ge=1, le=365)):
    """
    Get user activity for the last N days
    """
    try:
        if days > 365:
            days = 365  # Limit to 1 year
        
        start_date = (datetime.now() - datetime.timedelta(days=days)).date().isoformat()
        
        response = supabase.table("user_activity").select("*").eq("user_id", user_id).gte("date", start_date).order("date", desc=True).execute()
        
        if not response.data:
            return []
        
        return [UserActivity(**activity) for activity in response.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user activity: {str(e)}"
        )

@router.get("/{user_id}/streaks")
async def get_user_streaks(user_id: str):
    """
    Get detailed user streak information
    """
    try:
        response = supabase.table("user_streaks").select("*").eq("user_id", user_id).execute()
        
        if not response.data:
            return UserStreaks(
                current_streak=0,
                longest_streak=0,
                last_study_date=None,
                points=0,
                hearts=5,
                created_at=datetime.now().isoformat()
            )
        
        return UserStreaks(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user streaks: {str(e)}"
        )
