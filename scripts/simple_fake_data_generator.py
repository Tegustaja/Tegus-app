#!/usr/bin/env python3
"""
Simple Fake Data Generator for Personalized Learning API Testing

This script generates basic fake data for testing the API endpoints.
It creates realistic but simple data structures that can be used
to test the personalized learning system.

Usage:
    python3 scripts/simple_fake_data_generator.py
"""

import json
import uuid
import random
from datetime import datetime, timedelta

def generate_simple_fake_data():
    """Generate simple fake data for API testing"""
    
    # Generate user IDs
    user_ids = [str(uuid.uuid4()) for _ in range(3)]
    
    # Generate lesson IDs
    lesson_ids = [str(uuid.uuid4()) for _ in range(2)]
    
    # Generate lesson parts
    lesson_parts = []
    for i, lesson_id in enumerate(lesson_ids):
        for j in range(3):  # 3 parts per lesson
            part = {
                "id": str(uuid.uuid4()),
                "lesson_id": lesson_id,
                "title": f"Part {j+1}: {random.choice(['Introduction', 'Core Concepts', 'Practice', 'Review'])}",
                "description": f"This is part {j+1} of lesson {i+1}",
                "part_order": j + 1,
                "is_completed": random.choice([True, False]),
                "completed_at": datetime.utcnow().isoformat() if random.choice([True, False]) else None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            lesson_parts.append(part)
    
    # Generate exercises
    exercises = []
    for part in lesson_parts:
        for k in range(2):  # 2 exercises per part
            exercise = {
                "id": str(uuid.uuid4()),
                "lesson_part_id": part["id"],
                "exercise_type": random.choice(["multiple_choice", "true_false", "calculation"]),
                "title": f"Exercise {k+1}: {random.choice(['Basic Question', 'Practice Problem', 'Review Question'])}",
                "content": f"This is exercise {k+1} content for {part['title']}",
                "instructions": "Please answer the question below",
                "correct_answer": "Sample correct answer",
                "explanation": "This is the explanation for the correct answer",
                "difficulty_level": random.choice(["easy", "medium", "hard"]),
                "exercise_order": k + 1,
                "is_completed": random.choice([True, False]),
                "completed_at": datetime.utcnow().isoformat() if random.choice([True, False]) else None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            exercises.append(exercise)
    
    # Generate subtasks
    subtasks = []
    for exercise in exercises:
        if random.random() < 0.5:  # 50% chance of having subtasks
            subtask = {
                "id": str(uuid.uuid4()),
                "exercise_id": exercise["id"],
                "title": f"Additional {random.choice(['Explanation', 'Practice', 'Example'])}",
                "content": f"This is a subtask for {exercise['title']}",
                "subtask_type": random.choice(["explanation", "practice", "reinforcement"]),
                "subtask_order": 1,
                "is_optional": random.choice([True, False]),
                "is_completed": random.choice([True, False]),
                "completed_at": datetime.utcnow().isoformat() if random.choice([True, False]) else None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            subtasks.append(subtask)
    
    # Generate progress data
    progress_records = []
    
    # Lesson part progress
    for part in lesson_parts:
        for user_id in user_ids:
            progress = {
                "id": str(uuid.uuid4()),
                "lesson_part_id": part["id"],
                "user_id": user_id,
                "status": random.choice(["not_started", "in_progress", "completed"]),
                "progress_percentage": random.randint(0, 100),
                "time_spent_minutes": random.randint(0, 60),
                "started_at": datetime.utcnow().isoformat() if random.random() < 0.7 else None,
                "completed_at": datetime.utcnow().isoformat() if random.random() < 0.3 else None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            progress_records.append(progress)
    
    # Exercise progress
    for exercise in exercises:
        for user_id in user_ids:
            progress = {
                "id": str(uuid.uuid4()),
                "exercise_id": exercise["id"],
                "user_id": user_id,
                "status": random.choice(["not_started", "in_progress", "completed", "failed"]),
                "attempts": random.randint(0, 3),
                "correct_attempts": random.randint(0, 2),
                "time_spent_minutes": random.randint(0, 30),
                "user_answer": f"User answer for {exercise['title']}",
                "is_correct": random.choice([True, False]),
                "feedback_received": random.choice([True, False]),
                "started_at": datetime.utcnow().isoformat() if random.random() < 0.7 else None,
                "completed_at": datetime.utcnow().isoformat() if random.random() < 0.3 else None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            progress_records.append(progress)
    
    # Subtask progress
    for subtask in subtasks:
        for user_id in user_ids:
            if random.random() < 0.6:  # 60% chance of having progress
                progress = {
                    "id": str(uuid.uuid4()),
                    "subtask_id": subtask["id"],
                    "user_id": user_id,
                    "status": random.choice(["not_started", "in_progress", "completed"]),
                    "time_spent_minutes": random.randint(0, 20),
                    "started_at": datetime.utcnow().isoformat() if random.random() < 0.7 else None,
                    "completed_at": datetime.utcnow().isoformat() if random.random() < 0.3 else None,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                progress_records.append(progress)
    
    # Generate extensions
    extensions = []
    for lesson_id in lesson_ids:
        if random.random() < 0.4:  # 40% chance of having extensions
            extension = {
                "id": str(uuid.uuid4()),
                "lesson_id": lesson_id,
                "user_id": random.choice(user_ids),
                "extension_type": random.choice(["lesson_part", "exercise", "subtask"]),
                "parent_id": None,
                "extension_reason": random.choice([
                    "Student needs more practice",
                    "Additional explanation required",
                    "Request for more challenging content"
                ]),
                "created_at": datetime.utcnow().isoformat()
            }
            extensions.append(extension)
    
    return {
        "users": user_ids,
        "lessons": lesson_ids,
        "lesson_parts": lesson_parts,
        "exercises": exercises,
        "subtasks": subtasks,
        "progress_records": progress_records,
        "extensions": extensions
    }

def save_fake_data(data, output_dir="fake_data"):
    """Save fake data to JSON files"""
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save individual files
    for key, value in data.items():
        if key not in ["users", "lessons"]:  # Skip simple ID lists
            filename = os.path.join(output_dir, f"{key}.json")
            with open(filename, 'w') as f:
                json.dump(value, f, indent=2, default=str)
            print(f"💾 Saved {key} to {filename}")
    
    # Save summary
    summary = {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "users": len(data["users"]),
            "lessons": len(data["lessons"]),
            "lesson_parts": len(data["lesson_parts"]),
            "exercises": len(data["exercises"]),
            "subtasks": len(data["subtasks"]),
            "progress_records": len(data["progress_records"]),
            "extensions": len(data["extensions"])
        },
        "user_ids": data["users"],
        "lesson_ids": data["lessons"]
    }
    
    summary_file = os.path.join(output_dir, "summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"💾 Saved summary to {summary_file}")

def print_sample_data(data):
    """Print sample data for verification"""
    print("\n📊 Generated Data Summary:")
    print("=" * 50)
    
    summary = {
        "users": len(data["users"]),
        "lessons": len(data["lessons"]),
        "lesson_parts": len(data["lesson_parts"]),
        "exercises": len(data["exercises"]),
        "subtasks": len(data["subtasks"]),
        "progress_records": len(data["progress_records"]),
        "extensions": len(data["extensions"])
    }
    
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("\n🔍 Sample Data Preview:")
    print("=" * 50)
    
    if data["lesson_parts"]:
        part = data["lesson_parts"][0]
        print(f"Sample Lesson Part: {part['title']}")
        print(f"  Description: {part['description']}")
        print(f"  Order: {part['part_order']}")
        print(f"  Completed: {'Yes' if part['is_completed'] else 'No'}")
    
    if data["exercises"]:
        exercise = data["exercises"][0]
        print(f"\nSample Exercise: {exercise['title']}")
        print(f"  Type: {exercise['exercise_type']}")
        print(f"  Difficulty: {exercise['difficulty_level']}")
        print(f"  Content: {exercise['content'][:50]}...")
    
    if data["subtasks"]:
        subtask = data["subtasks"][0]
        print(f"\nSample Subtask: {subtask['title']}")
        print(f"  Type: {subtask['subtask_type']}")
        print(f"  Optional: {'Yes' if subtask['is_optional'] else 'No'}")

def main():
    """Main function"""
    print("🚀 Simple Personalized Learning Fake Data Generator")
    print("=" * 60)
    
    # Generate fake data
    data = generate_simple_fake_data()
    
    # Print summary
    print_sample_data(data)
    
    # Save to files
    save_fake_data(data)
    
    print(f"\n✨ Generated fake data successfully!")
    print("💡 Check the 'fake_data' directory for JSON files")
    print("💡 Use the summary.json file to get IDs for API testing")

if __name__ == "__main__":
    main()
