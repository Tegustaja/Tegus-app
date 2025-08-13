from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter(prefix="/settings")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class UserSettings(BaseModel):
    user_id: str
    theme: str = Field(default="light", description="light, dark, auto")
    language: str = Field(default="en", description="Language code")
    notifications_enabled: bool = Field(default=True)
    email_notifications: bool = Field(default=True)
    push_notifications: bool = Field(default=True)
    sound_enabled: bool = Field(default=True)
    auto_save: bool = Field(default=True)
    privacy_level: str = Field(default="standard", description="public, standard, private")
    timezone: str = Field(default="UTC")
    created_at: str
    updated_at: str

class UpdateSettingsRequest(BaseModel):
    theme: Optional[str] = Field(None, description="light, dark, auto")
    language: Optional[str] = Field(None, description="Language code")
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    auto_save: Optional[bool] = None
    privacy_level: Optional[str] = Field(None, description="public, standard, private")
    timezone: Optional[str] = None

class LearningPreferences(BaseModel):
    user_id: str
    daily_goal: int = Field(..., ge=1, le=480, description="Daily study goal in minutes (1-480)")
    learning_reason: str
    heard_from: str
    preferred_subjects: List[str] = Field(default_factory=list)
    preferred_difficulty: str = Field(default="medium", description="easy, medium, hard")
    study_reminders: bool = Field(default=True)
    reminder_time: str = Field(default="09:00", description="HH:MM format")
    study_days: List[str] = Field(default_factory=lambda: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
    max_session_duration: int = Field(default=60, ge=15, le=180, description="Maximum session duration in minutes")
    break_reminders: bool = Field(default=True)
    break_interval: int = Field(default=25, ge=15, le=60, description="Break reminder interval in minutes")
    created_at: str
    updated_at: str

class UpdatePreferencesRequest(BaseModel):
    daily_goal: Optional[int] = Field(None, ge=1, le=480)
    learning_reason: Optional[str] = None
    heard_from: Optional[str] = None
    preferred_subjects: Optional[List[str]] = None
    preferred_difficulty: Optional[str] = Field(None, description="easy, medium, hard")
    study_reminders: Optional[bool] = None
    reminder_time: Optional[str] = Field(None, description="HH:MM format")
    study_days: Optional[List[str]] = None
    max_session_duration: Optional[int] = Field(None, ge=15, le=180)
    break_reminders: Optional[bool] = None
    break_interval: Optional[int] = Field(None, ge=15, le=60)

class NotificationSettings(BaseModel):
    user_id: str
    lesson_completion: bool = Field(default=True)
    streak_reminders: bool = Field(default=True)
    weekly_progress: bool = Field(default=True)
    new_content: bool = Field(default=True)
    achievement_notifications: bool = Field(default=True)
    social_notifications: bool = Field(default=True)
    marketing_emails: bool = Field(default=False)
    created_at: str
    updated_at: str

@router.get("/{user_id}", response_model=UserSettings)
async def get_user_settings(user_id: str):
    """
    Get user settings
    """
    try:
        # Get user settings from database
        response = supabase.table("user_settings").select("*").eq("user_id", user_id).execute()
        
        if not response.data:
            # Create default settings if none exist
            default_settings = {
                "user_id": user_id,
                "theme": "light",
                "language": "en",
                "notifications_enabled": True,
                "email_notifications": True,
                "push_notifications": True,
                "sound_enabled": True,
                "auto_save": True,
                "privacy_level": "standard",
                "timezone": "UTC",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            supabase.table("user_settings").insert(default_settings).execute()
            
            return UserSettings(**default_settings)
        
        return UserSettings(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user settings: {str(e)}"
        )

@router.put("/{user_id}", response_model=UserSettings)
async def update_user_settings(user_id: str, request: UpdateSettingsRequest):
    """
    Update user settings
    """
    try:
        # Validate input values
        if request.theme and request.theme not in ["light", "dark", "auto"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid theme. Must be 'light', 'dark', or 'auto'"
            )
        
        if request.privacy_level and request.privacy_level not in ["public", "standard", "private"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid privacy level. Must be 'public', 'standard', or 'private'"
            )
        
        # Prepare update data
        update_data = {
            "updated_at": datetime.now().isoformat()
        }
        
        # Add fields that were provided
        if request.theme is not None:
            update_data["theme"] = request.theme
        if request.language is not None:
            update_data["language"] = request.language
        if request.notifications_enabled is not None:
            update_data["notifications_enabled"] = request.notifications_enabled
        if request.email_notifications is not None:
            update_data["email_notifications"] = request.email_notifications
        if request.push_notifications is not None:
            update_data["push_notifications"] = request.push_notifications
        if request.sound_enabled is not None:
            update_data["sound_enabled"] = request.sound_enabled
        if request.auto_save is not None:
            update_data["auto_save"] = request.auto_save
        if request.privacy_level is not None:
            update_data["privacy_level"] = request.privacy_level
        if request.timezone is not None:
            update_data["timezone"] = request.timezone
        
        # Update settings
        response = supabase.table("user_settings").update(update_data).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user settings"
            )
        
        return UserSettings(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user settings: {str(e)}"
        )

@router.get("/{user_id}/preferences", response_model=LearningPreferences)
async def get_learning_preferences(user_id: str):
    """
    Get learning preferences
    """
    try:
        # Get onboarding data which contains learning preferences
        response = supabase.table("onboarding_data").select("*").eq("user_id", user_id).execute()
        
        if not response.data:
            # Create default preferences if none exist
            default_preferences = {
                "user_id": user_id,
                "daily_goal": 30,
                "learning_reason": "Personal development",
                "heard_from": "Search engine",
                "preferred_subjects": [],
                "preferred_difficulty": "medium",
                "study_reminders": True,
                "reminder_time": "09:00",
                "study_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "max_session_duration": 60,
                "break_reminders": True,
                "break_interval": 25,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            supabase.table("onboarding_data").insert(default_preferences).execute()
            
            return LearningPreferences(**default_preferences)
        
        # Convert onboarding data to preferences format
        onboarding = response.data[0]
        
        # Parse preferred subjects if stored as JSON
        preferred_subjects = onboarding.get("preferred_subjects", [])
        if isinstance(preferred_subjects, str):
            try:
                import json
                preferred_subjects = json.loads(preferred_subjects)
            except:
                preferred_subjects = []
        
        # Parse study days if stored as JSON
        study_days = onboarding.get("study_days", ["monday", "tuesday", "wednesday", "thursday", "friday"])
        if isinstance(study_days, str):
            try:
                import json
                study_days = json.loads(study_days)
            except:
                study_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        
        preferences_data = {
            "user_id": user_id,
            "daily_goal": onboarding.get("daily_goal", 30),
            "learning_reason": onboarding.get("learning_reason", "Personal development"),
            "heard_from": onboarding.get("heard_from", "Search engine"),
            "preferred_subjects": preferred_subjects if isinstance(preferred_subjects, list) else [],
            "preferred_difficulty": onboarding.get("preferred_difficulty", "medium"),
            "study_reminders": onboarding.get("study_reminders", True),
            "reminder_time": onboarding.get("reminder_time", "09:00"),
            "study_days": study_days if isinstance(study_days, list) else ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "max_session_duration": onboarding.get("max_session_duration", 60),
            "break_reminders": onboarding.get("break_reminders", True),
            "break_interval": onboarding.get("break_interval", 25),
            "created_at": onboarding.get("created_at", datetime.now().isoformat()),
            "updated_at": onboarding.get("updated_at", datetime.now().isoformat())
        }
        
        return LearningPreferences(**preferences_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch learning preferences: {str(e)}"
        )

@router.put("/{user_id}/preferences", response_model=LearningPreferences)
async def update_learning_preferences(user_id: str, request: UpdatePreferencesRequest):
    """
    Update learning preferences
    """
    try:
        # Validate input values
        if request.preferred_difficulty and request.preferred_difficulty not in ["easy", "medium", "hard"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid preferred difficulty. Must be 'easy', 'medium', or 'hard'"
            )
        
        if request.reminder_time:
            try:
                datetime.strptime(request.reminder_time, "%H:%M")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reminder time format. Use HH:MM format"
                )
        
        if request.study_days:
            valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for day in request.study_days:
                if day.lower() not in valid_days:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid study day: {day}. Must be one of: {valid_days}"
                    )
        
        # Prepare update data
        update_data = {
            "updated_at": datetime.now().isoformat()
        }
        
        # Add fields that were provided
        if request.daily_goal is not None:
            update_data["daily_goal"] = request.daily_goal
        if request.learning_reason is not None:
            update_data["learning_reason"] = request.learning_reason
        if request.heard_from is not None:
            update_data["heard_from"] = request.heard_from
        if request.preferred_subjects is not None:
            update_data["preferred_subjects"] = request.preferred_subjects
        if request.preferred_difficulty is not None:
            update_data["preferred_difficulty"] = request.preferred_difficulty
        if request.study_reminders is not None:
            update_data["study_reminders"] = request.study_reminders
        if request.reminder_time is not None:
            update_data["reminder_time"] = request.reminder_time
        if request.study_days is not None:
            update_data["study_days"] = request.study_days
        if request.max_session_duration is not None:
            update_data["max_session_duration"] = request.max_session_duration
        if request.break_reminders is not None:
            update_data["break_reminders"] = request.break_reminders
        if request.break_interval is not None:
            update_data["break_interval"] = request.break_interval
        
        # Update preferences in onboarding_data table
        response = supabase.table("onboarding_data").update(update_data).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update learning preferences"
            )
        
        # Return updated preferences
        return await get_learning_preferences(user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update learning preferences: {str(e)}"
        )

@router.get("/{user_id}/notifications", response_model=NotificationSettings)
async def get_notification_settings(user_id: str):
    """
    Get notification settings
    """
    try:
        # Get notification settings from database
        response = supabase.table("notification_settings").select("*").eq("user_id", user_id).execute()
        
        if not response.data:
            # Create default notification settings if none exist
            default_notifications = {
                "user_id": user_id,
                "lesson_completion": True,
                "streak_reminders": True,
                "weekly_progress": True,
                "new_content": True,
                "achievement_notifications": True,
                "social_notifications": True,
                "marketing_emails": False,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            supabase.table("notification_settings").insert(default_notifications).execute()
            
            return NotificationSettings(**default_notifications)
        
        return NotificationSettings(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notification settings: {str(e)}"
        )

@router.put("/{user_id}/notifications")
async def update_notification_settings(user_id: str, settings: Dict[str, bool]):
    """
    Update notification settings
    """
    try:
        # Validate notification settings
        valid_settings = [
            "lesson_completion", "streak_reminders", "weekly_progress", 
            "new_content", "achievement_notifications", "social_notifications", "marketing_emails"
        ]
        
        for key in settings.keys():
            if key not in valid_settings:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid notification setting: {key}"
                )
        
        # Prepare update data
        update_data = {
            **settings,
            "updated_at": datetime.now().isoformat()
        }
        
        # Update notification settings
        response = supabase.table("notification_settings").update(update_data).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update notification settings"
            )
        
        return {"message": "Notification settings updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification settings: {str(e)}"
        )

@router.get("/{user_id}/export")
async def export_user_data(user_id: str):
    """
    Export all user data and settings
    """
    try:
        # Get all user data from various tables
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        onboarding_response = supabase.table("onboarding_data").select("*").eq("user_id", user_id).execute()
        settings_response = supabase.table("user_settings").select("*").eq("user_id", user_id).execute()
        progress_response = supabase.table("user_progress").select("*").eq("user_id", user_id).execute()
        stats_response = supabase.table("user_statistics").select("*").eq("user_id", user_id).execute()
        streaks_response = supabase.table("user_streaks").select("*").eq("user_id", user_id).execute()
        
        # Compile export data
        export_data = {
            "export_date": datetime.now().isoformat(),
            "user_id": user_id,
            "profile": profile_response.data[0] if profile_response.data else {},
            "learning_preferences": onboarding_response.data[0] if onboarding_response.data else {},
            "settings": settings_response.data[0] if settings_response.data else {},
            "progress": progress_response.data if progress_response.data else [],
            "statistics": stats_response.data[0] if stats_response.data else {},
            "streaks": streaks_response.data[0] if streaks_response.data else {}
        }
        
        return export_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export user data: {str(e)}"
        )
