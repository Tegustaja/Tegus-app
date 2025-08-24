"""
Standardized Multiple Choice Exercise Tool
This demonstrates how to implement tools using the new standardized architecture.
"""

import asyncio
import os
import uuid
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from supabase import create_client, Client
from pydantic import Field

from app.tool.base import (
    BaseTool, 
    ToolType, 
    ExerciseType, 
    DifficultyLevel, 
    ContentSubject,
    ExerciseInput,
    ExerciseOutput,
    StandardizedToolResult
)

# Load environment variables
load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_PATH = os.getenv("MULTIPLECHOICE_DATA_PATH")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class StandardizedMultipleChoiceExercise(BaseTool):
    """
    Standardized multiple choice exercise tool with consistent input/output handling.
    
    This tool demonstrates the new standardized architecture:
    - Uses ExerciseInput for validated input
    - Returns ExerciseOutput for structured results
    - Includes comprehensive metadata
    - Handles errors gracefully
    """
    
    # Tool identification
    name: str = "multiple_choice_exercise"
    description: str = "Generate multiple choice exercises from a knowledge database"
    tool_type: ToolType = ToolType.EXERCISE
    version: str = "2.0.0"
    
    # Tool capabilities
    supported_subjects: List[ContentSubject] = [
        ContentSubject.MATH, 
        ContentSubject.PHYSICS, 
        ContentSubject.CHEMISTRY,
        ContentSubject.BIOLOGY,
        ContentSubject.GENERAL
    ]
    supported_difficulties: List[DifficultyLevel] = [
        DifficultyLevel.BEGINNER,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED
    ]
    
    # Configuration
    max_execution_time: float = 45.0
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Exercise query or description",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID this step belongs to",
            },
            "step_index": {
                "type": "integer",
                "description": "Current step index (0-based)",
            },
            "subject": {
                "type": "string",
                "enum": ["mathematics", "physics", "chemistry", "biology", "general"],
                "description": "Subject category",
            },
            "difficulty": {
                "type": "string",
                "enum": ["beginner", "intermediate", "advanced"],
                "description": "Difficulty level",
            },
            "topic": {
                "type": "string",
                "description": "Specific topic within subject",
            }
        },
        "required": ["query", "session_id", "step_index"],
    }
    
    # Dependencies
    supabase: Optional[Client] = Field(
        default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None
    )

    def _validate_input(self, kwargs: dict) -> ExerciseInput:
        """Validate and convert input to ExerciseInput model."""
        # Extract required fields
        session_id = kwargs.get("session_id")
        step_index = kwargs.get("step_index")
        query = kwargs.get("query")
        
        # Validate required fields
        if not all([session_id, step_index is not None, query]):
            raise ValueError("Missing required parameters: session_id, step_index, query")
        
        # Create ExerciseInput with defaults for optional fields
        return ExerciseInput(
            session_id=session_id,
            step_index=step_index,
            query=query,
            subject=ContentSubject(kwargs.get("subject", "general")),
            difficulty=DifficultyLevel(kwargs.get("difficulty", "intermediate")),
            topic=kwargs.get("topic"),
            user_id=kwargs.get("user_id"),
            custom_prompt=kwargs.get("custom_prompt")
        )

    async def execute(self, input_data: ExerciseInput) -> ExerciseOutput:
        """
        Execute the multiple choice exercise tool with standardized input/output.
        
        Args:
            input_data: Validated ExerciseInput containing all necessary parameters
            
        Returns:
            ExerciseOutput with structured exercise data
        """
        
        # Generate unique exercise ID
        exercise_id = str(uuid.uuid4())
        
        try:
            # Query the ChromaDB for relevant content
            exercise_data = await self._query_knowledge_base(input_data.query)
            
            if not exercise_data:
                # Fallback: generate exercise from query
                exercise_data = await self._generate_fallback_exercise(input_data)
            
            # Create standardized output
            return ExerciseOutput(
                exercise_id=exercise_id,
                exercise_type=ExerciseType.MULTIPLE_CHOICE,
                question=exercise_data["question"],
                options=exercise_data["options"],
                correct_answer=exercise_data["correct_answer"],
                explanation=exercise_data.get("explanation"),
                difficulty=input_data.difficulty,
                subject=input_data.subject,
                topic=input_data.topic,
                metadata={
                    "source": "chroma_database",
                    "query": input_data.query,
                    "generation_method": "rag_retrieval"
                }
            )
            
        except Exception as e:
            # Return a fallback exercise if everything fails
            return ExerciseOutput(
                exercise_id=exercise_id,
                exercise_type=ExerciseType.MULTIPLE_CHOICE,
                question=f"Exercise based on: {input_data.query}",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer="Option A",
                explanation="This is a fallback exercise generated when the database query failed.",
                difficulty=input_data.difficulty,
                subject=input_data.subject,
                topic=input_data.topic,
                metadata={
                    "source": "fallback_generation",
                    "error": str(e),
                    "query": input_data.query
                }
            )

    async def _query_knowledge_base(self, query: str) -> Optional[dict]:
        """Query the ChromaDB knowledge base for relevant content."""
        try:
            if not CHROMA_PATH or not OPENAI_API_KEY:
                return None
                
            # Prepare the database
            embedding_function = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
            db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
            
            # Search the database for relevant chunks
            results = db.similarity_search_with_relevance_scores(query, k=1)
            
            MIN_RAG_DISTANCE = 0.8
            if not results or results[0][1] < MIN_RAG_DISTANCE:
                return None
            
            # Extract and process content
            content = results[0][0].page_content
            
            # Parse content into exercise format (this would depend on your data structure)
            # For now, return a basic structure
            return {
                "question": f"Based on the information: {content[:200]}...",
                "options": [
                    "Option A: First option",
                    "Option B: Second option", 
                    "Option C: Third option",
                    "Option D: Fourth option"
                ],
                "correct_answer": "Option A: First option",
                "explanation": f"This answer is based on the retrieved content: {content[:100]}..."
            }
            
        except Exception as e:
            print(f"Error querying knowledge base: {e}")
            return None

    async def _generate_fallback_exercise(self, input_data: ExerciseInput) -> dict:
        """Generate a fallback exercise when database query fails."""
        return {
            "question": f"Create a multiple choice question about: {input_data.query}",
            "options": [
                "Option A: First option",
                "Option B: Second option",
                "Option C: Third option", 
                "Option D: Fourth option"
            ],
            "correct_answer": "Option A: First option",
            "explanation": "This is a fallback exercise. Please provide the correct answer and explanation."
        }

    async def store_result(self, input_data: ExerciseInput, output: ExerciseOutput) -> bool:
        """Store the exercise result in the database."""
        try:
            if not self.supabase:
                return False
                
            # Store in database
            result = self.supabase.table("exercise_results").insert({
                "session_id": input_data.session_id,
                "step_index": input_data.step_index,
                "exercise_id": output.exercise_id,
                "exercise_type": output.exercise_type.value,
                "question": output.question,
                "options": output.options,
                "correct_answer": output.correct_answer,
                "difficulty": output.difficulty.value,
                "subject": output.subject.value,
                "topic": output.topic,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            return result.data is not None
            
        except Exception as e:
            print(f"Error storing exercise result: {e}")
            return False

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

async def example_usage():
    """Example of how to use the standardized tool."""
    
    # Create tool instance
    tool = StandardizedMultipleChoiceExercise()
    
    # Prepare input
    input_data = {
        "query": "What is the formula for calculating the area of a circle?",
        "session_id": str(uuid.uuid4()),
        "step_index": 0,
        "subject": "mathematics",
        "difficulty": "intermediate",
        "topic": "geometry"
    }
    
    # Execute tool
    result: StandardizedToolResult = await tool(**input_data)
    
    if result.success:
        # Get exercise-specific output
        exercise_output = result.get_exercise_output()
        if exercise_output:
            print(f"Exercise ID: {exercise_output.exercise_id}")
            print(f"Question: {exercise_output.question}")
            print(f"Options: {exercise_output.options}")
            print(f"Correct Answer: {exercise_output.correct_answer}")
            print(f"Difficulty: {exercise_output.difficulty}")
            print(f"Subject: {exercise_output.subject}")
    else:
        print(f"Tool execution failed: {result.error}")
        print(f"Metadata: {result.metadata}")

if __name__ == "__main__":
    asyncio.run(example_usage())
