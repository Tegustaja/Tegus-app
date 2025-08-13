from app.tool.base import BaseTool
from supabase import create_client, Client
from datetime import datetime
from typing import Optional
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
    name: str = "check_solution"
    description: str = """Generate an answer to the provided question/exercise using an LLM 
    and store the question and answer in the database."""
    session_id: Optional[str] = None

    parameters: dict = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "(required) The question or exercise to be answered by the LLM",
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
        "required": ["question", "session_id", "step_index"],
    }
    
    supabase: Optional[Client] = Field(default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None)

    async def execute(self, question: str, **kwargs) -> str:
        """
        Generates an answer to the question using an LLM and stores it in the database.

        Args:
            question: The question/exercise string
            **kwargs: Keyword arguments containing:
                - session_id: The UUID of the session
                - step_index: The current step index as a number (0-based)
        """
        # Extract and validate additional parameters
        session_id = kwargs.get("session_id")
        step_index = kwargs.get("step_index")
        
        # If the caller didn't provide a step_index but we're in an agent with a current_step_index, use that
        # This ensures we're always using the correct step index from the planning flow
        import inspect
        frame = inspect.currentframe()
        try:
            while frame:
                if 'self' in frame.f_locals and hasattr(frame.f_locals['self'], 'current_step_index'):
                    agent = frame.f_locals['self']
                    if agent.current_step_index is not None and hasattr(agent, 'session_id'):
                        print(f"Using step_index {agent.current_step_index} from agent instead of {step_index}")
                        step_index = agent.current_step_index
                        if not session_id and agent.session_id:
                            session_id = agent.session_id
                        break
                frame = frame.f_back
        finally:
            del frame  # Avoid reference cycles

        if not all([question, session_id, step_index is not None]):
            print(f"Missing parameters: question={question}, session_id={session_id}, step_index={step_index}")
            return "Error: Missing required parameters"

        # Ensure step_index is an integer
        try:
            step_index = int(step_index)
        except (ValueError, TypeError):
            print(f"Invalid step_index: {step_index}")
            return "Error: step_index must be a number"

        # Validate session_id format (UUID)
        try:
            uuid.UUID(session_id)
        except ValueError:
            print(f"Invalid session_id: {session_id}")
            return "Error: session_id must be a valid UUID"

        # Store session_id for later use
        self.session_id = session_id

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