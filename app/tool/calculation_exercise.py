"""
Calculation Exercise Tool - Migrated to Standardized Architecture
Generates calculation exercises using LLM based on user queries.
"""

import os
import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, List, Union, Dict, Any
from pydantic import Field
from dotenv import load_dotenv, find_dotenv

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
from app.schema import Message
from app.llm import LLM
from supabase import create_client, Client

# Load environment variables
load_dotenv(find_dotenv())

# Constants
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

# Default prompts as fallback




# Fetch prompts from database
#SYSTEM_PROMPT, USER_PROMPT = get_prompt("calculation_exercise")

class CalculationExercise(BaseTool):
    """
    Calculation exercise tool with standardized input/output handling.
    Generates calculation exercises using LLM based on user queries.
    """
    
    # Tool identification
    name: str = "calculation_exercise"
    description: str = "Generate calculation exercises based on a query using LLM"
    tool_type: ToolType = ToolType.EXERCISE
    version: str = "2.0.0"
    
    # Tool capabilities
    supported_subjects: List[ContentSubject] = [
        ContentSubject.MATH, 
        ContentSubject.PHYSICS, 
        ContentSubject.CHEMISTRY,
        ContentSubject.GENERAL
    ]
    supported_difficulties: List[DifficultyLevel] = [
        DifficultyLevel.BEGINNER,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED
    ]
    
    # Configuration
    max_execution_time: float = 60.0
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Query describing the type of calculation exercise to generate",
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
                "enum": ["mathematics", "physics", "chemistry", "general"],
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
            subject=ContentSubject(kwargs.get("subject", "mathematics")),
            difficulty=DifficultyLevel(kwargs.get("difficulty", "intermediate")),
            topic=kwargs.get("topic"),
            user_id=kwargs.get("user_id"),
            custom_prompt=kwargs.get("custom_prompt")
        )

    async def execute(self, input_data: ExerciseInput) -> ExerciseOutput:
        """
        Execute the calculation exercise tool with standardized input/output.
        
        Args:
            input_data: Validated ExerciseInput containing all necessary parameters
            
        Returns:
            ExerciseOutput with structured exercise data
        """
        
        # Generate unique exercise ID
        exercise_id = str(uuid.uuid4())
        
        print("DEBUG: Starting CalculationExercise.execute()")
        print(f"DEBUG: Parameters - query: {input_data.query}, session_id: {input_data.session_id}, step_index: {input_data.step_index}")
        
        try:
            # Generate calculation exercise with separated components
            exercise_data = await self._generate_exercise_components(input_data.query)
            
            # Store result in database (optional)
            await self._store_result(input_data, exercise_data, exercise_id)
            
            # Create standardized output
            return ExerciseOutput(
                exercise_id=exercise_id,
                exercise_type=ExerciseType.CALCULATION,
                question=exercise_data["question"],
                options=None,  # Calculation exercises don't have multiple choice options
                correct_answer=exercise_data["answer"],
                explanation=exercise_data.get("explanation"),
                difficulty=input_data.difficulty,
                subject=input_data.subject,
                topic=input_data.topic,
                metadata={
                    "source": "llm_generation",
                    "query": input_data.query,
                    "generation_method": "llm_calculation",
                    "exercise_id": exercise_id,
                    "calculation_type": exercise_data.get("calculation_type", "general")
                }
            )
            
        except Exception as e:
            print(f"DEBUG: Error in calculation exercise generation: {e}")
            # Return a fallback exercise if everything fails
            return ExerciseOutput(
                exercise_id=exercise_id,
                exercise_type=ExerciseType.CALCULATION,
                question=f"Calculate the result for: {input_data.query}",
                options=None,
                correct_answer="Please solve this calculation",
                explanation="This is a fallback exercise generated when the LLM generation failed.",
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
                "event_type": "calculation_exercise",
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
                    "tool_type": "calculation_exercise",
                    "events": existing_events + [new_event],
                }
            })
            
            # Update the database
            update_response = self.supabase.table("Lessons").update({
                "step_responses": step_responses
            }).eq("session_id", input_data.session_id).execute()
            
            return update_response.error is None
            
        except Exception as e:
            print(f"Error storing calculation exercise result: {e}")
            return False
            formatted_exercise = self._format_for_display(exercise_data)
            
            return [formatted_exercise]
            
        except Exception as e:
            print(f"DEBUG: Error in CalculationExercise.execute: {str(e)}")
            return ["Error generating exercise"]

    
    async def _generate_exercise_components(self, query: str) -> dict:
        """
        Generate calculation exercise with separated components using LLM.

        Args:
            query: The query describing the type of exercise to generate

        Returns:
            dict: Exercise components (title, description, question, solution, answer)
        """
        print(f"DEBUG: Generating exercise for query: {query}")

        try:
            DEFAULT_SYSTEM_PROMPT = """Oled ekspert füüsikaõpetaja, kes loob kvaliteetseid arvutusülesandeid 9. klassi õpilastele.
            Järgi neid juhiseid arvutusülesannete koostamisel:

            1. Ülesande Struktuur:
            - Koosta selge ja konkreetne probleemi kirjeldus
            - Lisa kõik vajalikud algandmed selgelt ja täpselt
            - Veendu, et ülesanne on lahendatav antud andmetega
            - Väldi ebavajalikku infot, mis võib õpilast segadusse ajada

            2. Raskusaste:
            - Ülesanne peab olema jõukohane 9. klassi õpilasele
            - Kasuta ainult 9. klassi õppekavas käsitletud mõisteid ja valemeid
            - Väldi liiga keerulisi arvutusi

            3. Lahenduskäik:
            - Koosta selge ja samm-sammuline lahendus
            - Selgita iga sammu põhjendust
            - Näita kõik vajalikud valemid ja teisendused
            - Kontrolli, et ühikud oleksid korrektsed ja järjepidevad

            4. Vastus:
            - Esita lõppvastus selgelt ja korrektse ühikuga
            - Veendu, et vastus on realistlik ja füüsikaliselt mõistlik

            Koosta ülesanne järgmistes komponentides:
            1. Pealkiri - lühike ja informatiivne
            2. Kirjeldus - ülesande kontekst ja taustinfo
            3. Küsimus - konkreetne küsimus, millele õpilane peab vastama
            4. Lahendus - detailne lahenduskäik koos selgitustega
            5. Vastus - lõppvastus korrektse ühikuga

            Vastus vormista JSON formaadis järgmise struktuuriga:
            {
            "title": "Ülesande pealkiri",
            "description": "Ülesande kirjeldus ja kontekst",
            "question": "Konkreetne küsimus",
            "solution": "Detailne lahenduskäik",
            "answer": "Lõppvastus korrektse ühikuga"
            }"""


            DEFAULT_USER_PROMPT = """Palun koosta arvutusülesanne teemal: {query}

            Veendu, et ülesanne on sobiva raskusastmega 9. klassi õpilastele.
            Ülesanne peab olema selgelt sõnastatud ja lahendatav.
            Lisa detailne lahenduskäik ja vastus."""

            # Create Message objects for system and user prompts
            system_msg = Message.system_message(DEFAULT_SYSTEM_PROMPT)
            user_msg = Message.user_message(
                DEFAULT_USER_PROMPT.format(query=query)
            )

            # Initialize the LLM and get the exercise
            llm = LLM()
            llm_response = await llm.ask(
                messages=[user_msg],
                system_msgs=[system_msg],
                stream=False
            )

            print(f"DEBUG: Raw LLM response: {llm_response}")

            # Attempt to parse the JSON response
            try:
                exercise_json = json.loads(llm_response)
                print(f"DEBUG: Parsed JSON: {exercise_json}")

                # Extract the components from the JSON response
                exercise_data = {
                    "title": exercise_json.get("title", ""),
                    "description": exercise_json.get("description", ""),
                    "question": exercise_json.get("question", ""),
                    "solution": exercise_json.get("solution", ""),
                    "answer": exercise_json.get("answer", "")
                }
                return exercise_data

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response: {e}")
                print(f"Problematic JSON string: {llm_response}")
                raise ValueError(f"Could not decode JSON from LLM response: {e}")

        except Exception as e:
            print(f"Error generating exercise components: {e}")
            raise

    def _format_for_display(self, exercise_data: dict) -> str:
        """Format the exercise data into a human-readable format for display."""
        try:
            formatted = f"""
            PEALKIRI: {exercise_data['title']}
            
            KIRJELDUS: {exercise_data['description']}
            
            KÜSIMUS: {exercise_data['question']}
            
            LAHENDUS:
            {exercise_data['solution']}
            
            VASTUS: {exercise_data['answer']}
            """
            return formatted.strip()
        except Exception as e:
            print(f"Error formatting exercise for display: {e}")
            return str(exercise_data)  # Fallback to string representation of the dict

    async def _store_result(self, session_id: str, step_index: int, exercise_data: dict) -> None:
        """Store the exercise data in the database with a specific format."""
        try:
            # First get the current lesson data
            if not self.supabase:
                return
            response = self.supabase.table("Lessons").select("*").eq("session_id", session_id).execute()
            
            # Check if response has data
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
                "event_type": "calculation_exercise",
                "timestamp": timestamp,
                "step_index": step_index,
                "exercise": {
                    "title": exercise_data.get("title", ""),
                    "description": exercise_data.get("description", ""),
                    "question": exercise_data.get("question", "")
                },
                "solution": exercise_data.get("solution", ""),
                "answer": exercise_data.get("answer", "")
            }
            
            # Check if we already have this exact content to avoid duplicates
            for event in existing_events:
                if (event.get("event_type") == "calculation_exercise" and 
                    event.get("exercise", {}).get("title") == exercise_data.get("title") and
                    event.get("answer") == exercise_data.get("answer")):
                    print("Exact same content already exists in events, skipping storage")
                    return
            
            # Update the specific step response - completely replace the content structure
            # to avoid nested content issues
            step_responses[step_index] = {
                "status": "finished",
                "step_index": step_index,
                "content": {
                    "tool_type": "calculation_exercise",
                    "events": existing_events + [new_event]
                }
            }
            
            # Update the entire step_responses array
            try:
                update_response = self.supabase.table("Lessons").update({
                    "step_responses": step_responses
                }).eq("session_id", session_id).execute()
                
                # Verify the update was successful
                if not update_response.data:
                    print(f"Update may have failed - no data returned from Supabase")
                    
            except Exception as supabase_error:
                print(f"Error updating database: {supabase_error}")
                
        except Exception as e:
            print(f"Failed to store CalculationExercise result: {e}")
            print(f"Session ID: {session_id}, Step Index: {step_index}")
            print(f"Response data: {response.data if 'response' in locals() else 'No response'}")