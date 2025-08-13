import os
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Union
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
#SYSTEM_PROMPT, USER_PROMPT = get_prompt("multiple_choice_exercise")

class MultipleChoiceExercise(BaseTool):
    name: str = "multiple_choice_exercise"
    description: str = "A tool to generate multiple choice exercises based on a query."
    session_id: Optional[str] = None

    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query describing the type of multiple choice exercise to generate",
            },
            "session_id": {
                "type": "string",
                "description": "The session ID this step belongs to.",
            },
            "step_index": {
                "type": "integer",
                "description": "The current step index as a number",
            }
        },
        "required": ["query", "session_id", "step_index"],
    }
    
    supabase: Optional[Client] = Field(default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None)

    async def execute(self, **kwargs) -> list:
        """
        Generates multiple choice exercises based on the query using LLM.
        Also stores the results in the database.
        
        Args:
            **kwargs: Keyword arguments containing:
                - query: The query string describing the type of exercise to generate
                - session_id: The UUID of the session
                - step_index: The current step index as a number (0-based)
        """
        print("DEBUG: Starting MultipleChoiceExercise.execute()")
        
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
            # Generate multiple choice exercise with separated components
            exercise_data = await self._generate_exercise_components(query)
            
            # Store the result in the database
            await self._store_result(session_id, step_index, exercise_data)
            
            # Format the full exercise for display
            formatted_exercise = self._format_for_display(exercise_data)
            
            return [formatted_exercise]
            
        except Exception as e:
            print(f"DEBUG: Error in MultipleChoiceExercise.execute: {str(e)}")
            return ["Error generating exercise"]

    async def _generate_exercise_components(self, query: str) -> dict:
        print(f"DEBUG: Generating exercise for query: {query}")

        try:
            DEFAULT_SYSTEM_PROMPT = """Oled ekspert füüsikaõpetaja, kes loob kvaliteetseid valikvastustega küsimusi 9. klassi õpilastele.
            Järgi neid juhiseid valikvastustega küsimuste koostamisel:

            1. Küsimuste Struktuur:
            - Koosta selged ja konkreetsed küsimused
            - Iga küsimus peab olema üheselt mõistetav
            - Väldi ebavajalikku keerukust või segadust tekitavaid sõnastusi

            2. Vastusevariandid:
            - Loo 4 vastusevarianti (tähistatud 1-4)
            - Ainult üks variant peab olema õige
            - Valed vastusevariandid peavad olema usutavad, kuid selgelt eristatavad õigest
            - Väldi "kõik ülaltoodud" või "mitte ükski ülaltoodud" tüüpi vastuseid

            3. Raskusaste:
            - Küsimused peavad olema sobiva raskusastmega 9. klassi õpilastele
            - Kasuta ainult 9. klassi õppekavas käsitletud mõisteid ja teemasid
            - Vali erinevate raskusastmetega küsimusi (lihtsad faktiteadmised, mõistmine, rakendamine)

            4. Selgitus:
            - Lisa iga küsimuse juurde põhjalik selgitus, miks õige vastus on õige
            - Selgita ka, miks valed vastused on valed
            - Kasuta selgituses lihtsat ja arusaadavat keelt

            Vastus vormista JSON formaadis järgmise struktuuriga:
            {
            "question": "Küsimuse tekst?",
            "choice_1": "Esimene vastusevariant",
            "choice_2": "Teine vastusevariant",
            "choice_3": "Kolmas vastusevariant",
            "choice_4": "Neljas vastusevariant",
            "correct_choice": "1",
            "explanation": "Selgitus, miks õige vastus on õige ja teised valed"
            }"""

            DEFAULT_USER_PROMPT = """Palun koosta valikvastustega küsimus teemal: {query}

            Veendu, et küsimus on sobiva raskusastmega 9. klassi õpilastele.
            Küsimus peab olema selgelt sõnastatud ja vastusevariandid hästi eristuvad.
            Lisa põhjalik selgitus, miks õige vastus on õige ja teised valed."""

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

            # Trimmime vastuse ja prindime uuesti, et näha kas tühikud olid probleemiks
            trimmed_response = llm_response.strip()
            print(f"DEBUG: Trimmed LLM response: '{trimmed_response}'")

            # Attempt to parse the JSON response
            try:
                exercise_json = json.loads(trimmed_response)
                print(f"DEBUG: Parsed JSON: {exercise_json}")

                # Extract the components from the JSON response
                exercise_data = {
                    "question": exercise_json.get("question", ""),
                    "choice_1": exercise_json.get("choice_1", ""),
                    "choice_2": exercise_json.get("choice_2", ""),
                    "choice_3": exercise_json.get("choice_3", ""),
                    "choice_4": exercise_json.get("choice_4", ""),
                    "correct_choice": exercise_json.get("correct_choice", ""),
                    "explanation": exercise_json.get("explanation", "")
                }
                return exercise_data

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response: {e}")
                print(f"Problematic JSON string: {trimmed_response}")
                raise ValueError(f"Could not decode JSON from LLM response: {e}")

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
            KÜSIMUS: {exercise_data['question']}
            
            VASTUSEVARIANDID:
            1. {exercise_data['choice_1']}
            2. {exercise_data['choice_2']}
            3. {exercise_data['choice_3']}
            4. {exercise_data['choice_4']}
            
            ÕIGE VASTUS: {exercise_data['correct_choice']}
            
            SELGITUS: {exercise_data['explanation']}
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
                "event_type": "multiple_choice_exercise",
                "timestamp": timestamp,
                "step_index": step_index,
                "question": exercise_data.get("question", ""),
                "choices": {
                    "choice_1": exercise_data.get("choice_1", ""),
                    "choice_2": exercise_data.get("choice_2", ""),
                    "choice_3": exercise_data.get("choice_3", ""),
                    "choice_4": exercise_data.get("choice_4", "")
                },
                "correct_choice": exercise_data.get("correct_choice", ""),
                "explanation": exercise_data.get("explanation", "")
            }
            
            # Check if we already have this exact content to avoid duplicates
            for event in existing_events:
                if (event.get("event_type") == "multiple_choice_exercise" and 
                    event.get("question") == exercise_data.get("question") and
                    event.get("correct_choice") == exercise_data.get("correct_choice")):
                    print("Exact same content already exists in events, skipping storage")
                    return
            
            # Update the specific step response - completely replace the content structure
            # to avoid nested content issues
            step_responses[step_index] = {
                "status": "finished",
                "step_index": step_index,
                "content": {
                    "tool_type": "multiple_choice_exercise",
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
            print(f"Failed to store MultipleChoiceExercise result: {e}")
            print(f"Session ID: {session_id}, Step Index: {step_index}")
            print(f"Response data: {response.data if 'response' in locals() else 'No response'}")