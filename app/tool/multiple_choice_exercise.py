"""
Multiple Choice Exercise Tool - Migrated to Standardized Architecture
Generates multiple choice exercises from a knowledge database using ChromaDB.
"""

import asyncio
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
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

class MultipleChoiceExercise(BaseTool):
    """
    Multiple choice exercise tool with standardized input/output handling.
    Retrieves exercises from ChromaDB and returns structured exercise data.
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
            
            # Store result in database (optional)
            await self._store_result(input_data, exercise_data, exercise_id)
            
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
                    "generation_method": "rag_retrieval",
                    "exercise_id": exercise_id
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
                    "query": input_data.query,
                    "exercise_id": exercise_id
                }
            )

    async def _query_knowledge_base(self, query: str) -> Optional[Dict[str, Any]]:
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
            
            # Parse content into exercise format
            return await self._parse_content_to_exercise(content, query)
            
        except Exception as e:
            print(f"Error querying knowledge base: {e}")
            return None

    async def _parse_content_to_exercise(self, content: str, query: str) -> Dict[str, Any]:
        """Parse content into multiple choice exercise format."""
        # For now, create a basic exercise structure
        # In a real implementation, you might use LLM to generate proper options
        return {
            "question": f"Based on the following information: {content[:200]}..., what is the main concept related to '{query}'?",
            "options": [
                f"Option A: {content[:50]}...",
                f"Option B: Alternative concept",
                f"Option C: Different interpretation",
                f"Option D: Unrelated concept"
            ],
            "correct_answer": f"Option A: {content[:50]}...",
            "explanation": f"This answer is based on the retrieved content: {content[:100]}..."
        }

    async def _generate_fallback_exercise(self, input_data: ExerciseInput) -> Dict[str, Any]:
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

    async def _store_result(self, input_data: ExerciseInput, exercise_data: Dict[str, Any], exercise_id: str) -> bool:
        """Store the exercise result in the database."""
        try:
            if not self.supabase:
                return False
            
            # Get current lesson data
            response = self.supabase.table("Lessons").select("*").eq("session_id", input_data.session_id).execute()
            if not response.data:
                print(f"No lesson found for session_id: {input_data.session_id}")
                return False
                
            lesson_data = response.data[0]
            step_responses = lesson_data.get("step_responses", [])
            
            # Ensure step_index is within bounds
            if input_data.step_index >= len(step_responses):
                print(f"Step index {input_data.step_index} is out of bounds")
                return False
                
            # Get existing content and events
            existing_content = step_responses[input_data.step_index].get("content", {})
            existing_events = existing_content.get("events", [])
            
            # Create new event
            new_event = {
                "event_type": "multiple_choice_exercise",
                "timestamp": datetime.now().isoformat(),
                "step_index": input_data.step_index,
                "content": exercise_data,
                "exercise_id": exercise_id
            }
            
            # Update the specific step response
            step_responses[input_data.step_index].update({
                "status": "finished",
                "step_index": input_data.step_index,
                "content": {
                    "tool_type": "multiple_choice_exercise",
                    "events": existing_events + [new_event],
                }
            })
            
            # Update the database
            update_response = self.supabase.table("Lessons").update({
                "step_responses": step_responses
            }).eq("session_id", input_data.session_id).execute()
            
            return update_response.error is None
            
        except Exception as e:
            print(f"Error storing exercise result: {e}")
            return False

    async def _format_content(self, content: list) -> str:
        """Format the content into a human-readable summary."""
        try:
            # Combine all content pieces into a single text
            combined_text = "\n\n".join(content)
            
            # Create a system message for formatting
            from app.schema import Message
            system_msg = Message.system_message(
                """Oled ekspert füüsikaõpetaja, kes loob põhjalikke kokkuvõtteid eesti keeles.
                Järgi neid juhiseid:
                
                1. Õpetamise Lähenemine:
                - Kasuta õpilasesõbralikku keelt
                - Jaga keerukaid mõisteid lihtsamateks osadeks
                - Lisa samm-sammult selgitused
                - Lisa visuaalseid kirjeldusi, kus vajalik
                
                2. Keel ja Stiil:
                - Kirjuta selges eesti keeles
                - Kasuta aktiivset kõneviisi
                - Hoida lõike lühikesena (2-3 lauset)
                - Kasuta täpplist märkmeid põhipunktide jaoks
                
                3. Sisu Organiseerimine:
                - Struktureeri infot loogiliselt
                - Kasuta selgeid sektsiooni pealkirju
                - Lisa üleminekulauseid
                - Seo ideid omavahel
                
                4. Interaktiivne Õppimine:
                - Lisa mõtlemapanevaid küsimusi
                - Soovita praktilisi harjutusi
                - Lisa eksperimentide ideid
                - Juhata tähelepanu olulistele detailidele"""
            )
            
            # Create a user message with the content to format
            user_msg = Message.user_message(
                f"""Palun loo järgmise füüsikakontseptsiooni põhjalik kokkuvõte:
                {combined_text}
                
                Struktureeri vastus järgmiselt:
                1. Mõiste
                - Defineeri põhikontseptsioon
                - Selgita selle tähtsust
                - Lisa põhilised komponendid
                
                2. Põhimõisted
                - Selgita põhikontseptsioone
                - Lisa vajalikud valemid
                - Selgita seoseid
                - Lisa olulised parameetrid
                
                3. Rakendused
                - Lisa praktilisi näiteid
                - Selgita reaalses elus kasutamist
                - Lisa seosed teiste kontseptsioonidega
                - Lisa praktilised kasutuskohad
                """
            )
            
            # Use OpenAI to format the content
            from app.llm import LLM
            llm = LLM()
            formatted_output = await llm.ask(
                messages=[user_msg],
                system_msgs=[system_msg]
            )
            
            return formatted_output.strip()
            
        except Exception as e:
            print(f"Error formatting content: {e}")
            return "\n\n".join(content)  # Fallback to raw content if formatting fails

    async def _store_result(self, session_id: str, step_index: int, content: str) -> None:
        """Store the formatted result in the database with a specific format."""
        try:
            # First get the current lesson data
            if not self.supabase:
                return
            response = self.supabase.table("Lessons").select("*").eq("session_id", session_id).execute()
            if not response.data:
                print(f"No lesson found for session_id: {session_id}")
                return
                
            lesson_data = response.data[0]
            step_responses = lesson_data.get("step_responses", [])
            
            # Ensure step_index is within bounds
            if step_index >= len(step_responses):
                print(f"Step index {step_index} is out of bounds")
                return
                
            # Get existing content and events
            existing_content = step_responses[step_index].get("content", {})
            existing_events = existing_content.get("events", [])
            
            # Create timestamp for the event
            timestamp = datetime.now().isoformat()
            
            # New event structure with content and metadata
            new_event = {
                "event_type": "multiple_choice_exercise",
                "timestamp": timestamp,
                "step_index": step_index,
                "content": content,
            }
            
            # Update the specific step response
            step_responses[step_index].update({
                "status": "finished",
                "step_index": step_index,
                "content": {
                    "tool_type": "multiple_choice_exercise",
                    "events": existing_events + [new_event],
                }
            })
            
            # Update the entire step_responses array
            update_response = self.supabase.table("Lessons").update({
                "step_responses": step_responses
            }).eq("session_id", session_id).execute()
            
            if update_response.error:
                print(f"Error updating database: {update_response.error}")
                
        except Exception as e:
            print(f"Failed to store MultipleChoiceExercise result: {e}")
            print(f"Session ID: {session_id}, Step Index: {step_index}")
            print(f"Response data: {response.data if 'response' in locals() else 'No response'}")
