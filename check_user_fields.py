#!/usr/bin/env python3
"""
Script to check user fields in profiles table
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

def check_user_fields():
    """Check what fields a user has in the profiles table"""
    
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
        
        # Test email
        email = "admin@tegus.com"
        
        print(f"🔍 Checking fields for user: {email}")
        
        # Get user profile
        profile_response = supabase.table("profiles").select("*").eq("email", email).execute()
        
        if not profile_response.data:
            print(f"❌ User {email} not found in profiles table")
            return False
        
        profile = profile_response.data[0]
        print(f"✅ User found: {profile['id']}")
        
        print(f"\n📋 User profile fields:")
        print("-" * 40)
        for key, value in profile.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_user_fields()
