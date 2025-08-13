import os
import asyncio
import json
import re
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

def get_prompt(agent_name):
    """
    Fetch prompt from the database for the specified agent
    
    Args:
        agent_name (str): Name of the agent/tool to fetch prompts for
        
    Returns:
        tuple: (system_prompt, user_secondary_prompt)
    """
    try:
        if not (SUPABASE_URL and SUPABASE_KEY):
            raise ValueError("Supabase not configured")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("prompts").select("*").eq("users", agent_name).execute()
#        response = supabase.table("prompts").select("*").eq("user", agent_name).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["system_prompt"], response.data[0]["user_secondary_prompt"]
        else:
            print(f"No prompts found for agent: {agent_name}, using default prompts")
            return DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT
    except Exception as e:
        print(f"Error fetching prompts from database: {e}")
        return DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT

# Default prompts as fallback
DEFAULT_SYSTEM_PROMPT = """Oled ekspert füüsikaõpetaja, kes loob kvaliteetseid tõene/väär tüüpi küsimusi 9. klassi õpilastele.
Järgi neid juhiseid tõene/väär väidete koostamisel:

1. Väidete Struktuur:
- Koosta selged ja konkreetsed väited
- Iga väide peab olema üheselt kas tõene või väär
- Väldi ebavajalikku keerukust või segadust tekitavaid sõnastusi

2. Väidete Sisu:
- Väited peavad põhinema 9. klassi füüsika õppekaval
- Kasuta olulisi mõisteid ja seaduspärasusi
- Väldi liiga triviaalseid või ilmselgeid väiteid
- Väldi liiga keerulisi või spetsiifilisi väiteid

3. Raskusaste:
- Väited peavad olema sobiva raskusastmega 9. klassi õpilastele
- Kasuta erinevate raskusastmetega väiteid (lihtsad faktiteadmised, mõistmine, rakendamine)
- Väldi liiga keerulisi või mitmetähenduslikke väiteid

4. Selgitus:
- Lisa iga väite juurde põhjalik selgitus, miks väide on tõene või väär
- Selgita asjakohaseid füüsikalisi põhimõtteid ja seaduspärasusi
- Kasuta selgituses lihtsat ja arusaadavat keelt

Vastus vormista JSON formaadis järgmise struktuuriga:
{
  "statement": "Väite tekst",
  "is_true": true/false,
  "explanation": "Selgitus, miks väide on tõene või väär"
}"""

DEFAULT_USER_PROMPT = """Palun koosta tõene/väär tüüpi väide teemal: {query}
                
Veendu, et väide on sobiva raskusastmega 9. klassi õpilastele.
Väide peab olema selgelt sõnastatud ja üheselt kas tõene või väär.
Lisa põhjalik selgitus, miks väide on tõene või väär."""

# Fetch prompts from database
SYSTEM_PROMPT, USER_PROMPT = get_prompt("true_false_exercise")

class TrueFalseExercise(BaseTool):
    name: str = "true_false_exercise"
    description: str = "A tool to generate true/false exercises based on a query."
    session_id: Optional[str] = None

    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query describing the type of true/false exercise to generate",
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
        Generates true/false exercises based on the query using LLM.
        Also stores the results in the database.
        
        Args:
            **kwargs: Keyword arguments containing:
                - query: The query string describing the type of exercise to generate
                - session_id: The UUID of the session
                - step_index: The current step index as a number (0-based)
        """
        print("DEBUG: Starting TrueFalseExercise.execute()")
        
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
            # Generate true/false exercise with separated components
            exercise_data = await self._generate_exercise_components(query)
            
            # Store the result in the database
            await self._store_result(session_id, step_index, exercise_data)
            
            # Format the full exercise for display
            formatted_exercise = self._format_for_display(exercise_data)
            
            return [formatted_exercise]
            
        except Exception as e:
            print(f"DEBUG: Error in TrueFalseExercise.execute: {str(e)}")
            return ["Error generating exercise"]

    async def _generate_exercise_components(self, query: str) -> dict:
        """
        Generate true/false exercise with separated components using LLM.

        Args:
            query: The query describing the type of exercise to generate

        Returns:
            dict: Exercise components (statement, is_true, explanation)
        """
        print(f"DEBUG: Generating exercise for query: {query}")

        try:
            # Create Message objects for system and user prompts
            system_msg = Message.system_message(DEFAULT_SYSTEM_PROMPT)
            user_msg = Message.user_message(
                USER_PROMPT.format(query=query) if USER_PROMPT else DEFAULT_USER_PROMPT.format(query=query)
            )

            # Initialize the LLM and get the exercise
            llm = LLM()
            llm_response = await llm.ask(
                messages=[user_msg],
                system_msgs=[system_msg],
                stream=False  # Set stream to False for a single response
            )

            print(f"DEBUG: Raw LLM response: {llm_response}")
            try:
            # Remove the ```json``` and ``` markers using regular expressions
                json_string = re.sub(r'```json\n?', '', llm_response)
                json_string = re.sub(r'```', '', json_string).strip()

                print(f"DEBUG: Cleaned JSON string: {json_string}")

                exercise_json = json.loads(json_string)
                print(f"DEBUG: Parsed JSON: {exercise_json}")
                exercise_data = {
                    "statement": exercise_json.get("statement", ""),
                    "is_true": exercise_json.get("is_true", False),
                    "explanation": exercise_json.get("explanation", "")
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
            # Convert boolean to Estonian
            is_true_text = "Tõene" if exercise_data['is_true'] else "Väär"
            
            formatted = f"""
            VÄIDE: {exercise_data['statement']}
            
            VASTUS: {is_true_text}
            
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
                "event_type": "true_false_exercise",
                "timestamp": timestamp,
                "step_index": step_index,
                "statement": exercise_data.get("statement", ""),
                "is_true": exercise_data.get("is_true", False),
                "explanation": exercise_data.get("explanation", "")
            }
            
            # Check if we already have this exact content to avoid duplicates
            for event in existing_events:
                if (event.get("event_type") == "true_false_exercise" and 
                    event.get("statement") == exercise_data.get("statement")):
                    print("Exact same content already exists in events, skipping storage")
                    return
            
            # Update the specific step response - completely replace the content structure
            # to avoid nested content issues
            step_responses[step_index] = {
                "status": "finished",
                "step_index": step_index,
                "content": {
                    "tool_type": "true_false_exercise",
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
            print(f"Failed to store TrueFalseExercise result: {e}")
            print(f"Session ID: {session_id}, Step Index: {step_index}")
            print(f"Response data: {response.data if 'response' in locals() else 'No response'}")