"""
Check Solution Tool - Migrated to Standardized Architecture
Generates answers to questions/exercises using LLM and stores results.
"""

from app.tool.base import (
    BaseTool, 
    ToolType, 
    DifficultyLevel, 
    ContentSubject,
    AssessmentInput,
    AssessmentOutput,
    StandardizedToolResult
)
from supabase import create_client, Client
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field
import uuid
import asyncio
import os
from dotenv import load_dotenv, find_dotenv

# Constants (only what's needed for Supabase)
load_dotenv(find_dotenv())

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

#def get_prompt(agent_name):
    
#    try:
#        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
#        response = supabase.table("prompts").select("*").eq("users", agent_name).execute()
#        response = supabase.table("prompts").select("*").eq("user", agent_name).execute()


#        if response.data and len(response.data) > 0:
#            return response.data[0]["system_prompt"], response.data[0]["user_secondary_prompt"]
#        else:
#            print(f"No prompts found for agent: {agent_name}, using default prompts")
#            return DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT
#    except Exception as e:
#        print(f"Error fetching prompts from database: {e}")
#        return DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT

# Default prompt as fallback

# Fetch prompts from database
#SYSTEM_PROMPT, USER_PROMPT = get_prompt("check_solution")

class CheckSolution(BaseTool):
    """
    Check Solution tool with standardized input/output handling.
    Generates answers to questions/exercises using LLM and stores results.
    """
    
    # Tool identification
    name: str = "check_solution"
    description: str = "Generate an answer to the provided question/exercise using an LLM"
    tool_type: ToolType = ToolType.ASSESSMENT
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
    max_execution_time: float = 30.0
    parameters: dict = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question or exercise to be answered by the LLM",
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
            }
        },
        "required": ["question", "session_id", "step_index"],
    }
    
    # Dependencies
    supabase: Optional[Client] = Field(
        default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None
    )

    def _validate_input(self, kwargs: dict) -> AssessmentInput:
        """Validate and convert input to AssessmentInput model."""
        # Extract required fields
        question = kwargs.get("question")
        session_id = kwargs.get("session_id")
        step_index = kwargs.get("step_index")
        
        # Validate required fields
        if not all([question, session_id, step_index is not None]):
            raise ValueError("Missing required parameters: question, session_id, step_index")
        
        # Create AssessmentInput with defaults for optional fields
        return AssessmentInput(
            question=question,
            session_id=session_id,
            step_index=step_index,
            expected_answer=kwargs.get("expected_answer"),
            context=kwargs.get("context"),
            user_id=kwargs.get("user_id")
        )

    async def execute(self, input_data: AssessmentInput) -> AssessmentOutput:
        """
        Execute the check solution tool with standardized input/output.
        
        Args:
            input_data: Validated AssessmentInput containing all necessary parameters
            
        Returns:
            AssessmentOutput with structured assessment data
        """
        
        # Generate unique assessment ID
        assessment_id = str(uuid.uuid4())
        
        # Extract parameters
        question = input_data.question
        session_id = input_data.session_id
        step_index = input_data.step_index

        try:
            # Generate answer using LLM
            answer = await self._generate_answer(question)
            
            # Store result in database (optional)
            await self._store_result(input_data, answer, assessment_id)
            
            # Create standardized output
            return AssessmentOutput(
                assessment_id=assessment_id,
                question=question,
                user_answer="",  # No user answer for solution generation
                is_correct=True,  # Generated solution is always correct
                score=1.0,
                feedback=f"Generated solution: {answer}",
                correct_answer=answer,
                explanation="This is the solution generated by the LLM.",
                suggestions=["Review the solution", "Practice similar problems"]
            )
            
        except Exception as e:
            print(f"Error in check solution: {e}")
            # Return fallback output if everything fails
            return AssessmentOutput(
                assessment_id=assessment_id,
                question=question,
                user_answer="",
                is_correct=False,
                score=0.0,
                feedback="Failed to generate solution",
                correct_answer="Solution generation failed",
                explanation="An error occurred while generating the solution.",
                suggestions=["Try again", "Check the question format"]
            )

        # Generate the answer using the LLM
        llm_answer = await self._get_llm_answer(question)

        # Store the question and LLM-generated answer in the database
        await self._store_result(session_id, step_index, question, llm_answer)

        return llm_answer

    async def _get_llm_answer(self, question: str) -> str:
        """Generate an answer to the question using an LLM."""
        try:
            from app.schema import Message
            from app.llm import LLM
            DEFAULT_SYSTEM_PROMPT = """Oled ekspert füüsikaõpetaja, kes aitab 9. klassi õpilastel füüsikat õppida.
            Sinu ülesanne on vastata õpilaste küsimustele selgelt, täpselt ja arusaadavalt.


            Järgi neid juhiseid vastamisel:
            1. Kasuta lihtsat ja arusaadavat keelt, vältides keerulisi termineid, kui need pole hädavajalikud
            2. Selgita mõisteid ja nähtusi põhjalikult, tuues näiteid igapäevaelust
            3. Kui küsimus on ebatäpne või mitmeti mõistetav, vasta kõige tõenäolisema tõlgenduse põhjal
            4. Kui küsimus sisaldab väärarusaamu, paranda need sõbralikult ja selgita õiget arusaama
            5. Kui sa ei tea vastust või küsimus väljub 9. klassi füüsika teemade raamest, ütle seda ausalt

            Vastused peavad olema:
            - Faktiliselt korrektsed ja kooskõlas teadusliku arusaamaga
            - Kohandatud 9. klassi õpilase teadmiste tasemele
            - Struktureeritud ja loogilised
            - Lühikesed ja konkreetsed, kuid siiski piisavalt põhjalikud
            - Huvitavad ja motiveerivad edasi õppima"""

            DEFAULT_USER_PROMPT = """Palun vasta järgmisele füüsikaküsimusele: {question}
                Koosta lühike, maksimaalselt 5 lauseline vastus sellele küsimusele, vasta selgelt ja lisa praktilisi näiteid ja hoia loogiline struktuur """
            # Create system message for the LLM
            system_msg = Message.system_message(DEFAULT_SYSTEM_PROMPT)

            # Create a user message with the question
            user_msg = Message.user_message(
                DEFAULT_USER_PROMPT.format(question=question)
            )

            # Initialize the LLM and get the answer
            llm = LLM()
            answer = await llm.ask(
                messages=[user_msg],
                system_msgs=[system_msg],
                stream=False  # It's usually better to get the full answer at once
            )

            return answer.strip()

        except Exception as e:
            print(f"Error generating LLM answer: {e}")
            return "Error: Could not generate an answer"

    async def _store_result(self, session_id: str, step_index: int, question: str, answer: str) -> None:
        """Store the question and LLM-generated answer in the database with a specific format."""
        try:
            # First get the current lesson data
            if not self.supabase:
                return "Answer generated (DB not configured)"
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
                
            # Get existing events
            existing_content = step_responses[step_index].get("content", {})
            # Make sure we're getting events from the correct place in the structure
            existing_events = existing_content.get("events", [])
            if not existing_events and isinstance(existing_content, dict):
                # Try to find events in nested content if needed
                for key, value in existing_content.items():
                    if isinstance(value, dict) and "events" in value:
                        existing_events = value.get("events", [])
                        break
            
            # Create timestamp for the event
            timestamp = datetime.utcnow().isoformat()
            
            # New event structure with content and metadata
            new_event = {
                "event_type": "check_solution",
                "timestamp": timestamp,
                "content": {
                    "question": question,
                    "answer": answer
                },
    
            }
            
            # Update the specific step response - completely replace the content structure
            # to avoid nested content issues
            step_responses[step_index] = {
                "status": "finished",
                "step_index": step_index,
                "content": {
                    "tool_type": "check_solution",
                    "events": existing_events + [new_event]
                }
            }
            
            # Update the entire step_responses array
            try:
                update_response = self.supabase.table("Lessons").update({
                    "step_responses": step_responses
                }).eq("session_id", session_id).execute()
                
                # Modern Supabase client doesn't have .error attribute
                # Instead, it raises exceptions on errors
            except Exception as update_error:
                print(f"Error updating database: {update_error}")
                
        except Exception as e:
            print(f"Failed to store CheckSolution result: {e}")
            print(f"Session ID: {session_id}, Step Index: {step_index}")
            print(f"Response data: {response.data if 'response' in locals() else 'No response'}")