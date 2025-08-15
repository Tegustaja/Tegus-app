#!/usr/bin/env python3
"""
Create Basic User Profiles

This script creates some basic user profiles so we can create lessons
that reference them through foreign key constraints.

Usage:
    python3 scripts/create_basic_profiles.py [--count N] [--dry-run]
"""

import sys
import os
import uuid
import random
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to the path so we can import the database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from faker import Faker
    from database.supabase_config import get_supabase_client
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you have the required dependencies installed:")
    print("   pip install faker supabase")
    sys.exit(1)

class ProfileCreator:
    """Creates basic user profiles"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.fake = Faker()
        self.fake.seed_instance(42)  # For reproducible results
        
        # Initialize Supabase client
        try:
            self.supabase = get_supabase_client()
            print("✅ Supabase client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Supabase client: {e}")
            print("💡 Make sure your environment variables are set correctly")
            sys.exit(1)
        
        # Track created profiles
        self.created_profiles = []
    
    def generate_profile(self) -> Dict[str, Any]:
        """Generate a realistic user profile"""
        profile = {
            "id": str(uuid.uuid4()),
            "email": self.fake.email(),
            "first_name": self.fake.first_name(),
            "last_name": self.fake.last_name(),
            "email_verified": True,  # Required field
            "account_status": "active",  # Required field
            "created_at": self.fake.date_time_between(start_date='-365d', end_date='now').isoformat(),
            "updated_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
        }
        
        return profile
    
    def insert_profile(self, profile: Dict[str, Any]) -> bool:
        """Insert a profile into the database"""
        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would create profile: {profile['first_name']} {profile['last_name']} ({profile['email']})")
                return True
            
            # Insert into profiles table
            result = self.supabase.table("profiles").insert(profile).execute()
            
            if result.data:
                print(f"  ✅ Created profile: {profile['first_name']} {profile['last_name']} ({profile['email']})")
                return True
            else:
                print(f"  ❌ Failed to create profile: {profile['first_name']} {profile['last_name']}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error creating profile: {e}")
            return False
    
    def create_profiles(self, count: int = 5) -> List[Dict[str, Any]]:
        """Create the specified number of profiles"""
        print(f"👥 Creating {count} user profiles...")
        print("=" * 50)
        
        created_count = 0
        
        for i in range(count):
            profile = self.generate_profile()
            
            if self.insert_profile(profile):
                self.created_profiles.append(profile)
                created_count += 1
        
        print(f"\n✅ Successfully created {created_count}/{count} profiles!")
        
        if not self.dry_run and self.created_profiles:
            print("\n📋 Created Profile IDs:")
            for i, profile in enumerate(self.created_profiles, 1):
                print(f"  {i}. {profile['id']} - {profile['first_name']} {profile['last_name']} ({profile['email']})")
        
        return self.created_profiles
    
    def save_profile_ids(self) -> None:
        """Save profile IDs to a file for use in other scripts"""
        if not self.created_profiles:
            return
        
        import json
        
        profiles_file = "created_profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(self.created_profiles, f, indent=2, default=str)
        
        print(f"\n💾 Profile IDs saved to: {profiles_file}")
        print("💡 You can use these IDs in other scripts for foreign key relationships")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Create basic user profiles")
    parser.add_argument("--count", type=int, default=5, help="Number of profiles to create (default: 5)")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without creating profiles")
    
    args = parser.parse_args()
    
    print("🚀 Basic User Profile Creator")
    print("=" * 60)
    
    if args.dry_run:
        print("⚠️ DRY RUN MODE - No profiles will be created")
    
    # Create profile creator
    creator = ProfileCreator(dry_run=args.dry_run)
    
    # Create profiles
    profiles = creator.create_profiles(args.count)
    
    # Save profile IDs
    creator.save_profile_ids()


if __name__ == "__main__":
    main()
