import asyncio
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.tool.base import BaseTool
from supabase import create_client, Client
import uuid
from typing import Optional
from pydantic import Field

# Load environment variables
load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Constants
CHROMA_PATH = os.getenv("MULTIPLECHOICE_DATA_PATH")
DATA_PATH = os.getenv("MULTIPLECHOICE_CHROMA_DATABASE_PATH")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class MultipleChoiceExercise(BaseTool):
    name: str = "multiple_choice_exercise"
    description: str = "A tool to retrieve multiple choice exercises from a database."
    session_id: Optional[str] = None

    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query sent to the database model",
            },
            "session_id": {
                "type": "string",
                "description": "The session ID this step belongs to.",
            },
            "step_index": {
                "type": "integer",
                "description": "The current step index as a number (0-based)",
            }
        },
        "required": ["query", "session_id", "step_index"],
    }
    
    supabase: Optional[Client] = Field(default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None)

    async def execute(self, **kwargs) -> list:
        """
        Performs a similarity search on the exercise database and returns relevant answers.
        Also stores the results in the database.
        
        Args:
            **kwargs: Keyword arguments containing:
                - query: The query string
                - session_id: The UUID of the session
                - step_index: The current step index as a number (0-based)
        """
        # Extract and validate parameters
        query = kwargs.get("query")
        session_id = kwargs.get("session_id")
        step_index = kwargs.get("step_index")

        if not all([query, session_id, step_index is not None]):
            print(f"Missing parameters: query={query}, session_id={session_id}, step_index={step_index}")
            return ["Error: Missing required parameters"]

        # Ensure step_index is an integer
        try:
            step_index = int(step_index)
        except (ValueError, TypeError):
            print(f"Invalid step_index: {step_index}")
            return ["Error: step_index must be a number"]

        # Validate session_id format (UUID)
        try:
            uuid.UUID(session_id)
        except ValueError:
            print(f"Invalid session_id: {session_id}")
            return ["Error: session_id must be a valid UUID"]

        # Store session_id for later use
        self.session_id = session_id

        # First, make the ChromaDB query
        try:
            # Prepare the database
            embedding_function = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
            db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
            
            # Search the database for relevant chunks
            results = db.similarity_search_with_relevance_scores(query, k=1)
            
            MIN_RAG_DISTANCE = 0.8
            if not results or results[0][1] < MIN_RAG_DISTANCE:
                return [f"Unable to find matching results for '{query}'"]
            
            # Extract content from results
            #content = [result[0].page_content for result in results]
            content = [result[0].page_content for result in results][0]

            # Format the content into a human-readable summary
            #formatted_content = await self._format_content(content)

            # Check for existing content in the database
            '''try:
                response = self.supabase.table("Lessons").select("*").eq("session_id", session_id).execute()
                if response.data:
                    lesson_data = response.data[0]
                    step_responses = lesson_data.get("step_responses", [])
                    if step_index < len(step_responses):
                        last_content = step_responses[step_index].get("content", {}).get("events", [])
                        if last_content:
                            last_event = last_content[-1]
                            if last_event.get("event_type") == "rag_search":
                                # Compare existing content with new content
                                should_store = await self._should_store_new_content(
                                    last_event.get("content", ""),
                                    formatted_content
                                )
                                print(f"Should store new content: {should_store}")
                                if not should_store:
                                    print("Content is similar to existing content, skipping storage")
                                    return content
            except Exception as e:
                print(f"Error checking existing content: {e}")
                # Continue with storage if check fails'''

            # Store the formatted content in the database
            await self._store_result(session_id, step_index, content)
            
            return content
                
        except Exception as e:
            return [f"Error occurred while processing the query: {str(e)}"]

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
