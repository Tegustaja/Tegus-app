#!/usr/bin/env python3
"""
Upload Generated Fake Data to Supabase Database

This script takes the generated fake data and uploads it to the Supabase database
using the personalized learning API endpoints.

Usage:
    python3 scripts/upload_fake_data_to_supabase.py [--api-url URL] [--dry-run]
"""

import json
import os
import sys
import time
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the parent directory to the path so we can import the database models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FakeDataUploader:
    """Uploads generated fake data to Supabase database"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000", dry_run: bool = False):
        self.api_base_url = api_base_url.rstrip('/')
        self.dry_run = dry_run
        self.upload_results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        
        # API endpoints
        self.endpoints = {
            'lesson_parts': f"{self.api_base_url}/lesson-parts/",
            'exercises': f"{self.api_base_url}/personalized-exercises/",
            'subtasks': f"{self.api_base_url}/subtasks/",
            'progress': f"{self.api_base_url}/personalized-progress/",
            'extensions': f"{self.api_base_url}/lesson-extensions/"
        }
    
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
    
    def test_api_connection(self) -> bool:
        """Test if the API is accessible"""
        try:
            response = requests.get(f"{self.api_base_url}/docs", timeout=10)
            if response.status_code == 200:
                print(f"✅ API connection successful: {self.api_base_url}")
                return True
            else:
                print(f"⚠️ API responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ API connection failed: {e}")
            return False
    
    def upload_lesson_parts(self, lesson_parts: List[Dict[str, Any]]) -> None:
        """Upload lesson parts to the database"""
        print(f"\n📚 Uploading {len(lesson_parts)} lesson parts...")
        
        for i, part in enumerate(lesson_parts, 1):
            try:
                # Prepare data for API (remove internal fields)
                upload_data = {
                    "lesson_id": part["lesson_id"],
                    "title": part["title"],
                    "description": part["description"],
                    "part_order": part["part_order"],
                    "is_completed": part["is_completed"]
                }
                
                if part.get("completed_at"):
                    upload_data["completed_at"] = part["completed_at"]
                
                if self.dry_run:
                    print(f"  [DRY RUN] Would upload lesson part {i}: {part['title']}")
                    self.upload_results['skipped'].append(f"lesson_part_{i}")
                else:
                    response = requests.post(
                        self.endpoints['lesson_parts'],
                        json=upload_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"  ✅ Uploaded lesson part {i}: {part['title']} (ID: {result.get('id', 'N/A')})")
                        self.upload_results['success'].append(f"lesson_part_{i}")
                        
                        # Update the part with the new ID from the database
                        part['uploaded_id'] = result.get('id')
                    else:
                        print(f"  ❌ Failed to upload lesson part {i}: {part['title']} - {response.status_code}")
                        print(f"     Error: {response.text}")
                        self.upload_results['failed'].append(f"lesson_part_{i}")
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ Error uploading lesson part {i}: {e}")
                self.upload_results['failed'].append(f"lesson_part_{i}")
    
    def upload_exercises(self, exercises: List[Dict[str, Any]]) -> None:
        """Upload exercises to the database"""
        print(f"\n🏋️ Uploading {len(exercises)} exercises...")
        
        for i, exercise in enumerate(exercises, 1):
            try:
                # Prepare data for API
                upload_data = {
                    "lesson_part_id": exercise["lesson_part_id"],
                    "exercise_type": exercise["exercise_type"],
                    "title": exercise["title"],
                    "content": exercise["content"],
                    "instructions": exercise["instructions"],
                    "correct_answer": exercise.get("correct_answer"),
                    "explanation": exercise.get("explanation"),
                    "difficulty_level": exercise["difficulty_level"],
                    "exercise_order": exercise["exercise_order"],
                    "is_completed": exercise["is_completed"]
                }
                
                if exercise.get("completed_at"):
                    upload_data["completed_at"] = exercise["completed_at"]
                
                if self.dry_run:
                    print(f"  [DRY RUN] Would upload exercise {i}: {exercise['title']}")
                    self.upload_results['skipped'].append(f"exercise_{i}")
                else:
                    response = requests.post(
                        self.endpoints['exercises'],
                        json=upload_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"  ✅ Uploaded exercise {i}: {exercise['title']} (ID: {result.get('id', 'N/A')})")
                        self.upload_results['success'].append(f"exercise_{i}")
                        
                        # Update the exercise with the new ID from the database
                        exercise['uploaded_id'] = result.get('id')
                    else:
                        print(f"  ❌ Failed to upload exercise {i}: {exercise['title']} - {response.status_code}")
                        print(f"     Error: {response.text}")
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
                # Prepare data for API
                upload_data = {
                    "exercise_id": subtask["exercise_id"],
                    "title": subtask["title"],
                    "content": subtask["content"],
                    "subtask_type": subtask["subtask_type"],
                    "subtask_order": subtask["subtask_order"],
                    "is_optional": subtask["is_optional"],
                    "is_completed": subtask["is_completed"]
                }
                
                if subtask.get("completed_at"):
                    upload_data["completed_at"] = subtask["completed_at"]
                
                if self.dry_run:
                    print(f"  [DRY RUN] Would upload subtask {i}: {subtask['title']}")
                    self.upload_results['skipped'].append(f"subtask_{i}")
                else:
                    response = requests.post(
                        self.endpoints['subtasks'],
                        json=upload_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"  ✅ Uploaded subtask {i}: {subtask['title']} (ID: {result.get('id', 'N/A')})")
                        self.upload_results['success'].append(f"subtask_{i}")
                        
                        # Update the subtask with the new ID from the database
                        subtask['uploaded_id'] = result.get('id')
                    else:
                        print(f"  ❌ Failed to upload subtask {i}: {subtask['title']} - {response.status_code}")
                        print(f"     Error: {response.text}")
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
                    endpoint = f"{self.endpoints['progress']}lesson-part"
                    upload_data = {
                        "lesson_part_id": progress["lesson_part_id"],
                        "user_id": progress["user_id"],
                        "status": progress["status"],
                        "progress_percentage": progress["progress_percentage"],
                        "time_spent_minutes": progress["time_spent_minutes"]
                    }
                    
                    if progress.get("started_at"):
                        upload_data["started_at"] = progress["started_at"]
                    if progress.get("completed_at"):
                        upload_data["completed_at"] = progress["completed_at"]
                    
                    progress_type = "lesson_part"
                    
                elif "exercise_id" in progress:
                    endpoint = f"{self.endpoints['progress']}exercise"
                    upload_data = {
                        "exercise_id": progress["exercise_id"],
                        "user_id": progress["user_id"],
                        "status": progress["status"],
                        "attempts": progress["attempts"],
                        "correct_attempts": progress["correct_attempts"],
                        "time_spent_minutes": progress["time_spent_minutes"],
                        "user_answer": progress.get("user_answer"),
                        "is_correct": progress["is_correct"],
                        "feedback_received": progress["feedback_received"]
                    }
                    
                    if progress.get("started_at"):
                        upload_data["started_at"] = progress["started_at"]
                    if progress.get("completed_at"):
                        upload_data["completed_at"] = progress["completed_at"]
                    
                    progress_type = "exercise"
                    
                elif "subtask_id" in progress:
                    endpoint = f"{self.endpoints['progress']}subtask"
                    upload_data = {
                        "subtask_id": progress["subtask_id"],
                        "user_id": progress["user_id"],
                        "status": progress["status"],
                        "time_spent_minutes": progress["time_spent_minutes"]
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
                    response = requests.post(
                        endpoint,
                        json=upload_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"  ✅ Uploaded {progress_type} progress {i} (ID: {result.get('id', 'N/A')})")
                        self.upload_results['success'].append(f"progress_{i}")
                    else:
                        print(f"  ❌ Failed to upload {progress_type} progress {i} - {response.status_code}")
                        print(f"     Error: {response.text}")
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
                # Prepare data for API
                upload_data = {
                    "lesson_id": extension["lesson_id"],
                    "user_id": extension["user_id"],
                    "extension_type": extension["extension_type"],
                    "parent_id": extension.get("parent_id"),
                    "extension_reason": extension["extension_reason"]
                }
                
                if self.dry_run:
                    print(f"  [DRY RUN] Would upload extension {i}: {extension['extension_type']}")
                    self.upload_results['skipped'].append(f"extension_{i}")
                else:
                    response = requests.post(
                        self.endpoints['extensions'],
                        json=upload_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"  ✅ Uploaded extension {i}: {extension['extension_type']} (ID: {result.get('id', 'N/A')})")
                        self.upload_results['success'].append(f"extension_{i}")
                    else:
                        print(f"  ❌ Failed to upload extension {i}: {extension['extension_type']} - {response.status_code}")
                        print(f"     Error: {response.text}")
                        self.upload_results['failed'].append(f"extension_{i}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ Error uploading extension {i}: {e}")
                self.upload_results['failed'].append(f"extension_{i}")
    
    def save_upload_results(self, data: Dict[str, Any]) -> None:
        """Save upload results and updated data to files"""
        results_dir = Path("upload_results")
        results_dir.mkdir(exist_ok=True)
        
        # Save upload results
        results_file = results_dir / "upload_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.upload_results, f, indent=2, default=str)
        
        # Save updated data with new IDs
        updated_data_dir = results_dir / "updated_data"
        updated_data_dir.mkdir(exist_ok=True)
        
        for key, value in data.items():
            if key != 'summary' and isinstance(value, list):
                filename = updated_data_dir / f"{key}.json"
                with open(filename, 'w') as f:
                    json.dump(value, f, indent=2, default=str)
        
        print(f"\n💾 Upload results saved to: {results_file}")
        print(f"💾 Updated data saved to: {updated_data_dir}")
    
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
        print("🚀 Starting data upload to Supabase...")
        print(f"🌐 API Base URL: {self.api_base_url}")
        
        if self.dry_run:
            print("⚠️ DRY RUN MODE - No data will be actually uploaded")
        
        # Test API connection first
        if not self.test_api_connection():
            print("❌ Cannot proceed without API connection")
            return
        
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
    parser = argparse.ArgumentParser(description="Upload generated fake data to Supabase database")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000", 
                       help="Base URL for the API (default: http://localhost:8000)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Perform a dry run without actually uploading data")
    
    args = parser.parse_args()
    
    print("🚀 Fake Data Uploader for Personalized Learning API")
    print("=" * 70)
    
    # Create uploader
    uploader = FakeDataUploader(
        api_base_url=args.api_url,
        dry_run=args.dry_run
    )
    
    # Load fake data
    data = uploader.load_fake_data()
    
    if not data:
        return
    
    # Upload all data
    uploader.upload_all_data(data)


if __name__ == "__main__":
    main()
