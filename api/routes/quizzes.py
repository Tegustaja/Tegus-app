from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Import existing quiz tools
from app.tool.multiple_choice_exercise import MultipleChoiceExercise
from app.tool.true_false_exercise import TrueFalseExercise
from app.tool.check_solution import CheckSolution

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter(prefix="/quizzes")

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class GenerateQuizRequest(BaseModel):
    topic: str
    difficulty: str = Field(default="medium", description="easy, medium, hard")
    quiz_type: str = Field(default="mixed", description="mixed, multiple_choice, true_false")
    num_questions: int = Field(default=5, ge=1, le=20, description="Number of questions to generate")
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class QuizQuestion(BaseModel):
    question_id: str
    question: str
    question_type: str  # "multiple_choice" or "true_false"
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: str
    explanation: Optional[str] = None
    points: int = 1

class QuizResponse(BaseModel):
    quiz_id: str
    topic: str
    difficulty: str
    quiz_type: str
    num_questions: int
    questions: List[QuizQuestion]
    total_points: int
    time_limit_minutes: Optional[int] = None
    created_at: str

class SubmitAnswerRequest(BaseModel):
    quiz_id: str
    question_id: str
    user_answer: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class SubmitAnswerResponse(BaseModel):
    quiz_id: str
    question_id: str
    is_correct: bool
    correct_answer: str
    user_answer: str
    explanation: Optional[str] = None
    points_earned: int
    feedback: str

class QuizResult(BaseModel):
    quiz_id: str
    user_id: str
    total_questions: int
    correct_answers: int
    total_points: int
    points_earned: int
    percentage: float
    completed_at: str

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: GenerateQuizRequest):
    """
    Generate quiz questions
    """
    try:
        questions = []
        total_points = 0
        
        # Generate questions based on quiz type
        if request.quiz_type == "multiple_choice":
            generator = MultipleChoiceExercise()
            for i in range(request.num_questions):
                question_data = generator.generate_exercise(
                    topic=request.topic,
                    difficulty=request.difficulty
                )
                
                question = QuizQuestion(
                    question_id=f"q_{i+1}",
                    question=question_data.get("question", ""),
                    question_type="multiple_choice",
                    options=question_data.get("options", []),
                    correct_answer=question_data.get("correct_answer", ""),
                    explanation=question_data.get("explanation", ""),
                    points=1
                )
                questions.append(question)
                total_points += question.points
                
        elif request.quiz_type == "true_false":
            generator = TrueFalseExercise()
            for i in range(request.num_questions):
                question_data = generator.generate_exercise(
                    topic=request.topic,
                    difficulty=request.difficulty
                )
                
                question = QuizQuestion(
                    question_id=f"q_{i+1}",
                    question=question_data.get("question", ""),
                    question_type="true_false",
                    correct_answer=question_data.get("correct_answer", ""),
                    explanation=question_data.get("explanation", ""),
                    points=1
                )
                questions.append(question)
                total_points += question.points
                
        else:  # mixed quiz
            # Generate a mix of question types
            mc_generator = MultipleChoiceExercise()
            tf_generator = TrueFalseExercise()
            
            mc_count = request.num_questions // 2
            tf_count = request.num_questions - mc_count
            
            # Generate multiple choice questions
            for i in range(mc_count):
                question_data = mc_generator.generate_exercise(
                    topic=request.topic,
                    difficulty=request.difficulty
                )
                
                question = QuizQuestion(
                    question_id=f"q_{i+1}",
                    question=question_data.get("question", ""),
                    question_type="multiple_choice",
                    options=question_data.get("options", []),
                    correct_answer=question_data.get("correct_answer", ""),
                    explanation=question_data.get("explanation", ""),
                    points=1
                )
                questions.append(question)
                total_points += question.points
            
            # Generate true/false questions
            for i in range(tf_count):
                question_data = tf_generator.generate_exercise(
                    topic=request.topic,
                    difficulty=request.difficulty
                )
                
                question = QuizQuestion(
                    question_id=f"q_{mc_count + i + 1}",
                    question=question_data.get("question", ""),
                    question_type="true_false",
                    correct_answer=question_data.get("correct_answer", ""),
                    explanation=question_data.get("explanation", ""),
                    points=1
                )
                questions.append(question)
                total_points += question.points
        
        # Generate unique quiz ID
        quiz_id = f"quiz_{request.topic}_{request.difficulty}_{len(questions)}"
        
        return QuizResponse(
            quiz_id=quiz_id,
            topic=request.topic,
            difficulty=request.difficulty,
            quiz_type=request.quiz_type,
            num_questions=len(questions),
            questions=questions,
            total_points=total_points,
            time_limit_minutes=request.num_questions * 2,  # 2 minutes per question
            created_at="now()"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )

@router.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_quiz_answer(request: SubmitAnswerRequest):
    """
    Submit and grade quiz answers
    """
    try:
        # Initialize solution checker
        solution_checker = CheckSolution()
        
        # For now, we'll provide a basic response
        # In a real implementation, you'd fetch the quiz question details from the database
        
        # Simulate answer checking
        is_correct = True  # This would be determined by the actual answer checking logic
        points_earned = 1 if is_correct else 0
        feedback = "Correct!" if is_correct else "Incorrect. Try again!"
        
        return SubmitAnswerResponse(
            quiz_id=request.quiz_id,
            question_id=request.question_id,
            is_correct=is_correct,
            correct_answer="",  # Would come from stored quiz
            user_answer=request.user_answer,
            explanation="Explanation would come from the question data",
            points_earned=points_earned,
            feedback=feedback
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )

@router.get("/types")
async def get_quiz_types():
    """
    Get available quiz types
    """
    return {
        "quiz_types": [
            {
                "type": "mixed",
                "name": "Mixed Quiz",
                "description": "Combination of multiple choice and true/false questions"
            },
            {
                "type": "multiple_choice",
                "name": "Multiple Choice Quiz",
                "description": "All questions are multiple choice"
            },
            {
                "type": "true_false",
                "name": "True/False Quiz",
                "description": "All questions are true/false statements"
            }
        ]
    }

@router.get("/difficulties")
async def get_quiz_difficulty_levels():
    """
    Get available quiz difficulty levels
    """
    return {
        "difficulty_levels": [
            {
                "level": "easy",
                "name": "Easy",
                "description": "Basic concepts and simple questions"
            },
            {
                "level": "medium",
                "name": "Medium",
                "description": "Intermediate concepts and moderate complexity"
            },
            {
                "level": "hard",
                "name": "Hard",
                "description": "Advanced concepts and complex questions"
            }
        ]
    }

@router.get("/topics")
async def get_available_topics():
    """
    Get available topics for quiz generation
    """
    return {
        "topics": [
            "mathematics",
            "algebra",
            "geometry",
            "calculus",
            "statistics",
            "physics",
            "chemistry",
            "biology",
            "history",
            "geography",
            "literature",
            "grammar"
        ]
    }
