from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import jwt
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Import centralized Supabase client
from ..config import supabase_client
from app.logger import logger

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter(prefix="/auth")

# Check if Supabase client is available
if not supabase_client:
    raise ValueError("Supabase client not configured. Please check SUPABASE_URL and SUPABASE_KEY environment variables.")

# Models
class SignInRequest(BaseModel):
    email: str
    password: str

class SignUpRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

async def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Verify Supabase JWT token and return user info
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify the token with Supabase
        user_response = supabase_client.auth.get_user(token)
        
        if hasattr(user_response, 'error') and user_response.error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        if not hasattr(user_response, 'user') or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user profile from profiles table
        profile_response = supabase_client.table("profiles").select("*").eq("id", user_response.user.id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        profile = profile_response.data[0]
        
        return {
            "id": profile["id"],
            "email": profile.get("email", user_response.user.email),
            "is_admin": profile.get("is_admin", False),
            "admin_expires_at": profile.get("admin_expires_at"),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.post("/sign-up", response_model=AuthResponse)
async def sign_up(request: SignUpRequest):
    """
    Create new user account using Supabase Auth
    """
    try:
        print(f"🔐 Creating user in Supabase Auth: {request.email}")
        
        # Create user in Supabase Auth
        auth_response = supabase_client.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name,
                }
            }
        })
        
        print(f"📊 Supabase Auth response: {auth_response}")
        
        # Check for errors in the response
        if hasattr(auth_response, 'error') and auth_response.error:
            print(f"❌ Supabase Auth error: {auth_response.error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=auth_response.error.message
            )
        
        # Check if user was created
        if not hasattr(auth_response, 'data') or not auth_response.data or not auth_response.data.user:
            print(f"❌ No user data in response: {auth_response}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user in Supabase Auth"
            )
        
        user_id = auth_response.data.user.id
        print(f"✅ User created in Supabase Auth with ID: {user_id}")
        
        # Create profile in profiles table
        profile_data = {
            "id": user_id,
            "email": request.email,
            "full_name": request.full_name,
            "is_admin": False,
            "email_verified": False,
            "account_status": "active",
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        
        print(f"📝 Creating profile in profiles table...")
        profile_response = supabase_client.table("profiles").insert(profile_data).execute()
        
        if hasattr(profile_response, 'error') and profile_response.error:
            print(f"❌ Profile creation error: {profile_response.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile"
            )
        
        print(f"✅ Profile created successfully")
        
        # Return the session data from Supabase
        if hasattr(auth_response.data, 'session') and auth_response.data.session:
            print(f"✅ User has session, returning tokens")
            return AuthResponse(
                access_token=auth_response.data.session.access_token,
                refresh_token=auth_response.data.session.refresh_token,
                user={
                    "id": user_id,
                    "email": request.email,
                    "full_name": request.full_name,
                    "is_admin": False,
                    "created_at": profile_data["created_at"],
                }
            )
        else:
            # Email confirmation required
            print(f"ℹ️ Email confirmation required")
            return AuthResponse(
                access_token="",
                refresh_token="",
                user={
                    "id": user_id,
                    "email": request.email,
                    "full_name": request.full_name,
                    "is_admin": False,
                    "created_at": profile_data["created_at"],
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in sign_up: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.post("/sign-in", response_model=AuthResponse)
async def sign_in(request: SignInRequest):
    """
    Authenticate user using Supabase Auth
    """
    try:
        print(f"🔐 Signing in user: {request.email}")
        
        # Sign in with Supabase
        auth_response = supabase_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })
        
        print(f"📊 Supabase Auth response: {auth_response}")
        
        # Check for errors in the response
        if hasattr(auth_response, 'error') and auth_response.error:
            print(f"❌ Supabase Auth error: {auth_response.error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login credentials"
            )
        
        # Check if authentication was successful
        if not hasattr(auth_response, 'data') or not auth_response.data or not auth_response.data.user or not auth_response.data.session:
            print(f"❌ No user or session data in response")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
        
        user_id = auth_response.data.user.id
        print(f"✅ User authenticated successfully: {user_id}")
        
        # Get user profile from profiles table
        profile_response = supabase_client.table("profiles").select("*").eq("id", user_id).execute()
        
        if not profile_response.data:
            print(f"❌ User profile not found for ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        profile = profile_response.data[0]
        print(f"✅ User profile found")
        
        return AuthResponse(
            access_token=auth_response.data.session.access_token,
            refresh_token=auth_response.data.session.refresh_token,
            user={
                "id": profile["id"],
                "email": profile.get("email", request.email),
                "full_name": profile.get("full_name"),
                "is_admin": profile.get("is_admin", False),
                "admin_expires_at": profile.get("admin_expires_at"),
                "created_at": profile["created_at"],
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in sign_in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.post("/admin-sign-in", response_model=AuthResponse)
async def admin_sign_in(request: SignInRequest):
    """
    Authenticate admin user using Supabase Auth
    """
    try:
        print(f"🔐 Admin sign in: {request.email}")
        
        # Sign in with Supabase
        auth_response = supabase_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })
        
        print(f"📊 Supabase Auth response: {auth_response}")
        
        # Check for errors in the response
        if hasattr(auth_response, 'error') and auth_response.error:
            print(f"❌ Supabase Auth error: {auth_response.error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login credentials"
            )
        
        # Check if authentication was successful
        if not hasattr(auth_response, 'data') or not auth_response.data or not auth_response.data.user or not auth_response.data.session:
            print(f"❌ No user or session data in response")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
        
        user_id = auth_response.data.user.id
        print(f"✅ User authenticated successfully: {user_id}")
        
        # Get user profile from profiles table
        profile_response = supabase_client.table("profiles").select("*").eq("id", user_id).execute()
        
        if not profile_response.data:
            print(f"❌ User profile not found for ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        profile = profile_response.data[0]
        print(f"✅ User profile found")
        
        # Check if user is admin
        if not profile.get("is_admin", False):
            print(f"❌ User is not an admin")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not an admin"
            )
        
        # Check if admin privileges haven't expired
        if profile.get("admin_expires_at") and profile["admin_expires_at"] < str(datetime.datetime.utcnow()):
            print(f"❌ Admin privileges have expired")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges have expired"
            )
        
        print(f"✅ Admin authentication successful")
        
        return AuthResponse(
            access_token=auth_response.data.session.access_token,
            refresh_token=auth_response.data.session.refresh_token,
            user={
                "id": profile["id"],
                "email": profile.get("email", request.email),
                "full_name": profile.get("full_name"),
                "is_admin": True,
                "admin_expires_at": profile.get("admin_expires_at"),
                "created_at": profile["created_at"],
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in admin_sign_in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.post("/sign-out")
async def sign_out(current_user: dict = Depends(get_current_user)):
    """
    Sign out user (Supabase handles this automatically)
    """
    return {"message": "Signed out successfully"}

@router.get("/profile", response_model=dict)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile
    """
    try:
        profile_response = supabase_client.table("profiles").select("*").eq("id", current_user["id"]).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        profile = profile_response.data[0]
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )

@router.put("/profile", response_model=dict)
async def update_profile(
    updates: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update current user profile
    """
    try:
        update_data = {}
        if updates.full_name is not None:
            update_data["full_name"] = updates.full_name
        if updates.avatar_url is not None:
            update_data["avatar_url"] = updates.avatar_url
        
        update_data["updated_at"] = datetime.datetime.utcnow().isoformat()
        
        profile_response = supabase_client.table("profiles").update(update_data).eq("id", current_user["id"]).execute()
        
        if hasattr(profile_response, 'error') and profile_response.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        return {"message": "Profile updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: dict):
    """
    Refresh access token using refresh token
    """
    try:
        refresh_token_value = request.get("refresh_token")
        if not refresh_token_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        # Refresh the session with Supabase
        auth_response = supabase_client.auth.refresh_session(refresh_token_value)
        
        if hasattr(auth_response, 'error') and auth_response.error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        if not hasattr(auth_response, 'data') or not auth_response.data or not auth_response.data.session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh token"
            )
        
        return AuthResponse(
            access_token=auth_response.data.session.access_token,
            refresh_token=auth_response.data.session.refresh_token,
            user={
                "id": auth_response.data.user.id,
                "email": auth_response.data.user.email,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh token: {str(e)}"
        ) 