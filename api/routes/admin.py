from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv


# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter()

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Security
security = HTTPBearer()

# Models
class AdminCreateRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class AdminResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_admin: bool
    admin_expires_at: Optional[str] = None
    created_at: str
    updated_at: str

class AdminListResponse(BaseModel):
    admins: List[AdminResponse]
    total: int

# Helper function to get current admin user
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        # Verify the JWT token with Supabase
        user = supabase.auth.get_user(credentials.credentials)
        
        # Check if user is admin
        profile_response = supabase.table("profiles").select("is_admin, admin_expires_at").eq("id", user.user.id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Profile not found"
            )
        
        profile = profile_response.data[0]
        
        # Check if user is admin and privileges haven't expired
        if not profile.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        if profile.get("admin_expires_at"):
            expires_at = datetime.fromisoformat(profile["admin_expires_at"].replace('Z', '+00:00'))
            if datetime.now(expires_at.tzinfo) > expires_at:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin privileges have expired"
                )
        
        return user.user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/create-admin", response_model=AdminResponse)
async def create_admin(request: AdminCreateRequest, current_admin: dict = Depends(get_current_admin)):
    """
    Create a new admin account (only existing admins can create new admins)
    """
    try:
        import uuid
        
        # Check if user already exists
        existing_user = supabase.auth.admin.list_users()
        user_exists = any(user.email == request.email for user in existing_user.users)
        
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Create user in Supabase auth
        auth_response = supabase.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user in auth system"
            )
        
        user_id = auth_response.user.id
        
        # Set admin privileges for 30 days
        admin_expires_at = datetime.utcnow() + timedelta(days=30)
        
        # Create profile with admin privileges
        profile_data = {
            "id": user_id,
            "email": request.email,
            "is_admin": True,
            "admin_expires_at": admin_expires_at.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("profiles").insert(profile_data).execute()
        
        # Create onboarding data
        onboarding_data = {
            "user_id": user_id,
            "heard_from": "admin_created",
            "learning_reason": "admin_access",
            "daily_goal": 60
        }
        supabase.table("onboarding_data").insert(onboarding_data).execute()
        
        # Create user statistics
        stats_data = {
            "user_id": user_id,
            "total_lessons": 0,
            "total_study_time_minutes": 0,
            "total_tests_completed": 0
        }
        supabase.table("user_statistics").insert(stats_data).execute()
        
        # Create user streaks
        streaks_data = {
            "user_id": user_id,
            "current_streak": 0,
            "longest_streak": 0,
            "last_study_date": None,
            "points": 0,
            "hearts": 5
        }
        supabase.table("user_streaks").insert(streaks_data).execute()
        
        return AdminResponse(
            id=user_id,
            email=request.email,
            full_name=request.full_name,
            is_admin=True,
            admin_expires_at=admin_expires_at.isoformat(),
            created_at=profile_data["created_at"],
            updated_at=profile_data["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin: {str(e)}"
        )

@router.get("/admins", response_model=AdminListResponse)
async def list_admins(current_admin: dict = Depends(get_current_admin)):
    """
    List all admin accounts
    """
    try:
        # Get all admin profiles
        response = supabase.table("profiles").select("*").eq("is_admin", True).execute()
        
        admins = []
        for profile in response.data:
            admin = AdminResponse(
                id=profile["id"],
                email=profile["email"],
                full_name=profile.get("full_name"),
                is_admin=profile.get("is_admin", False),
                admin_expires_at=profile.get("admin_expires_at"),
                created_at=profile["created_at"],
                updated_at=profile["updated_at"]
            )
            admins.append(admin)
        
        return AdminListResponse(admins=admins, total=len(admins))
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list admins: {str(e)}"
        )

@router.post("/extend-admin/{user_id}")
async def extend_admin_privileges(
    user_id: str, 
    days: int = Query(30, ge=1, le=365),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Extend admin privileges for a user
    """
    try:
        # Get current profile
        profile_response = supabase.table("profiles").select("is_admin, admin_expires_at").eq("id", user_id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        profile = profile_response.data[0]
        
        if not profile.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not an admin"
            )
        
        # Calculate new expiration date
        current_expires = profile.get("admin_expires_at")
        if current_expires:
            current_expires_dt = datetime.fromisoformat(current_expires.replace('Z', '+00:00'))
            new_expires = current_expires_dt + timedelta(days=days)
        else:
            new_expires = datetime.utcnow() + timedelta(days=days)
        
        # Update admin expiration
        supabase.table("profiles").update({
            "admin_expires_at": new_expires.isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        
        return {
            "message": f"Admin privileges extended by {days} days",
            "new_expires_at": new_expires.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extend admin privileges: {str(e)}"
        )

@router.delete("/revoke-admin/{user_id}")
async def revoke_admin_privileges(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Revoke admin privileges from a user
    """
    try:
        # Prevent admin from revoking their own privileges
        if user_id == current_admin["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot revoke your own admin privileges"
            )
        
        # Update profile to remove admin privileges
        supabase.table("profiles").update({
            "is_admin": False,
            "admin_expires_at": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        
        return {"message": "Admin privileges revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke admin privileges: {str(e)}"
        )

@router.get("/admin-status")
async def get_admin_status(current_admin: dict = Depends(get_current_admin)):
    """
    Get current admin's status and privileges
    """
    try:
        profile_response = supabase.table("profiles").select("*").eq("id", current_admin["id"]).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        profile = profile_response.data[0]
        
        return {
            "id": profile["id"],
            "email": profile["email"],
            "is_admin": profile.get("is_admin", False),
            "admin_expires_at": profile.get("admin_expires_at"),
            "days_remaining": None if not profile.get("admin_expires_at") else 
                max(0, (datetime.fromisoformat(profile["admin_expires_at"].replace('Z', '+00:00')) - datetime.now()).days)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin status: {str(e)}"
        )

