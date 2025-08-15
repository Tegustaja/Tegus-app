#!/usr/bin/env python3
"""
Check Existing Database Data

This script checks what data already exists in your database
so we can use real IDs for foreign key relationships.

Usage:
    python3 scripts/check_existing_data.py
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import the database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database.supabase_config import get_supabase_client
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you have the required dependencies installed:")
    print("   pip install supabase")
    sys.exit(1)

def check_existing_data():
    """Check what data exists in the database"""
    print("🔍 Checking Existing Database Data...")
    print("=" * 60)
    
    try:
        supabase = get_supabase_client()
        
        # Check profiles table
        print("\n👥 Checking Profiles Table...")
        try:
            profiles_result = supabase.table("profiles").select("*", count="exact").limit(5).execute()
            if profiles_result.data:
                print(f"  ✅ Found {len(profiles_result.data)} profiles")
                print("  📋 Sample profile IDs:")
                for i, profile in enumerate(profiles_result.data[:3]):
                    print(f"    {i+1}. {profile.get('id', 'N/A')} - {profile.get('email', 'N/A')}")
            else:
                print("  ❌ No profiles found")
        except Exception as e:
            print(f"  ❌ Error checking profiles: {e}")
        
        # Check lessons table
        print("\n📚 Checking Lessons Table...")
        try:
            lessons_result = supabase.table("Lessons").select("*", count="exact").limit(5).execute()
            if lessons_result.data:
                print(f"  ✅ Found {len(lessons_result.data)} lessons")
                print("  📋 Sample lesson IDs:")
                for i, lesson in enumerate(lessons_result.data[:3]):
                    print(f"    {i+1}. {lesson.get('session_id', 'N/A')} - {lesson.get('title', 'N/A')}")
            else:
                print("  ❌ No lessons found")
        except Exception as e:
            print(f"  ❌ Error checking lessons: {e}")
        
        # Check lesson_parts table
        print("\n🔧 Checking Lesson Parts Table...")
        try:
            parts_result = supabase.table("lesson_parts").select("*", count="exact").limit(5).execute()
            if parts_result.data:
                print(f"  ✅ Found {len(parts_result.data)} lesson parts")
                print("  📋 Sample lesson part IDs:")
                for i, part in enumerate(parts_result.data[:3]):
                    print(f"    {i+1}. {part.get('id', 'N/A')} - {part.get('title', 'N/A')}")
            else:
                print("  ❌ No lesson parts found")
        except Exception as e:
            print(f"  ❌ Error checking lesson parts: {e}")
        
        # Check exercises table
        print("\n🏋️ Checking Exercises Table...")
        try:
            exercises_result = supabase.table("exercises").select("*", count="exact").limit(5).execute()
            if exercises_result.data:
                print(f"  ✅ Found {len(exercises_result.data)} exercises")
                print("  📋 Sample exercise IDs:")
                for i, exercise in enumerate(exercises_result.data[:3]):
                    print(f"    {i+1}. {exercise.get('id', 'N/A')} - {exercise.get('title', 'N/A')}")
            else:
                print("  ❌ No exercises found")
        except Exception as e:
            print(f"  ❌ Error checking exercises: {e}")
        
        # Check subtasks table
        print("\n🔧 Checking Subtasks Table...")
        try:
            subtasks_result = supabase.table("subtasks").select("*", count="exact").limit(5).execute()
            if subtasks_result.data:
                print(f"  ✅ Found {len(subtasks_result.data)} subtasks")
                print("  📋 Sample subtask IDs:")
                for i, subtask in enumerate(subtasks_result.data[:3]):
                    print(f"    {i+1}. {subtask.get('id', 'N/A')} - {subtask.get('title', 'N/A')}")
            else:
                print("  ❌ No subtasks found")
        except Exception as e:
            print(f"  ❌ Error checking subtasks: {e}")
        
        # Check progress tables
        print("\n📊 Checking Progress Tables...")
        try:
            # Lesson part progress
            lpp_result = supabase.table("lesson_part_progress").select("*", count="exact").limit(3).execute()
            print(f"  ✅ Lesson Part Progress: {len(lpp_result.data) if lpp_result.data else 0} records")
            
            # Exercise progress
            ep_result = supabase.table("exercise_progress").select("*", count="exact").limit(3).execute()
            print(f"  ✅ Exercise Progress: {len(ep_result.data) if ep_result.data else 0} records")
            
            # Subtask progress
            sp_result = supabase.table("subtask_progress").select("*", count="exact").limit(3).execute()
            print(f"  ✅ Subtask Progress: {len(sp_result.data) if sp_result.data else 0} records")
            
        except Exception as e:
            print(f"  ❌ Error checking progress tables: {e}")
        
        # Check extensions table
        print("\n🔗 Checking Extensions Table...")
        try:
            extensions_result = supabase.table("lesson_extensions").select("*", count="exact").limit(5).execute()
            if extensions_result.data:
                print(f"  ✅ Found {len(extensions_result.data)} extensions")
            else:
                print("  ❌ No extensions found")
        except Exception as e:
            print(f"  ❌ Error checking extensions: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Database check completed!")
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")

def main():
    """Main function"""
    print("🚀 Database Data Checker")
    print("=" * 60)
    
    check_existing_data()

if __name__ == "__main__":
    main()
