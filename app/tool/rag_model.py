"""
RAG Model Tool - Migrated to Standardized Architecture
Retrieval-Augmented Generation model for content creation and question answering.
"""

import asyncio
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import Field
from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from supabase import create_client, Client

from app.tool.base import (
    BaseTool, 
    ToolType, 
    ContentSubject, 
    DifficultyLevel,
    ContentInput,
    ContentOutput,
    StandardizedToolResult
)
from app.schema import Message
from app.llm import LLM

# Load environment variables
load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAG_MODEL_CHROMA_DATABASE_PATH = os.getenv("RAG_MODEL_CHROMA_DATABASE_PATH")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class RAGModel(BaseTool):
    """
    RAG Model tool with standardized input/output handling.
    Retrieval-Augmented Generation for content creation and question answering.
    """
    
    # Tool identification
    name: str = "rag_model"
    description: str = "Retrieval-Augmented Generation model for content creation and question answering"
    tool_type: ToolType = ToolType.CONTENT
    version: str = "2.0.0"
    
    # Tool capabilities
    supported_subjects: List[ContentSubject] = [
        ContentSubject.MATH, 
        ContentSubject.PHYSICS, 
        ContentSubject.CHEMISTRY,
        ContentSubject.BIOLOGY,
        ContentSubject.HISTORY,
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
                "description": "Query for content generation or question answering",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID this step belongs to",
            },
            "step_index": {
                "type": "integer",
                "description": "Current step index (0-based)",
            },
            "content_type": {
                "type": "string",
                "description": "Type of content to generate",
                "enum": ["explanation", "summary", "answer", "lesson"]
            },
            "format": {
                "type": "string",
                "default": "text",
                "description": "Output format preference"
            },
            "use_knowledge_base": {
                "type": "boolean",
                "default": True,
                "description": "Whether to use the knowledge base for retrieval"
            }
        },
        "required": ["query", "session_id", "step_index"]
    }
    
    # Dependencies
    supabase: Optional[Client] = Field(
        default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None
    )
    llm: Optional[LLM] = Field(default_factory=LLM)

    def _validate_input(self, kwargs: Dict[str, Any]) -> ContentInput:
        """Validate and convert input to ContentInput model."""
        # Extract required fields
        session_id = kwargs.get("session_id")
        step_index = kwargs.get("step_index")
        query = kwargs.get("query")
        
        # Validate required fields
        if not all([session_id, step_index is not None, query]):
            raise ValueError("Missing required parameters: session_id, step_index, query")
        
        # Create ContentInput
        return ContentInput(
            session_id=session_id,
            step_index=step_index,
            prompt=query,
            content_type=kwargs.get("content_type", "explanation"),
            format=kwargs.get("format", "text")
        )

    async def execute(self, input_data: ContentInput) -> ContentOutput:
        """
        Execute the RAG model tool with standardized input/output.
        
        Args:
            input_data: Validated ContentInput containing all necessary parameters
            
        Returns:
            ContentOutput with generated content
        """
        
        # Generate unique content ID
        content_id = str(uuid.uuid4())
        
        try:
            # Retrieve relevant content from knowledge base
            retrieved_content = ""
            if input_data.content_type != "answer" and self._should_use_knowledge_base():
                retrieved_content = await self._retrieve_from_knowledge_base(input_data.prompt)
            
            # Generate content using LLM
            if not self.llm:
                raise ValueError("LLM not configured")
            
            # Create the system prompt based on content type
            system_prompt = self._get_system_prompt(input_data.content_type)
            
            # Create the user prompt
            user_prompt = self._create_user_prompt(input_data.prompt, retrieved_content, input_data.content_type)
            
            # Generate content
            generated_content = await self.llm.ask(
                messages=[Message.user_message(user_prompt)],
                system_msgs=[Message.system_message(system_prompt)]
            )
            
            # Store result in database if possible
            if self.supabase:
                await self._store_result(input_data, generated_content, content_id)
            
            # Create standardized output
            return ContentOutput(
                content_id=content_id,
                content=generated_content,
                content_type=input_data.content_type,
                format=input_data.format,
                metadata={
                    "query": input_data.prompt,
                    "retrieved_content_length": len(retrieved_content),
                    "generated_content_length": len(generated_content),
                    "content_id": content_id,
                    "model": "rag_model"
                }
            )
            
        except Exception as e:
            # Return a fallback response if everything fails
            return ContentOutput(
                content_id=content_id,
                content=f"Error generating content: {str(e)}",
                content_type="error",
                format="text",
                metadata={
                    "error": str(e),
                    "query": input_data.prompt,
                    "content_id": content_id
                }
            )

    def _should_use_knowledge_base(self) -> bool:
        """Determine if knowledge base should be used."""
        return bool(RAG_MODEL_CHROMA_DATABASE_PATH and OPENAI_API_KEY)

    async def _retrieve_from_knowledge_base(self, query: str) -> str:
        """Retrieve relevant content from the knowledge base."""
        try:
            if not RAG_MODEL_CHROMA_DATABASE_PATH or not OPENAI_API_KEY:
                return ""
            
            # Prepare the database
            embedding_function = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
            db = Chroma(persist_directory=RAG_MODEL_CHROMA_DATABASE_PATH, embedding_function=embedding_function)
            
            # Search the database for relevant chunks
            results = db.similarity_search_with_relevance_scores(query, k=3)
            
            MIN_RAG_DISTANCE = 0.7
            relevant_content = []
            
            for content, score in results:
                if score >= MIN_RAG_DISTANCE:
                    relevant_content.append(content.page_content)
            
            return "\n\n".join(relevant_content) if relevant_content else ""
            
        except Exception as e:
            print(f"Error retrieving from knowledge base: {e}")
            return ""

    def _get_system_prompt(self, content_type: str) -> str:
        """Get appropriate system prompt based on content type."""
        base_prompt = """Sa oled kogenud füüsikaõpetaja ekspert, kes spetsialiseerub 9. klassi füüsika õpetamisele. 
        Sinu ülesanne on koostada põhjalikke, täpseid ja õpilasesõbralikke vastuseid eesti keeles."""
        
        if content_type == "explanation":
            return base_prompt + "\n\nSelgita mõisteid lihtsas, kuid täpses keeles. Jaga keerulised ideed väikesteks, arusaadavateks osadeks."
        elif content_type == "summary":
            return base_prompt + "\n\nTee kokkuvõte, mis rõhutab põhipunkte ja nende omavahelisi seoseid."
        elif content_type == "lesson":
            return base_prompt + "\n\nStruktureeri info loogiliselt, alustades põhimõistetest ja liikudes edasi nende rakendusteni."
        else:
            return base_prompt

    def _create_user_prompt(self, query: str, retrieved_content: str, content_type: str) -> str:
        """Create user prompt based on content type and retrieved content."""
        if retrieved_content:
            return f"""Koosta järgmise 9. klassi füüsika teema kohta põhjalik, selge ja täpne {content_type}:
            
            Küsimus: {query}
            
            Asjakohane info: {retrieved_content}
            
            Palun järgi neid juhiseid:
            1. Selgita kõiki olulisi mõisteid ja nende omavahelisi seoseid lihtsas, kuid täpses keeles
            2. Struktureeri info loogiliselt, alustades põhimõistetest ja liikudes edasi nende rakendusteni
            3. Kasuta konkreetseid näiteid igapäevaelust, et illustreerida füüsikalisi nähtusi"""
        else:
            return f"""Koosta järgmise 9. klassi füüsika teema kohta põhjalik, selge ja täpne {content_type}:
            
            Küsimus: {query}
            
            Palun järgi neid juhiseid:
            1. Selgita kõiki olulisi mõisteid ja nende omavahelisi seoseid lihtsas, kuid täpses keeles
            2. Struktureeri info loogiliselt, alustades põhimõistetest ja liikudes edasi nende rakendusteni
            3. Kasuta konkreetseid näiteid igapäevaelust, et illustreerida füüsikalisi nähtusi"""

    async def _store_result(self, input_data: ContentInput, generated_content: str, content_id: str) -> bool:
        """Store the generated content result in the database."""
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
                "event_type": "rag_model_generation",
                "timestamp": datetime.now().isoformat(),
                "step_index": input_data.step_index,
                "content": generated_content,
                "content_id": content_id,
                "content_type": input_data.content_type
            }
            
            # Update the specific step response
            step_responses[input_data.step_index].update({
                "status": "finished",
                "step_index": input_data.step_index,
                "content": {
                    "tool_type": "rag_model",
                    "events": existing_events + [new_event],
                }
            })
            
            # Update the database
            update_response = self.supabase.table("Lessons").update({
                "step_responses": step_responses
            }).eq("session_id", input_data.session_id).execute()
            
            return update_response.error is None
            
        except Exception as e:
            print(f"Error storing RAG model result: {e}")
            return False

# Legacy compatibility
def get_prompt(agent_name: str, query: str = None):
    """Legacy function for backward compatibility."""
    print("Warning: get_prompt is deprecated. Use the new RAGModel class instead.")
    return "", ""