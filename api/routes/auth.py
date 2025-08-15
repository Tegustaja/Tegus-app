from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter()

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"SUPABASE_URL: {SUPABASE_URL}")  # Debug logging
print(f"SUPABASE_KEY: {SUPABASE_KEY[:20] if SUPABASE_KEY else 'None'}...")  # Debug logging

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("Supabase client created successfully")  # Debug logging

# Security
security = HTTPBearer()

# Models
class SignUpRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=6)

class SignInRequest(BaseModel):
    email: str
    password: str

class ProfileResponse(BaseModel):
    id: str
    email: str
    avatar_url: Optional[str] = None
    updated_at: Optional[str] = None
    is_admin: bool = False
    admin_expires_at: Optional[str] = None
    onboarding_completed: bool = False

class ProfileUpdateRequest(BaseModel):
    avatar_url: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: ProfileResponse

# Helper function to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        # Verify the JWT token with Supabase
        user = supabase.auth.get_user(credentials.credentials)
        return user.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/sign-up", response_model=AuthResponse)
async def sign_up(request: SignUpRequest):
    """
    Register a new user with password hashing
    """
    try:
        import uuid
        import bcrypt
        from datetime import datetime
        
        # Generate a UUID for the user
        user_id = str(uuid.uuid4())
        
        # Hash the password
        password_bytes = request.password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt)
        
        # Create profile record with password hash
        profile_data = {
            "id": user_id,
            "email": request.email,
            "password_hash": password_hash.decode('utf-8'),
            "salt": salt.decode('utf-8'),
            "email_verified": True,  # Default to verified for new signups
            "account_status": "active",  # Default to active status
            "is_admin": False,  # Default to non-admin for new signups
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        print(f"Creating profile for user {user_id}")  # Debug logging
        profile_result = supabase.table("profiles").insert(profile_data).execute()
        print(f"Profile created: {profile_result}")  # Debug logging
        
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
        
        # Get the created profile
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        profile = profile_response.data[0] if profile_response.data else {}
        
        profile_data = ProfileResponse(
            id=user_id,
            email=profile.get("email", request.email),
            avatar_url=profile.get("avatar_url"),
            updated_at=profile.get("updated_at"),
            is_admin=profile.get("is_admin", False),
            admin_expires_at=profile.get("admin_expires_at"),
            onboarding_completed=False
        )
        
        # For testing purposes, return a mock auth response
        # In production, you'd want to implement proper JWT token generation
        mock_token = f"mock_token_{user_id}"
        
        return AuthResponse(
            access_token=mock_token,
            refresh_token=mock_token,
            user=profile_data
        )
        
    except Exception as e:
        print(f"Sign-up error: {e}")  # Debug logging
        if "already registered" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.post("/sign-in", response_model=AuthResponse)
async def sign_in(request: SignInRequest):
    """
    Authenticate existing user with local password verification
    """
    try:
        import bcrypt
        
        # Find user by email
        profile_response = supabase.table("profiles").select("*").eq("email", request.email).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        profile = profile_response.data[0]
        user_id = profile["id"]
        
        # Verify password
        stored_password_hash = profile.get("password_hash")
        stored_salt = profile.get("salt")
        
        if not stored_password_hash or not stored_salt:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password using bcrypt.checkpw
        password_bytes = request.password.encode('utf-8')
        stored_hash_bytes = stored_password_hash.encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, stored_hash_bytes):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        profile_data = ProfileResponse(
            id=user_id,
            email=profile.get("email", request.email),
            avatar_url=profile.get("avatar_url"),
            updated_at=profile.get("updated_at"),
            is_admin=profile.get("is_admin", False),
            admin_expires_at=profile.get("admin_expires_at"),
            onboarding_completed=False
        )
        
        # Generate mock tokens for now (in production, implement proper JWT)
        mock_token = f"mock_token_{user_id}"
        
        return AuthResponse(
            access_token=mock_token,
            refresh_token=mock_token,
            user=profile_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user's profile information
    """
    try:
        user_id = current_user["id"]
        
        # Get profile data
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        profile = profile_response.data[0] if profile_response.data else {}
        
        return ProfileResponse(
            id=user_id,
            email=profile.get("email", current_user.get("email", "")),
            avatar_url=profile.get("avatar_url"),
            updated_at=profile.get("updated_at"),
            is_admin=profile.get("is_admin", False),
            admin_expires_at=profile.get("admin_expires_at"),
            onboarding_completed=False
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )

@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update current user's profile information
    """
    try:
        user_id = current_user["id"]
        
        # Update profile if avatar_url is provided
        if request.avatar_url is not None:
            supabase.table("profiles").update({
                "avatar_url": request.avatar_url,
                "updated_at": "now()"
            }).eq("id", user_id).execute()
        
        # Get updated profile
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        profile = profile_response.data[0] if profile_response.data else {}
        
        return ProfileResponse(
            id=user_id,
            email=profile.get("email", current_user.get("email", "")),
            avatar_url=profile.get("avatar_url"),
            updated_at=profile.get("updated_at"),
            is_admin=profile.get("is_admin", False),
            admin_expires_at=profile.get("admin_expires_at"),
            onboarding_completed=False
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

@router.post("/sign-out")
async def sign_out(current_user: dict = Depends(get_current_user)):
    """
    Sign out current user (invalidate tokens)
    """
    try:
        # Supabase handles token invalidation automatically
        # This endpoint can be used for additional cleanup if needed
        return {"message": "Successfully signed out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sign out: {str(e)}"
        )

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token
    """
    try:
        # Refresh token with Supabase
        auth_response = supabase.auth.refresh_session(refresh_token)
        
        if not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # For now, return mock tokens (in production, implement proper JWT refresh)
        mock_token = f"refreshed_mock_token_{int(datetime.utcnow().timestamp())}"
        
        return {
            "access_token": mock_token,
            "refresh_token": mock_token
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/admin-sign-in")
async def admin_sign_in(request: SignInRequest):
    """
    Special sign-in for admin accounts with extended authorization
    """
    try:
        # Sign in with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_id = auth_response.user.id
        
        # Get user profile and check admin status
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        profile = profile_response.data[0] if profile_response.data else {}
        
        # Check if user is admin
        if not profile.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        # Check if admin privileges have expired
        admin_expires_at = profile.get("admin_expires_at")
        if admin_expires_at:
            expires_at = datetime.fromisoformat(admin_expires_at.replace('Z', '+00:00'))
            if datetime.now(expires_at.tzinfo) > expires_at:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin privileges have expired"
                )
        
        profile_data = ProfileResponse(
            id=user_id,
            email=profile.get("email", request.email),
            avatar_url=profile.get("avatar_url"),
            updated_at=profile.get("updated_at"),
            is_admin=profile.get("is_admin", False),
            admin_expires_at=profile.get("admin_expires_at"),
            onboarding_completed=False
        )
        
        # For admin accounts, generate mock tokens (in production, implement proper JWT)
        mock_token = f"admin_mock_token_{user_id}"
        
        return AuthResponse(
            access_token=mock_token,
            refresh_token=mock_token,
            user=profile_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        ) 