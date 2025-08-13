from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Import existing exercise tools
from app.tool.calculation_exercise import CalculationExercise
from app.tool.multiple_choice_exercise import MultipleChoiceExercise
from app.tool.true_false_exercise import TrueFalseExercise
from app.tool.check_solution import CheckSolution

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter(prefix="/exercises")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class GenerateExerciseRequest(BaseModel):
    topic: str
    difficulty: str = Field(default="medium", description="easy, medium, hard")
    exercise_type: str = Field(default="calculation", description="calculation, multiple_choice, true_false")
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ExerciseResponse(BaseModel):
    exercise_id: str
    topic: str
    difficulty: str
    exercise_type: str
    question: str
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: str
    explanation: Optional[str] = None
    hints: Optional[List[str]] = None
    created_at: str

class CheckAnswerRequest(BaseModel):
    exercise_id: str
    user_answer: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class CheckAnswerResponse(BaseModel):
    exercise_id: str
    is_correct: bool
    correct_answer: str
    user_answer: str
    explanation: Optional[str] = None
    score: Optional[float] = None
    feedback: str

@router.post("/generate", response_model=ExerciseResponse)
async def generate_exercise(request: GenerateExerciseRequest):
    """
    Generate calculation exercises, multiple choice, or true/false questions
    """
    try:
        # Initialize exercise generator based on type
        if request.exercise_type == "calculation":
            exercise_generator = CalculationExercise()
        elif request.exercise_type == "multiple_choice":
            exercise_generator = MultipleChoiceExercise()
        elif request.exercise_type == "true_false":
            exercise_generator = TrueFalseExercise()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid exercise type. Must be 'calculation', 'multiple_choice', or 'true_false'"
            )
        
        # Generate exercise
        exercise_data = exercise_generator.generate_exercise(
            topic=request.topic,
            difficulty=request.difficulty
        )
        
        # Create exercise record in database if user_id is provided
        if request.user_id:
            exercise_record = {
                "topic": request.topic,
                "difficulty": request.difficulty,
                "exercise_type": request.exercise_type,
                "question": exercise_data.get("question", ""),
                "correct_answer": exercise_data.get("correct_answer", ""),
                "options": exercise_data.get("options", []),
                "explanation": exercise_data.get("explanation", ""),
                "hints": exercise_data.get("hints", []),
                "user_id": request.user_id,
                "session_id": request.session_id,
                "created_at": "now()"
            }
            
            # Store in database (you might want to create an exercises table)
            # For now, we'll just return the generated exercise
            
        return ExerciseResponse(
            exercise_id=exercise_data.get("id", "generated_exercise"),
            topic=request.topic,
            difficulty=request.difficulty,
            exercise_type=request.exercise_type,
            question=exercise_data.get("question", ""),
            options=exercise_data.get("options"),
            correct_answer=exercise_data.get("correct_answer", ""),
            explanation=exercise_data.get("explanation"),
            hints=exercise_data.get("hints"),
            created_at="now()"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate exercise: {str(e)}"
        )

@router.post("/check-answer", response_model=CheckAnswerResponse)
async def check_exercise_answer(request: CheckAnswerRequest):
    """
    Check user's exercise answer
    """
    try:
        # Initialize solution checker
        solution_checker = CheckSolution()
        
        # Check the answer
        result = solution_checker.check_answer(
            user_answer=request.user_answer,
            correct_answer="",  # This would come from the stored exercise
            exercise_type="calculation"  # This would be determined from the exercise
        )
        
        # For now, we'll provide a basic response
        # In a real implementation, you'd fetch the exercise details from the database
        
        is_correct = result.get("is_correct", False)
        feedback = result.get("feedback", "Answer checked successfully")
        
        return CheckAnswerResponse(
            exercise_id=request.exercise_id,
            is_correct=is_correct,
            correct_answer="",  # Would come from stored exercise
            user_answer=request.user_answer,
            explanation=result.get("explanation"),
            score=result.get("score", 0.0),
            feedback=feedback
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check answer: {str(e)}"
        )

@router.get("/types")
async def get_exercise_types():
    """
    Get available exercise types
    """
    return {
        "exercise_types": [
            {
                "type": "calculation",
                "name": "Calculation Exercise",
                "description": "Mathematical calculations and problem solving"
            },
            {
                "type": "multiple_choice",
                "name": "Multiple Choice",
                "description": "Choose the correct answer from multiple options"
            },
            {
                "type": "true_false",
                "name": "True/False",
                "description": "Determine if a statement is true or false"
            }
        ]
    }

@router.get("/difficulties")
async def get_difficulty_levels():
    """
    Get available difficulty levels
    """
    return {
        "difficulty_levels": [
            {
                "level": "easy",
                "name": "Easy",
                "description": "Basic concepts and simple problems"
            },
            {
                "level": "medium",
                "name": "Medium",
                "description": "Intermediate concepts and moderate complexity"
            },
            {
                "level": "hard",
                "name": "Hard",
                "description": "Advanced concepts and complex problems"
            }
        ]
    }
