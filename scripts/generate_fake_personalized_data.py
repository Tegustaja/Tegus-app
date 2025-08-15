#!/usr/bin/env python3
"""
Fake Data Generator for Personalized Learning Lesson Structure

This script generates realistic fake data for:
- Lessons (using existing Lessons table)
- Lesson Parts
- Exercises
- Subtasks
- Progress Tracking
- Lesson Extensions

Usage:
    python3 scripts/generate_fake_personalized_data.py [--count N] [--users N] [--lessons N]
"""

import sys
import os
import uuid
import random
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the parent directory to the path so we can import the database models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database models
from database.models import Lesson, LessonPart, Exercise, Subtask, LessonPartProgress, ExerciseProgress, SubtaskProgress, LessonExtension

# Sample data for realistic content generation
SUBJECTS = [
    "Physics", "Mathematics", "Chemistry", "Biology", "Computer Science",
    "History", "Literature", "Geography", "Economics", "Psychology"
]

TOPICS = {
    "Physics": [
        "Mechanics", "Thermodynamics", "Electromagnetism", "Optics", "Quantum Physics",
        "Wave Motion", "Energy Conservation", "Force and Motion", "Gravity", "Electricity"
    ],
    "Mathematics": [
        "Algebra", "Calculus", "Geometry", "Trigonometry", "Statistics",
        "Linear Algebra", "Number Theory", "Probability", "Differential Equations", "Topology"
    ],
    "Chemistry": [
        "Atomic Structure", "Chemical Bonding", "Reactions", "Thermochemistry", "Electrochemistry",
        "Organic Chemistry", "Inorganic Chemistry", "Analytical Chemistry", "Biochemistry", "Physical Chemistry"
    ],
    "Biology": [
        "Cell Biology", "Genetics", "Evolution", "Ecology", "Human Anatomy",
        "Microbiology", "Plant Biology", "Animal Behavior", "Immunology", "Neuroscience"
    ],
    "Computer Science": [
        "Programming", "Data Structures", "Algorithms", "Databases", "Networks",
        "Artificial Intelligence", "Machine Learning", "Software Engineering", "Computer Architecture", "Operating Systems"
    ]
}

EXERCISE_TYPES = [
    "multiple_choice", "true_false", "calculation", "explanation", "interactive"
]

SUBTASK_TYPES = [
    "explanation", "practice", "reinforcement", "extension"
]

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

# Sample exercise content templates
EXERCISE_CONTENT_TEMPLATES = {
    "multiple_choice": [
        "What is the primary function of {concept}?",
        "Which of the following best describes {concept}?",
        "In {context}, what would be the most appropriate approach?",
        "Which statement about {concept} is correct?",
        "What happens when {scenario} occurs?"
    ],
    "true_false": [
        "{statement} - True or False?",
        "Is it correct that {concept}?",
        "Does {scenario} always result in {outcome}?",
        "Can {process} be applied to {context}?",
        "Is {theory} universally accepted?"
    ],
    "calculation": [
        "Calculate the {quantity} for {scenario}",
        "Determine the {result} when {conditions}",
        "Find the {value} given {parameters}",
        "Solve for {unknown} in {equation}",
        "Compute the {measurement} of {object}"
    ],
    "explanation": [
        "Explain how {concept} works in {context}",
        "Describe the process of {procedure}",
        "What are the key principles behind {theory}?",
        "How does {mechanism} function?",
        "What factors influence {phenomenon}?"
    ],
    "interactive": [
        "Simulate {process} and observe the results",
        "Build a model of {system} and test it",
        "Design an experiment to investigate {hypothesis}",
        "Create a visualization of {concept}",
        "Construct a workflow for {procedure}"
    ]
}

# Sample subtask content templates
SUBTASK_CONTENT_TEMPLATES = {
    "explanation": [
        "Additional explanation of {concept}",
        "Step-by-step breakdown of {process}",
        "Common misconceptions about {topic}",
        "Real-world examples of {concept}",
        "Historical context of {discovery}"
    ],
    "practice": [
        "Practice problems for {concept}",
        "Hands-on exercises with {topic}",
        "Interactive simulations of {phenomenon}",
        "Group activities related to {concept}",
        "Lab exercises for {procedure}"
    ],
    "reinforcement": [
        "Review questions for {concept}",
        "Summary of key points about {topic}",
        "Memory aids for {concept}",
        "Quick quiz on {material}",
        "Flashcards for {vocabulary}"
    ],
    "extension": [
        "Advanced applications of {concept}",
        "Related topics to explore",
        "Research opportunities in {field}",
        "Career connections to {subject}",
        "Current developments in {area}"
    ]
}

# Sample correct answers and explanations
SAMPLE_ANSWERS = [
    "The correct answer involves understanding the fundamental principles.",
    "This requires applying the formula with the given values.",
    "The solution follows from the conservation laws.",
    "This can be derived using the standard methodology.",
    "The answer is based on empirical evidence and theory."
]

SAMPLE_EXPLANATIONS = [
    "This concept is fundamental to understanding the broader topic.",
    "The explanation involves several key principles working together.",
    "Understanding this helps build a foundation for advanced concepts.",
    "This demonstrates an important application of the theory.",
    "The explanation shows how theory connects to practical applications."
]

class FakeDataGenerator:
    """Generates fake data for the personalized learning system"""
    
    def __init__(self, supabase_client=None):
        self.supabase_client = supabase_client
        self.generated_data = {
            'lessons': [],
            'lesson_parts': [],
            'exercises': [],
            'subtasks': [],
            'progress_records': [],
            'extensions': []
        }
    
    def generate_lesson_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate fake lesson data"""
        lessons = []
        
        for i in range(count):
            subject = random.choice(SUBJECTS)
            topic = random.choice(TOPICS.get(subject, ["General Topic"]))
            
            lesson = {
                "session_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),  # Will be replaced with actual user IDs
                "topic_id": str(uuid.uuid4()),  # Will be replaced with actual topic IDs
                "title": f"{subject}: {topic} - Lesson {i+1}",
                "focus_area": random.choice([subject, f"{subject} Fundamentals", f"Advanced {subject}"]),
                "proficiency_level": random.choice(["beginner", "intermediate", "advanced"]),
                "steps": {},
                "step_statuses": {},
                "step_responses": {},
                "steps_feedback": {},
                "start_time": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                "last_active": (datetime.utcnow() - timedelta(hours=random.randint(1, 24))).isoformat(),
                "is_completed": random.choice([True, False]),
                "completed_at": None,
                "current_database_index": random.randint(0, 5),
                "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 60))).isoformat()
            }
            
            if lesson["is_completed"]:
                lesson["completed_at"] = (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat()
            
            lessons.append(lesson)
        
        self.generated_data['lessons'] = lessons
        return lessons
    
    def generate_lesson_parts(self, lessons: List[Dict], parts_per_lesson: int = 3) -> List[Dict[str, Any]]:
        """Generate fake lesson part data"""
        lesson_parts = []
        
        for lesson in lessons:
            for i in range(parts_per_lesson):
                part = {
                    "id": str(uuid.uuid4()),
                    "lesson_id": lesson["session_id"],
                    "title": f"Part {i+1}: {self._generate_part_title()}",
                    "description": self._generate_part_description(),
                    "part_order": i + 1,
                    "is_completed": random.choice([True, False]),
                    "completed_at": None,
                    "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                    "updated_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
                }
                
                if part["is_completed"]:
                    part["completed_at"] = (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat()
                
                lesson_parts.append(part)
        
        self.generated_data['lesson_parts'] = lesson_parts
        return lesson_parts
    
    def generate_exercises(self, lesson_parts: List[Dict], exercises_per_part: int = 4) -> List[Dict[str, Any]]:
        """Generate fake exercise data"""
        exercises = []
        
        for part in lesson_parts:
            for i in range(exercises_per_part):
                exercise_type = random.choice(EXERCISE_TYPES)
                difficulty = random.choice(DIFFICULTY_LEVELS)
                
                exercise = {
                    "id": str(uuid.uuid4()),
                    "lesson_part_id": part["id"],
                    "exercise_type": exercise_type,
                    "title": self._generate_exercise_title(exercise_type),
                    "content": self._generate_exercise_content(exercise_type),
                    "instructions": self._generate_exercise_instructions(exercise_type),
                    "correct_answer": random.choice(SAMPLE_ANSWERS) if exercise_type in ["multiple_choice", "true_false", "calculation"] else None,
                    "explanation": random.choice(SAMPLE_EXPLANATIONS),
                    "difficulty_level": difficulty,
                    "exercise_order": i + 1,
                    "is_completed": random.choice([True, False]),
                    "completed_at": None,
                    "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                    "updated_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
                }
                
                if exercise["is_completed"]:
                    exercise["completed_at"] = (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat()
                
                exercises.append(exercise)
        
        self.generated_data['exercises'] = exercises
        return exercises
    
    def generate_subtasks(self, exercises: List[Dict], subtasks_per_exercise: int = 2) -> List[Dict[str, Any]]:
        """Generate fake subtask data"""
        subtasks = []
        
        for exercise in exercises:
            # Not all exercises have subtasks
            if random.random() < 0.7:  # 70% chance of having subtasks
                for i in range(random.randint(1, subtasks_per_exercise)):
                    subtask_type = random.choice(SUBTASK_TYPES)
                    
                    subtask = {
                        "id": str(uuid.uuid4()),
                        "exercise_id": exercise["id"],
                        "title": self._generate_subtask_title(subtask_type),
                        "content": self._generate_subtask_content(subtask_type),
                        "subtask_type": subtask_type,
                        "subtask_order": i + 1,
                        "is_optional": random.choice([True, False]),
                        "is_completed": random.choice([True, False]),
                        "completed_at": None,
                        "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                        "updated_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
                    }
                    
                    if subtask["is_completed"]:
                        subtask["completed_at"] = (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat()
                    
                    subtasks.append(subtask)
        
        self.generated_data['subtasks'] = subtasks
        return subtasks
    
    def generate_progress_data(self, lesson_parts: List[Dict], exercises: List[Dict], subtasks: List[Dict], user_count: int = 5) -> List[Dict[str, Any]]:
        """Generate fake progress tracking data"""
        progress_records = []
        
        # Generate user IDs
        user_ids = [str(uuid.uuid4()) for _ in range(user_count)]
        
        # Generate progress for lesson parts
        for part in lesson_parts:
            for user_id in user_ids:
                if random.random() < 0.8:  # 80% chance of having progress
                    progress = {
                        "id": str(uuid.uuid4()),
                        "lesson_part_id": part["id"],
                        "user_id": user_id,
                        "status": random.choice(["not_started", "in_progress", "completed"]),
                        "progress_percentage": random.randint(0, 100),
                        "time_spent_minutes": random.randint(0, 120),
                        "started_at": None,
                        "completed_at": None,
                        "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                        "updated_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
                    }
                    
                    if progress["status"] != "not_started":
                        progress["started_at"] = (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
                    
                    if progress["status"] == "completed":
                        progress["completed_at"] = (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat()
                        progress["progress_percentage"] = 100
                    
                    progress_records.append(progress)
        
        # Generate progress for exercises
        for exercise in exercises:
            for user_id in user_ids:
                if random.random() < 0.8:  # 80% chance of having progress
                    progress = {
                        "id": str(uuid.uuid4()),
                        "exercise_id": exercise["id"],
                        "user_id": user_id,
                        "status": random.choice(["not_started", "in_progress", "completed", "failed"]),
                        "attempts": random.randint(0, 5),
                        "correct_attempts": random.randint(0, 3),
                        "time_spent_minutes": random.randint(0, 60),
                        "user_answer": f"User answer for exercise {exercise['id'][:8]}",
                        "is_correct": random.choice([True, False]),
                        "feedback_received": random.choice([True, False]),
                        "started_at": None,
                        "completed_at": None,
                        "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                        "updated_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
                    }
                    
                    if progress["status"] != "not_started":
                        progress["started_at"] = (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
                    
                    if progress["status"] == "completed":
                        progress["completed_at"] = (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat()
                        progress["is_correct"] = True
                        progress["correct_attempts"] = progress["attempts"]
                    
                    progress_records.append(progress)
        
        # Generate progress for subtasks
        for subtask in subtasks:
            for user_id in user_ids:
                if random.random() < 0.6:  # 60% chance of having progress (subtasks are optional)
                    progress = {
                        "id": str(uuid.uuid4()),
                        "subtask_id": subtask["id"],
                        "user_id": user_id,
                        "status": random.choice(["not_started", "in_progress", "completed"]),
                        "time_spent_minutes": random.randint(0, 30),
                        "started_at": None,
                        "completed_at": None,
                        "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                        "updated_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
                    }
                    
                    if progress["status"] != "not_started":
                        progress["started_at"] = (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
                    
                    if progress["status"] == "completed":
                        progress["completed_at"] = (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat()
                    
                    progress_records.append(progress)
        
        self.generated_data['progress_records'] = progress_records
        return progress_records
    
    def generate_extensions(self, lessons: List[Dict], user_count: int = 5) -> List[Dict[str, Any]]:
        """Generate fake lesson extension data"""
        extensions = []
        
        # Generate user IDs
        user_ids = [str(uuid.uuid4()) for _ in range(user_count)]
        
        for lesson in lessons:
            # 30% chance of having extensions
            if random.random() < 0.3:
                extension_count = random.randint(1, 3)
                
                for i in range(extension_count):
                    extension_type = random.choice(["lesson_part", "exercise", "subtask"])
                    
                    extension = {
                        "id": str(uuid.uuid4()),
                        "lesson_id": lesson["session_id"],
                        "user_id": random.choice(user_ids),
                        "extension_type": extension_type,
                        "parent_id": None,  # Will be set based on extension type
                        "extension_reason": self._generate_extension_reason(extension_type),
                        "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 14))).isoformat()
                    }
                    
                    extensions.append(extension)
        
        self.generated_data['extensions'] = extensions
        return extensions
    
    def _generate_part_title(self) -> str:
        """Generate a realistic lesson part title"""
        titles = [
            "Introduction and Overview",
            "Core Concepts",
            "Practical Applications",
            "Advanced Topics",
            "Review and Practice",
            "Problem Solving",
            "Real-world Examples",
            "Theory and Principles",
            "Hands-on Activities",
            "Assessment and Evaluation"
        ]
        return random.choice(titles)
    
    def _generate_part_description(self) -> str:
        """Generate a realistic lesson part description"""
        descriptions = [
            "This section introduces the fundamental concepts and provides an overview of the topic.",
            "Explore the core principles and theories that form the foundation of this subject.",
            "Learn how to apply theoretical knowledge to practical, real-world situations.",
            "Dive deeper into advanced concepts and explore cutting-edge developments.",
            "Review what you've learned and practice applying your knowledge.",
            "Develop problem-solving skills through various exercises and challenges.",
            "See how the concepts apply in real-world scenarios and case studies.",
            "Understand the underlying theory and principles behind the concepts.",
            "Engage in hands-on activities to reinforce your learning.",
            "Assess your understanding and evaluate your progress."
        ]
        return random.choice(descriptions)
    
    def _generate_exercise_title(self, exercise_type: str) -> str:
        """Generate a realistic exercise title based on type"""
        if exercise_type == "multiple_choice":
            return f"Multiple Choice: {random.choice(['Understanding', 'Application', 'Analysis', 'Evaluation'])}"
        elif exercise_type == "true_false":
            return f"True or False: {random.choice(['Fact Check', 'Concept Verification', 'Statement Analysis'])}"
        elif exercise_type == "calculation":
            return f"Calculation: {random.choice(['Problem Solving', 'Formula Application', 'Numerical Analysis'])}"
        elif exercise_type == "explanation":
            return f"Explanation: {random.choice(['Concept Clarification', 'Process Description', 'Theory Explanation'])}"
        else:  # interactive
            return f"Interactive: {random.choice(['Simulation', 'Model Building', 'Experiment Design'])}"
    
    def _generate_exercise_content(self, exercise_type: str) -> str:
        """Generate realistic exercise content"""
        template = random.choice(EXERCISE_CONTENT_TEMPLATES[exercise_type])
        concepts = ["force", "energy", "motion", "reaction", "equilibrium", "momentum", "acceleration", "velocity"]
        contexts = ["physics problems", "mathematical equations", "chemical reactions", "biological systems"]
        
        content = template.format(
            concept=random.choice(concepts),
            context=random.choice(contexts),
            scenario="the object moves with constant velocity",
            outcome="the system reaches equilibrium",
            process="the calculation method",
            quantity="net force",
            result="final velocity",
            value="acceleration",
            parameters="initial velocity and time",
            unknown="displacement",
            equation="v = v₀ + at",
            measurement="kinetic energy",
            object="moving particle",
            procedure="data analysis",
            mechanism="force transmission",
            phenomenon="wave propagation",
            hypothesis="the relationship between variables"
        )
        
        return content
    
    def _generate_exercise_instructions(self, exercise_type: str) -> str:
        """Generate realistic exercise instructions"""
        if exercise_type == "multiple_choice":
            return "Select the best answer from the options provided. Consider all possibilities before choosing."
        elif exercise_type == "true_false":
            return "Determine whether each statement is true or false based on your understanding of the concepts."
        elif exercise_type == "calculation":
            return "Show all your work and use appropriate units. Round your final answer to the correct number of significant figures."
        elif exercise_type == "explanation":
            return "Provide a clear, concise explanation using your own words. Include relevant examples when possible."
        else:  # interactive
            return "Follow the interactive prompts and observe the results. Record your observations and conclusions."
    
    def _generate_subtask_title(self, subtask_type: str) -> str:
        """Generate a realistic subtask title"""
        if subtask_type == "explanation":
            return f"Additional {random.choice(['Explanation', 'Clarification', 'Details', 'Context'])}"
        elif subtask_type == "practice":
            return f"Practice {random.choice(['Exercises', 'Problems', 'Activities', 'Drills'])}"
        elif subtask_type == "reinforcement":
            return f"Reinforcement {random.choice(['Review', 'Summary', 'Quiz', 'Check'])}"
        else:  # extension
            return f"Extension: {random.choice(['Advanced Topics', 'Related Concepts', 'Applications', 'Research'])}"
    
    def _generate_subtask_content(self, subtask_type: str) -> str:
        """Generate realistic subtask content"""
        template = random.choice(SUBTASK_CONTENT_TEMPLATES[subtask_type])
        concepts = ["force", "energy", "motion", "reaction", "equilibrium", "momentum", "acceleration", "velocity"]
        topics = ["mechanics", "thermodynamics", "electromagnetism", "optics", "quantum physics"]
        fields = ["physics", "mathematics", "chemistry", "biology", "engineering"]
        
        content = template.format(
            concept=random.choice(concepts),
            topic=random.choice(topics),
            process="problem-solving methodology",
            discovery="scientific breakthrough",
            phenomenon="physical behavior",
            procedure="experimental technique",
            system="physical system",
            hypothesis="scientific hypothesis",
            area="research area",
            vocabulary="technical terms",
            material="course material"
        )
        
        return content
    
    def _generate_extension_reason(self, extension_type: str) -> str:
        """Generate realistic extension reasons"""
        reasons = {
            "lesson_part": [
                "Student needs additional foundational material",
                "Request for more comprehensive coverage",
                "Need for supplementary content",
                "Student struggling with core concepts"
            ],
            "exercise": [
                "Student needs more practice problems",
                "Request for additional challenges",
                "Need for different difficulty levels",
                "Student wants to explore topic further"
            ],
            "subtask": [
                "Student needs additional explanations",
                "Request for more examples",
                "Need for reinforcement activities",
                "Student wants optional enrichment"
            ]
        }
        
        return random.choice(reasons.get(extension_type, ["Student requested additional content"]))
    
    def generate_all_data(self, lesson_count: int = 10, parts_per_lesson: int = 3, 
                          exercises_per_part: int = 4, subtasks_per_exercise: int = 2,
                          user_count: int = 5) -> Dict[str, Any]:
        """Generate all fake data"""
        print("🎯 Generating fake data for personalized learning system...")
        
        # Generate data in dependency order
        lessons = self.generate_lesson_data(lesson_count)
        print(f"✅ Generated {len(lessons)} lessons")
        
        lesson_parts = self.generate_lesson_parts(lessons, parts_per_lesson)
        print(f"✅ Generated {len(lesson_parts)} lesson parts")
        
        exercises = self.generate_exercises(lesson_parts, exercises_per_part)
        print(f"✅ Generated {len(exercises)} exercises")
        
        subtasks = self.generate_subtasks(exercises, subtasks_per_exercise)
        print(f"✅ Generated {len(subtasks)} subtasks")
        
        progress_records = self.generate_progress_data(lesson_parts, exercises, subtasks, user_count)
        print(f"✅ Generated {len(progress_records)} progress records")
        
        extensions = self.generate_extensions(lessons, user_count)
        print(f"✅ Generated {len(extensions)} lesson extensions")
        
        print("\n🎉 All fake data generated successfully!")
        return self.generated_data
    
    def save_to_files(self, output_dir: str = "fake_data"):
        """Save generated data to JSON files"""
        import json
        
        os.makedirs(output_dir, exist_ok=True)
        
        for data_type, data in self.generated_data.items():
            filename = os.path.join(output_dir, f"{data_type}.json")
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"💾 Saved {data_type} to {filename}")
        
        # Save summary
        summary = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                data_type: len(data) for data_type, data in self.generated_data.items()
            }
        }
        
        summary_file = os.path.join(output_dir, "summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"💾 Saved summary to {summary_file}")
    
    def print_summary(self):
        """Print a summary of generated data"""
        print("\n📊 Generated Data Summary:")
        print("=" * 50)
        
        for data_type, data in self.generated_data.items():
            print(f"{data_type.replace('_', ' ').title()}: {len(data)}")
        
        print("\n🔍 Sample Data Preview:")
        print("=" * 50)
        
        # Show sample lesson
        if self.generated_data['lessons']:
            lesson = self.generated_data['lessons'][0]
            print(f"Sample Lesson: {lesson['title']}")
            print(f"  Subject: {lesson['focus_area']}")
            print(f"  Level: {lesson['proficiency_level']}")
            print(f"  Status: {'Completed' if lesson['is_completed'] else 'In Progress'}")
        
        # Show sample exercise
        if self.generated_data['exercises']:
            exercise = self.generated_data['exercises'][0]
            print(f"\nSample Exercise: {exercise['title']}")
            print(f"  Type: {exercise['exercise_type']}")
            print(f"  Difficulty: {exercise['difficulty_level']}")
            print(f"  Content: {exercise['content'][:100]}...")
        
        # Show sample subtask
        if self.generated_data['subtasks']:
            subtask = self.generated_data['subtasks'][0]
            print(f"\nSample Subtask: {subtask['title']}")
            print(f"  Type: {subtask['subtask_type']}")
            print(f"  Optional: {'Yes' if subtask['is_optional'] else 'No'}")
            print(f"  Content: {subtask['content'][:100]}...")


def main():
    """Main function to run the fake data generator"""
    parser = argparse.ArgumentParser(description="Generate fake data for personalized learning system")
    parser.add_argument("--count", type=int, default=10, help="Number of lessons to generate (default: 10)")
    parser.add_argument("--parts", type=int, default=3, help="Number of parts per lesson (default: 3)")
    parser.add_argument("--exercises", type=int, default=4, help="Number of exercises per part (default: 4)")
    parser.add_argument("--subtasks", type=int, default=2, help="Number of subtasks per exercise (default: 2)")
    parser.add_argument("--users", type=int, default=5, help="Number of users for progress tracking (default: 5)")
    parser.add_argument("--output", type=str, default="fake_data", help="Output directory for JSON files (default: fake_data)")
    parser.add_argument("--save", action="store_true", help="Save generated data to JSON files")
    
    args = parser.parse_args()
    
    print("🚀 Personalized Learning Fake Data Generator")
    print("=" * 60)
    
    # Generate fake data
    generator = FakeDataGenerator()
    data = generator.generate_all_data(
        lesson_count=args.count,
        parts_per_lesson=args.parts,
        exercises_per_part=args.exercises,
        subtasks_per_exercise=args.subtasks,
        user_count=args.users
    )
    
    # Print summary
    generator.print_summary()
    
    # Save to files if requested
    if args.save:
        generator.save_to_files(args.output)
    
    print(f"\n✨ Generated {args.count} lessons with realistic data!")
    print("💡 Use --save to export data to JSON files")
    print("💡 Use --help to see all available options")


if __name__ == "__main__":
    main()
