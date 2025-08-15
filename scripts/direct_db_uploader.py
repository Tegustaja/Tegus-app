#!/usr/bin/env python3
"""
Direct Database Uploader for Personalized Learning Fake Data

This script uploads generated fake data directly to the Supabase database
using the database models and Supabase client.

Usage:
    python3 scripts/direct_db_uploader.py [--dry-run]
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the parent directory to the path so we can import the database models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from supabase import create_client, Client
    from database.models import LessonPart, Exercise, Subtask, LessonPartProgress, ExerciseProgress, SubtaskProgress, LessonExtension
    from database.supabase_config import get_supabase_client
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you have the required dependencies installed:")
    print("   pip install supabase")
    sys.exit(1)

class DirectDatabaseUploader:
    """Uploads generated fake data directly to the database"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.upload_results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        
        # Initialize Supabase client
        try:
            self.supabase = get_supabase_client()
            print("✅ Supabase client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Supabase client: {e}")
            print("💡 Make sure your environment variables are set correctly")
            sys.exit(1)
    
    def load_fake_data(self) -> Optional[Dict[str, Any]]:
        """Load the generated fake data"""
        fake_data_dir = Path("fake_data")
        
        if not fake_data_dir.exists():
            print("❌ Fake data directory not found. Please run the fake data generator first:")
            print("   python3 scripts/simple_fake_data_generator.py")
            return None
        
        data = {}
        
        # Load summary first
        summary_file = fake_data_dir / "summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                data['summary'] = json.load(f)
        
        # Load all data files
        data_files = [
            'lesson_parts.json',
            'exercises.json', 
            'subtasks.json',
            'progress_records.json',
            'extensions.json'
        ]
        
        for filename in data_files:
            file_path = fake_data_dir / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data[filename.replace('.json', '')] = json.load(f)
        
        return data
    
    def upload_lesson_parts(self, lesson_parts: List[Dict[str, Any]]) -> None:
        """Upload lesson parts to the database"""
        print(f"\n📚 Uploading {len(lesson_parts)} lesson parts...")
        
        for i, part in enumerate(lesson_parts, 1):
            try:
                # Prepare data for database
                upload_data = {
                    "id": part["id"],
                    "lesson_id": part["lesson_id"],
                    "title": part["title"],
                    "description": part["description"],
                    "part_order": part["part_order"],
                    "is_completed": part["is_completed"],
                    "created_at": part["created_at"],
                    "updated_at": part["updated_at"]
                }
                
                if part.get("completed_at"):
                    upload_data["completed_at"] = part["completed_at"]
                
                if self.dry_run:
                    print(f"  [DRY RUN] Would upload lesson part {i}: {part['title']}")
                    self.upload_results['skipped'].append(f"lesson_part_{i}")
                else:
                    # Insert into database
                    result = self.supabase.table("lesson_parts").insert(upload_data).execute()
                    
                    if result.data:
                        print(f"  ✅ Uploaded lesson part {i}: {part['title']} (ID: {part['id']})")
                        self.upload_results['success'].append(f"lesson_part_{i}")
                    else:
                        print(f"  ❌ Failed to upload lesson part {i}: {part['title']}")
                        self.upload_results['failed'].append(f"lesson_part_{i}")
                
                # Small delay to avoid overwhelming the database
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ Error uploading lesson part {i}: {e}")
                self.upload_results['failed'].append(f"lesson_part_{i}")
    
    def upload_exercises(self, exercises: List[Dict[str, Any]]) -> None:
        """Upload exercises to the database"""
        print(f"\n🏋️ Uploading {len(exercises)} exercises...")
        
        for i, exercise in enumerate(exercises, 1):
            try:
                # Prepare data for database
                upload_data = {
                    "id": exercise["id"],
                    "lesson_part_id": exercise["lesson_part_id"],
                    "exercise_type": exercise["exercise_type"],
                    "title": exercise["title"],
                    "content": exercise["content"],
                    "instructions": exercise["instructions"],
                    "correct_answer": exercise.get("correct_answer"),
                    "explanation": exercise.get("explanation"),
                    "difficulty_level": exercise["difficulty_level"],
                    "exercise_order": exercise["exercise_order"],
                    "is_completed": exercise["is_completed"],
                    "created_at": exercise["created_at"],
                    "updated_at": exercise["updated_at"]
                }
                
                if exercise.get("completed_at"):
                    upload_data["completed_at"] = exercise["completed_at"]
                
                if self.dry_run:
                    print(f"  [DRY RUN] Would upload exercise {i}: {exercise['title']}")
                    self.upload_results['skipped'].append(f"exercise_{i}")
                else:
                    # Insert into database
                    result = self.supabase.table("exercises").insert(upload_data).execute()
                    
                    if result.data:
                        print(f"  ✅ Uploaded exercise {i}: {exercise['title']} (ID: {exercise['id']})")
                        self.upload_results['success'].append(f"exercise_{i}")
                    else:
                        print(f"  ❌ Failed to upload exercise {i}: {exercise['title']}")
                        self.upload_results['failed'].append(f"exercise_{i}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ Error uploading exercise {i}: {e}")
                self.upload_results['failed'].append(f"exercise_{i}")
    
    def upload_subtasks(self, subtasks: List[Dict[str, Any]]) -> None:
        """Upload subtasks to the database"""
        print(f"\n🔧 Uploading {len(subtasks)} subtasks...")
        
        for i, subtask in enumerate(subtasks, 1):
            try:
                # Prepare data for database
                upload_data = {
                    "id": subtask["id"],
                    "exercise_id": subtask["exercise_id"],
                    "title": subtask["title"],
                    "content": subtask["content"],
                    "subtask_type": subtask["subtask_type"],
                    "subtask_order": subtask["subtask_order"],
                    "is_optional": subtask["is_optional"],
                    "is_completed": subtask["is_completed"],
                    "created_at": subtask["created_at"],
                    "updated_at": subtask["updated_at"]
                }
                
                if subtask.get("completed_at"):
                    upload_data["completed_at"] = subtask["completed_at"]
                
                if self.dry_run:
                    print(f"  [DRY RUN] Would upload subtask {i}: {subtask['title']}")
                    self.upload_results['skipped'].append(f"subtask_{i}")
                else:
                    # Insert into database
                    result = self.supabase.table("subtasks").insert(upload_data).execute()
                    
                    if result.data:
                        print(f"  ✅ Uploaded subtask {i}: {subtask['title']} (ID: {subtask['id']})")
                        self.upload_results['success'].append(f"subtask_{i}")
                    else:
                        print(f"  ❌ Failed to upload subtask {i}: {subtask['title']}")
                        self.upload_results['failed'].append(f"subtask_{i}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ Error uploading subtask {i}: {e}")
                self.upload_results['failed'].append(f"subtask_{i}")
    
    def upload_progress_records(self, progress_records: List[Dict[str, Any]]) -> None:
        """Upload progress records to the database"""
        print(f"\n📊 Uploading {len(progress_records)} progress records...")
        
        for i, progress in enumerate(progress_records, 1):
            try:
                # Determine progress type and prepare data
                if "lesson_part_id" in progress:
                    table_name = "lesson_part_progress"
                    upload_data = {
                        "id": progress["id"],
                        "lesson_part_id": progress["lesson_part_id"],
                        "user_id": progress["user_id"],
                        "status": progress["status"],
                        "progress_percentage": progress["progress_percentage"],
                        "time_spent_minutes": progress["time_spent_minutes"],
                        "created_at": progress["created_at"],
                        "updated_at": progress["updated_at"]
                    }
                    
                    if progress.get("started_at"):
                        upload_data["started_at"] = progress["started_at"]
                    if progress.get("completed_at"):
                        upload_data["completed_at"] = progress["completed_at"]
                    
                    progress_type = "lesson_part"
                    
                elif "exercise_id" in progress:
                    table_name = "exercise_progress"
                    upload_data = {
                        "id": progress["id"],
                        "exercise_id": progress["exercise_id"],
                        "user_id": progress["user_id"],
                        "status": progress["status"],
                        "attempts": progress["attempts"],
                        "correct_attempts": progress["correct_attempts"],
                        "time_spent_minutes": progress["time_spent_minutes"],
                        "user_answer": progress.get("user_answer"),
                        "is_correct": progress["is_correct"],
                        "feedback_received": progress["feedback_received"],
                        "created_at": progress["created_at"],
                        "updated_at": progress["updated_at"]
                    }
                    
                    if progress.get("started_at"):
                        upload_data["started_at"] = progress["started_at"]
                    if progress.get("completed_at"):
                        upload_data["completed_at"] = progress["completed_at"]
                    
                    progress_type = "exercise"
                    
                elif "subtask_id" in progress:
                    table_name = "subtask_progress"
                    upload_data = {
                        "id": progress["id"],
                        "subtask_id": progress["subtask_id"],
                        "user_id": progress["user_id"],
                        "status": progress["status"],
                        "time_spent_minutes": progress["time_spent_minutes"],
                        "created_at": progress["created_at"],
                        "updated_at": progress["updated_at"]
                    }
                    
                    if progress.get("started_at"):
                        upload_data["started_at"] = progress["started_at"]
                    if progress.get("completed_at"):
                        upload_data["completed_at"] = progress["completed_at"]
                    
                    progress_type = "subtask"
                else:
                    print(f"  ⚠️ Skipping progress record {i}: unknown type")
                    self.upload_results['skipped'].append(f"progress_{i}")
                    continue
                
                if self.dry_run:
                    print(f"  [DRY RUN] Would upload {progress_type} progress {i}")
                    self.upload_results['skipped'].append(f"progress_{i}")
                else:
                    # Insert into database
                    result = self.supabase.table(table_name).insert(upload_data).execute()
                    
                    if result.data:
                        print(f"  ✅ Uploaded {progress_type} progress {i} (ID: {progress['id']})")
                        self.upload_results['success'].append(f"progress_{i}")
                    else:
                        print(f"  ❌ Failed to upload {progress_type} progress {i}")
                        self.upload_results['failed'].append(f"progress_{i}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ Error uploading progress record {i}: {e}")
                self.upload_results['failed'].append(f"progress_{i}")
    
    def upload_extensions(self, extensions: List[Dict[str, Any]]) -> None:
        """Upload lesson extensions to the database"""
        print(f"\n🔗 Uploading {len(extensions)} lesson extensions...")
        
        for i, extension in enumerate(extensions, 1):
            try:
                # Prepare data for database
                upload_data = {
                    "id": extension["id"],
                    "lesson_id": extension["lesson_id"],
                    "user_id": extension["user_id"],
                    "extension_type": extension["extension_type"],
                    "parent_id": extension.get("parent_id"),
                    "extension_reason": extension["extension_reason"],
                    "created_at": extension["created_at"]
                }
                
                if self.dry_run:
                    print(f"  [DRY RUN] Would upload extension {i}: {extension['extension_type']}")
                    self.upload_results['skipped'].append(f"extension_{i}")
                else:
                    # Insert into database
                    result = self.supabase.table("lesson_extensions").insert(upload_data).execute()
                    
                    if result.data:
                        print(f"  ✅ Uploaded extension {i}: {extension['extension_type']} (ID: {extension['id']})")
                        self.upload_results['success'].append(f"extension_{i}")
                    else:
                        print(f"  ❌ Failed to upload extension {i}: {extension['extension_type']}")
                        self.upload_results['failed'].append(f"extension_{i}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ Error uploading extension {i}: {e}")
                self.upload_results['failed'].append(f"extension_{i}")
    
    def save_upload_results(self, data: Dict[str, Any]) -> None:
        """Save upload results to files"""
        results_dir = Path("upload_results")
        results_dir.mkdir(exist_ok=True)
        
        # Save upload results
        results_file = results_dir / "direct_upload_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.upload_results, f, indent=2, default=str)
        
        print(f"\n💾 Upload results saved to: {results_file}")
    
    def print_upload_summary(self) -> None:
        """Print a summary of the upload results"""
        print("\n📊 Upload Summary")
        print("=" * 50)
        
        total_success = len(self.upload_results['success'])
        total_failed = len(self.upload_results['failed'])
        total_skipped = len(self.upload_results['skipped'])
        total = total_success + total_failed + total_skipped
        
        print(f"✅ Successful: {total_success}")
        print(f"❌ Failed: {total_failed}")
        print(f"⏭️ Skipped: {total_skipped}")
        print(f"📊 Total: {total}")
        
        if total_failed > 0:
            print(f"\n❌ Failed uploads:")
            for failed in self.upload_results['failed'][:10]:  # Show first 10
                print(f"  • {failed}")
            if total_failed > 10:
                print(f"  ... and {total_failed - 10} more")
        
        if self.dry_run:
            print(f"\n⚠️ This was a DRY RUN - no data was actually uploaded")
        else:
            print(f"\n🎉 Upload completed!")
    
    def upload_all_data(self, data: Dict[str, Any]) -> None:
        """Upload all data to the database"""
        print("🚀 Starting direct database upload...")
        
        if self.dry_run:
            print("⚠️ DRY RUN MODE - No data will be actually uploaded")
        
        # Upload data in dependency order
        if 'lesson_parts' in data:
            self.upload_lesson_parts(data['lesson_parts'])
        
        if 'exercises' in data:
            self.upload_exercises(data['exercises'])
        
        if 'subtasks' in data:
            self.upload_subtasks(data['subtasks'])
        
        if 'progress_records' in data:
            self.upload_progress_records(data['progress_records'])
        
        if 'extensions' in data:
            self.upload_extensions(data['extensions'])
        
        # Save results
        self.save_upload_results(data)
        
        # Print summary
        self.print_upload_summary()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Upload generated fake data directly to Supabase database")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Perform a dry run without actually uploading data")
    
    args = parser.parse_args()
    
    print("🚀 Direct Database Uploader for Personalized Learning")
    print("=" * 70)
    
    # Create uploader
    uploader = DirectDatabaseUploader(dry_run=args.dry_run)
    
    # Load fake data
    data = uploader.load_fake_data()
    
    if not data:
        return
    
    # Upload all data
    uploader.upload_all_data(data)


if __name__ == "__main__":
    main()
