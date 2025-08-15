#!/usr/bin/env python3
"""
Faker-based Data Generator for Personalized Learning System

This script uses the faker library to generate realistic fake data
and inserts it directly into the Supabase database.

Usage:
    python3 scripts/faker_data_generator.py [--count N] [--dry-run]
"""

import sys
import os
import uuid
import random
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

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

class FakerDataGenerator:
    """Generates realistic fake data using faker library"""
    
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
        
        # Track generated data
        self.generated_data = {
            'lessons': [],
            'lesson_parts': [],
            'exercises': [],
            'subtasks': [],
            'progress_records': [],
            'extensions': []
        }
        
        # Get existing profile IDs for foreign key relationships
        self.profile_ids = self.get_existing_profile_ids()
        
        # Sample data for realistic content
        self.subjects = [
            "Physics", "Mathematics", "Chemistry", "Biology", "Computer Science",
            "History", "Literature", "Geography", "Economics", "Psychology",
            "Engineering", "Medicine", "Law", "Business", "Arts"
        ]
        
        self.topics = {
            "Physics": ["Mechanics", "Thermodynamics", "Electromagnetism", "Optics", "Quantum Physics", "Wave Motion", "Energy Conservation"],
            "Mathematics": ["Algebra", "Calculus", "Geometry", "Trigonometry", "Statistics", "Linear Algebra", "Number Theory"],
            "Chemistry": ["Atomic Structure", "Chemical Bonding", "Reactions", "Thermochemistry", "Organic Chemistry", "Biochemistry"],
            "Biology": ["Cell Biology", "Genetics", "Evolution", "Ecology", "Human Anatomy", "Microbiology", "Neuroscience"],
            "Computer Science": ["Programming", "Data Structures", "Algorithms", "Databases", "Networks", "AI/ML", "Software Engineering"]
        }
        
        self.exercise_types = ["multiple_choice", "true_false", "calculation", "explanation", "interactive"]
        self.difficulty_levels = ["easy", "medium", "hard"]
        self.subtask_types = ["explanation", "practice", "reinforcement", "extension"]
        self.progress_statuses = ["not_started", "in_progress", "completed", "failed"]
    
    def get_existing_profile_ids(self) -> List[str]:
        """Get existing profile IDs from the database"""
        try:
            result = self.supabase.table("profiles").select("id").execute()
            if result.data:
                profile_ids = [profile["id"] for profile in result.data]
                print(f"✅ Found {len(profile_ids)} existing profiles")
                return profile_ids
            else:
                print("⚠️ No existing profiles found")
                return []
        except Exception as e:
            print(f"❌ Error fetching profile IDs: {e}")
            return []
    
    def generate_lesson(self) -> Dict[str, Any]:
        """Generate a realistic lesson"""
        if not self.profile_ids:
            raise ValueError("No existing profiles found. Please create profiles first.")
            
        subject = random.choice(self.subjects)
        topic = random.choice(self.topics.get(subject, ["General Topic"]))
        
        lesson = {
            "session_id": str(uuid.uuid4()),
            "user_id": random.choice(self.profile_ids),  # Use existing profile ID
            "topic_id": str(uuid.uuid4()),
            "title": f"{subject}: {topic} - {self.fake.catch_phrase()}",
            "focus_area": random.choice([subject, f"{subject} Fundamentals", f"Advanced {subject}"]),
            "proficiency_level": random.choice(["beginner", "intermediate", "advanced"]),
            "steps": {},
            "step_statuses": {},
            "step_responses": {},
            "steps_feedback": {},
            "start_time": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            "last_active": self.fake.date_time_between(start_date='-7d', end_date='now').isoformat(),
            "is_completed": random.choice([True, False]),
            "completed_at": None,
            "current_database_index": random.randint(0, 5),
            "created_at": self.fake.date_time_between(start_date='-60d', end_date='now').isoformat()
        }
        
        if lesson["is_completed"]:
            lesson["completed_at"] = self.fake.date_time_between(start_date='-7d', end_date='now').isoformat()
        
        return lesson
    
    def generate_lesson_part(self, lesson_id: str, part_order: int) -> Dict[str, Any]:
        """Generate a realistic lesson part"""
        part_titles = [
            "Introduction and Overview",
            "Core Concepts and Theory",
            "Practical Applications",
            "Advanced Topics and Extensions",
            "Review and Practice",
            "Problem Solving Workshop",
            "Real-world Examples",
            "Hands-on Activities",
            "Assessment and Evaluation",
            "Summary and Next Steps"
        ]
        
        part = {
            "id": str(uuid.uuid4()),
            "lesson_id": lesson_id,
            "title": f"Part {part_order}: {random.choice(part_titles)}",
            "description": self.fake.paragraph(nb_sentences=3),
            "part_order": part_order,
            "is_completed": random.choice([True, False]),
            "completed_at": None,
            "created_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            "updated_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
        }
        
        if part["is_completed"]:
            part["completed_at"] = self.fake.date_time_between(start_date='-7d', end_date='now').isoformat()
        
        return part
    
    def generate_exercise(self, lesson_part_id: str, exercise_order: int) -> Dict[str, Any]:
        """Generate a realistic exercise"""
        exercise_type = random.choice(self.exercise_types)
        difficulty = random.choice(self.difficulty_levels)
        
        # Generate realistic content based on type
        if exercise_type == "multiple_choice":
            content = f"What is the primary function of {self.fake.word()} in {self.fake.word()}?"
            instructions = "Select the best answer from the options provided below."
            correct_answer = f"The correct answer involves understanding the {self.fake.word()} principles."
        elif exercise_type == "true_false":
            content = f"{self.fake.sentence()} - True or False?"
            instructions = "Determine whether the statement is true or false based on your understanding."
            correct_answer = "This statement is true because of the underlying principles."
        elif exercise_type == "calculation":
            content = f"Calculate the {self.fake.word()} for a {self.fake.word()} with parameters: {self.fake.word()} = {random.randint(1, 100)}"
            instructions = "Show all your work and use appropriate units. Round to 3 significant figures."
            correct_answer = f"The result is approximately {random.randint(10, 1000)} units."
        elif exercise_type == "explanation":
            content = f"Explain how {self.fake.word()} works in the context of {self.fake.word()}."
            instructions = "Provide a clear, concise explanation using your own words."
            correct_answer = "This concept works by applying fundamental principles."
        else:  # interactive
            content = f"Design an experiment to investigate {self.fake.word()} in {self.fake.word()}."
            instructions = "Follow the interactive prompts and record your observations."
            correct_answer = "The experiment demonstrates key concepts through hands-on learning."
        
        exercise = {
            "id": str(uuid.uuid4()),
            "lesson_part_id": lesson_part_id,
            "exercise_type": exercise_type,
            "title": f"Exercise {exercise_order}: {self.fake.catch_phrase()}",
            "content": content,
            "instructions": instructions,
            "correct_answer": correct_answer,
            "explanation": self.fake.paragraph(nb_sentences=2),
            "difficulty_level": difficulty,
            "exercise_order": exercise_order,
            "is_completed": random.choice([True, False]),
            "completed_at": None,
            "created_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            "updated_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
        }
        
        if exercise["is_completed"]:
            exercise["completed_at"] = self.fake.date_time_between(start_date='-7d', end_date='now').isoformat()
        
        return exercise
    
    def generate_subtask(self, exercise_id: str, subtask_order: int) -> Dict[str, Any]:
        """Generate a realistic subtask"""
        subtask_type = random.choice(self.subtask_types)
        
        if subtask_type == "explanation":
            title = f"Additional {random.choice(['Explanation', 'Clarification', 'Details', 'Context'])}"
            content = f"Here's additional information about {self.fake.word()} to help you understand the concept better."
        elif subtask_type == "practice":
            title = f"Practice {random.choice(['Exercises', 'Problems', 'Activities', 'Drills'])}"
            content = f"Complete these additional practice problems to reinforce your understanding of {self.fake.word()}."
        elif subtask_type == "reinforcement":
            title = f"Reinforcement {random.choice(['Review', 'Summary', 'Quiz', 'Check'])}"
            content = f"Review the key points about {self.fake.word()} to ensure you've mastered the concept."
        else:  # extension
            title = f"Extension: {random.choice(['Advanced Topics', 'Related Concepts', 'Applications', 'Research'])}"
            content = f"Explore these advanced applications of {self.fake.word()} to extend your knowledge."
        
        subtask = {
            "id": str(uuid.uuid4()),
            "exercise_id": exercise_id,
            "title": title,
            "content": content,
            "subtask_type": subtask_type,
            "subtask_order": subtask_order,
            "is_optional": random.choice([True, False]),
            "is_completed": random.choice([True, False]),
            "completed_at": None,
            "created_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            "updated_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
        }
        
        if subtask["is_completed"]:
            subtask["completed_at"] = self.fake.date_time_between(start_date='-7d', end_date='now').isoformat()
        
        return subtask
    
    def generate_progress_record(self, entity_type: str, entity_id: str, user_id: str) -> Dict[str, Any]:
        """Generate a realistic progress record"""
        status = random.choice(self.progress_statuses)
        
        if entity_type == "lesson_part":
            progress = {
                "id": str(uuid.uuid4()),
                "lesson_part_id": entity_id,
                "user_id": user_id,
                "status": status,
                "progress_percentage": random.randint(0, 100),
                "time_spent_minutes": random.randint(0, 120),
                "started_at": None,
                "completed_at": None,
                "created_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
                "updated_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
            }
            
            if status != "not_started":
                progress["started_at"] = self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
            
            if status == "completed":
                progress["completed_at"] = self.fake.date_time_between(start_date='-7d', end_date='now').isoformat()
                progress["progress_percentage"] = 100
        
        elif entity_type == "exercise":
            progress = {
                "id": str(uuid.uuid4()),
                "exercise_id": entity_id,
                "user_id": user_id,
                "status": status,
                "attempts": random.randint(0, 5),
                "correct_attempts": random.randint(0, 3),
                "time_spent_minutes": random.randint(0, 60),
                "user_answer": f"User answer: {self.fake.sentence()}",
                "is_correct": random.choice([True, False]),
                "feedback_received": random.choice([True, False]),
                "started_at": None,
                "completed_at": None,
                "created_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
                "updated_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
            }
            
            if status != "not_started":
                progress["started_at"] = self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
            
            if status == "completed":
                progress["completed_at"] = self.fake.date_time_between(start_date='-7d', end_date='now').isoformat()
                progress["is_correct"] = True
                progress["correct_attempts"] = progress["attempts"]
        
        else:  # subtask
            progress = {
                "id": str(uuid.uuid4()),
                "subtask_id": entity_id,
                "user_id": user_id,
                "status": status,
                "time_spent_minutes": random.randint(0, 30),
                "started_at": None,
                "completed_at": None,
                "created_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
                "updated_at": self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
            }
            
            if status != "not_started":
                progress["started_at"] = self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
            
            if status == "completed":
                progress["completed_at"] = self.fake.date_time_between(start_date='-7d', end_date='now').isoformat()
        
        return progress
    
    def generate_extension(self, lesson_id: str, user_id: str) -> Dict[str, Any]:
        """Generate a realistic lesson extension"""
        extension_type = random.choice(["lesson_part", "exercise", "subtask"])
        
        extension_reasons = [
            "Student needs additional foundational material",
            "Request for more comprehensive coverage",
            "Need for supplementary content",
            "Student struggling with core concepts",
            "Request for more practice problems",
            "Need for different difficulty levels",
            "Student wants to explore topic further",
            "Additional explanation required",
            "Request for more examples",
            "Need for reinforcement activities"
        ]
        
        extension = {
            "id": str(uuid.uuid4()),
            "lesson_id": lesson_id,
            "user_id": user_id,
            "extension_type": extension_type,
            "parent_id": None,
            "extension_reason": random.choice(extension_reasons),
            "created_at": self.fake.date_time_between(start_date='-14d', end_date='now').isoformat()
        }
        
        return extension
    
    def insert_lesson(self, lesson: Dict[str, Any]) -> bool:
        """Insert a lesson into the database"""
        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would insert lesson: {lesson['title']}")
                return True
            
            # Insert into lessons table
            result = self.supabase.table("Lessons").insert(lesson).execute()
            
            if result.data:
                print(f"  ✅ Inserted lesson: {lesson['title']}")
                return True
            else:
                print(f"  ❌ Failed to insert lesson: {lesson['title']}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error inserting lesson: {e}")
            return False
    
    def insert_lesson_part(self, part: Dict[str, Any]) -> bool:
        """Insert a lesson part into the database"""
        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would insert lesson part: {part['title']}")
                return True
            
            # Insert into lesson_parts table
            result = self.supabase.table("lesson_parts").insert(part).execute()
            
            if result.data:
                print(f"  ✅ Inserted lesson part: {part['title']}")
                return True
            else:
                print(f"  ❌ Failed to insert lesson part: {part['title']}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error inserting lesson part: {e}")
            return False
    
    def insert_exercise(self, exercise: Dict[str, Any]) -> bool:
        """Insert an exercise into the database"""
        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would insert exercise: {exercise['title']}")
                return True
            
            # Insert into exercises table
            result = self.supabase.table("exercises").insert(exercise).execute()
            
            if result.data:
                print(f"  ✅ Inserted exercise: {exercise['title']}")
                return True
            else:
                print(f"  ❌ Failed to insert exercise: {exercise['title']}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error inserting exercise: {e}")
            return False
    
    def insert_subtask(self, subtask: Dict[str, Any]) -> bool:
        """Insert a subtask into the database"""
        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would insert subtask: {subtask['title']}")
                return True
            
            # Insert into subtasks table
            result = self.supabase.table("subtasks").insert(subtask).execute()
            
            if result.data:
                print(f"  ✅ Inserted subtask: {subtask['title']}")
                return True
            else:
                print(f"  ❌ Failed to insert subtask: {subtask['title']}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error inserting subtask: {e}")
            return False
    
    def insert_progress_record(self, progress: Dict[str, Any], entity_type: str) -> bool:
        """Insert a progress record into the database"""
        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would insert {entity_type} progress record")
                return True
            
            # Determine table name
            if entity_type == "lesson_part":
                table_name = "lesson_part_progress"
            elif entity_type == "exercise":
                table_name = "exercise_progress"
            else:  # subtask
                table_name = "subtask_progress"
            
            # Insert into appropriate progress table
            result = self.supabase.table(table_name).insert(progress).execute()
            
            if result.data:
                print(f"  ✅ Inserted {entity_type} progress record")
                return True
            else:
                print(f"  ❌ Failed to insert {entity_type} progress record")
                return False
                
        except Exception as e:
            print(f"  ❌ Error inserting {entity_type} progress record: {e}")
            return False
    
    def insert_extension(self, extension: Dict[str, Any]) -> bool:
        """Insert a lesson extension into the database"""
        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would insert extension: {extension['extension_type']}")
                return True
            
            # Insert into lesson_extensions table
            result = self.supabase.table("lesson_extensions").insert(extension).execute()
            
            if result.data:
                print(f"  ✅ Inserted extension: {extension['extension_type']}")
                return True
            else:
                print(f"  ❌ Failed to insert extension: {extension['extension_type']}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error inserting extension: {e}")
            return False
    
    def generate_and_insert_data(self, lesson_count: int = 5) -> None:
        """Generate and insert all data"""
        print(f"🚀 Generating and inserting {lesson_count} complete lesson structures...")
        print("=" * 70)
        
        success_count = 0
        
        for i in range(lesson_count):
            print(f"\n📚 Generating Lesson {i+1}/{lesson_count}")
            print("-" * 50)
            
            # Generate lesson
            lesson = self.generate_lesson()
            if not self.insert_lesson(lesson):
                print(f"❌ Failed to insert lesson {i+1}, skipping...")
                continue
            
            self.generated_data['lessons'].append(lesson)
            
            # Generate lesson parts (3-5 per lesson)
            parts_per_lesson = random.randint(3, 5)
            lesson_parts = []
            
            for j in range(parts_per_lesson):
                part = self.generate_lesson_part(lesson["session_id"], j + 1)
                if self.insert_lesson_part(part):
                    lesson_parts.append(part)
                    self.generated_data['lesson_parts'].append(part)
                else:
                    print(f"⚠️ Failed to insert lesson part {j+1}")
            
            # Generate exercises (2-4 per part)
            for part in lesson_parts:
                exercises_per_part = random.randint(2, 4)
                exercises = []
                
                for k in range(exercises_per_part):
                    exercise = self.generate_exercise(part["id"], k + 1)
                    if self.insert_exercise(exercise):
                        exercises.append(exercise)
                        self.generated_data['exercises'].append(exercise)
                    else:
                        print(f"⚠️ Failed to insert exercise {k+1}")
                
                # Generate subtasks (0-2 per exercise)
                for exercise in exercises:
                    if random.random() < 0.7:  # 70% chance of having subtasks
                        subtasks_per_exercise = random.randint(1, 2)
                        
                        for l in range(subtasks_per_exercise):
                            subtask = self.generate_subtask(exercise["id"], l + 1)
                            if self.insert_subtask(subtask):
                                self.generated_data['subtasks'].append(subtask)
                            else:
                                print(f"⚠️ Failed to insert subtask {l+1}")
            
            # Generate progress records for multiple users
            user_count = min(random.randint(2, 4), len(self.profile_ids))
            user_ids = random.sample(self.profile_ids, user_count)
            
            # Progress for lesson parts
            for part in lesson_parts:
                for user_id in user_ids:
                    if random.random() < 0.8:  # 80% chance of having progress
                        progress = self.generate_progress_record("lesson_part", part["id"], user_id)
                        if self.insert_progress_record(progress, "lesson_part"):
                            self.generated_data['progress_records'].append(progress)
            
            # Progress for exercises
            for exercise in self.generated_data['exercises']:
                for user_id in user_ids:
                    if random.random() < 0.8:  # 80% chance of having progress
                        progress = self.generate_progress_record("exercise", exercise["id"], user_id)
                        if self.insert_progress_record(progress, "exercise"):
                            self.generated_data['progress_records'].append(progress)
            
            # Progress for subtasks
            for subtask in self.generated_data['subtasks']:
                for user_id in user_ids:
                    if random.random() < 0.6:  # 60% chance of having progress
                        progress = self.generate_progress_record("subtask", subtask["id"], user_id)
                        if self.insert_progress_record(progress, "subtask"):
                            self.generated_data['progress_records'].append(progress)
            
            # Generate extensions
            if random.random() < 0.4:  # 40% chance of having extensions
                extension_count = random.randint(1, 2)
                
                for _ in range(extension_count):
                    extension = self.generate_extension(lesson["session_id"], random.choice(user_ids))
                    if self.insert_extension(extension):
                        self.generated_data['extensions'].append(extension)
            
            success_count += 1
            print(f"✅ Lesson {i+1} completed successfully!")
        
        print(f"\n🎉 Successfully generated {success_count}/{lesson_count} lesson structures!")
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print a summary of generated data"""
        print("\n📊 Generated Data Summary:")
        print("=" * 50)
        
        for key, data in self.generated_data.items():
            print(f"{key.replace('_', ' ').title()}: {len(data)}")
        
        if not self.dry_run:
            print(f"\n💾 All data has been inserted into the database!")
        else:
            print(f"\n⚠️ This was a DRY RUN - no data was actually inserted")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate fake data using faker library")
    parser.add_argument("--count", type=int, default=5, help="Number of lesson structures to generate (default: 5)")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without inserting data")
    
    args = parser.parse_args()
    
    print("🚀 Faker-based Personalized Learning Data Generator")
    print("=" * 70)
    
    if args.dry_run:
        print("⚠️ DRY RUN MODE - No data will be inserted into the database")
    
    # Create generator
    generator = FakerDataGenerator(dry_run=args.dry_run)
    
    # Generate and insert data
    generator.generate_and_insert_data(args.count)


if __name__ == "__main__":
    main()
