#!/usr/bin/env python3
"""
Script to create a user in Supabase Auth
This will create a user that can authenticate with the current auth system
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

def create_supabase_user():
    """Create a user in Supabase Auth"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        return False
    
    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase successfully")
        
        # User details
        email = "admin@tegus.com"
        password = "admin123"
        
        print(f"👤 Creating user in Supabase Auth: {email}")
        
        # Create user in Supabase Auth
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": "Admin User"
            }
        })
        
        if auth_response.error:
            print(f"❌ Error creating user in Supabase Auth: {auth_response.error.message}")
            return False
        
        if not auth_response.data.user:
            print("❌ No user data returned from Supabase Auth")
            return False
        
        user_id = auth_response.data.user.id
        print(f"✅ User created in Supabase Auth with ID: {user_id}")
        
        # Now create/update the profile in the profiles table
        print("📝 Creating profile in profiles table...")
        
        profile_data = {
            "id": user_id,
            "email": email,
            "full_name": "Admin User",
            "is_admin": True,
            "email_verified": True,
            "account_status": "active"
        }
        
        # Check if profile already exists
        existing_profile = supabase.table("profiles").select("id").eq("id", user_id).execute()
        
        if existing_profile.data:
            # Update existing profile
            supabase.table("profiles").update(profile_data).eq("id", user_id).execute()
            print("✅ Profile updated in profiles table")
        else:
            # Create new profile
            supabase.table("profiles").insert(profile_data).execute()
            print("✅ Profile created in profiles table")
        
        print(f"\n🎉 User '{email}' created successfully!")
        print(f"   - Supabase Auth ID: {user_id}")
        print(f"   - Email: {email}")
        print(f"   - Password: {password}")
        print(f"   - Admin privileges: Enabled")
        print(f"\n💡 You can now sign in with these credentials!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_supabase_user()
