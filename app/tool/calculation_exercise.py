import os
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Union
from pydantic import Field

from app.tool.base import BaseTool
from app.schema import Message
from app.llm import LLM
from supabase import create_client, Client

# Load environment variables
from dotenv import load_dotenv, find_dotenv
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
    name: str = "calculation_exercise"
    description: str = "A tool to generate calculation exercises based on a query."
    session_id: Optional[str] = None

    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query describing the type of calculation exercise to generate",
            },
            "session_id": {
                "type": "string",
                "description": "The session ID this step belongs to.",
            },
            "step_index": {
                "type": "integer",
                "description": "The current step index as a number ",
            }
        },
        "required": ["query", "session_id", "step_index"],
    }
    
    supabase: Optional[Client] = Field(default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None)

    async def execute(self, **kwargs) -> list:
        """
        Generates calculation exercises based on the query using LLM.
        Also stores the results in the database.
        
        Args:
            **kwargs: Keyword arguments containing:
                - query: The query string describing the type of exercise to generate
                - session_id: The UUID of the session
                - step_index: The current step index as a number (0-based)
        """
        print("DEBUG: Starting CalculationExercise.execute()")
        
        # Extract and validate parameters
        query = kwargs.get("query")
        session_id = kwargs.get("session_id")
        step_index = kwargs.get("step_index")
        
        print(f"DEBUG: Parameters - query: {query}, session_id: {session_id}, step_index: {step_index}")
        
        # Validate parameters
        if not all([query, session_id, step_index is not None]):
            print("DEBUG: Missing required parameters")
            return ["Error: Missing required parameters"]
        
        try:
            # Generate calculation exercise with separated components
            exercise_data = await self._generate_exercise_components(query)
            
            # Store the result in the database
            await self._store_result(session_id, step_index, exercise_data)
            
            # Format the full exercise for display
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