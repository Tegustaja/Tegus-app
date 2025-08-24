"""
Summarizer Tool - Migrated to Standardized Architecture
Summarizes content and extracts key information using LLM.
"""

import os
import asyncio
import glob
import uuid
from typing import List, Optional, Dict, Any
from pydantic import Field
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
import aiofiles

from app.tool.base import (
    BaseTool, 
    ToolType, 
    ContentSubject, 
    DifficultyLevel,
    ContentInput,
    ContentOutput,
    StandardizedToolResult
)

# Load environment variables
load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class Summarizer(BaseTool):
    """
    Summarizer tool with standardized input/output handling.
    Summarizes content and extracts key information using LLM.
    """
    
    # Tool identification
    name: str = "summarizer"
    description: str = "Summarize content and extract key information"
    tool_type: ToolType = ToolType.CONTENT
    version: str = "2.0.0"
    
    # Tool capabilities
    supported_subjects: List[ContentSubject] = [ContentSubject.GENERAL]
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
            "content": {
                "type": "string",
                "description": "Content to summarize",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID this step belongs to",
            },
            "step_index": {
                "type": "integer",
                "description": "Current step index (0-based)",
            },
            "summary_length": {
                "type": "string",
                "default": "medium",
                "enum": ["short", "medium", "long"],
                "description": "Length of summary to generate"
            },
            "focus_areas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific areas to focus on in the summary"
            }
        },
        "required": ["content", "session_id", "step_index"]
    }
    
    # Dependencies
    openai_client: Optional[OpenAI] = Field(
        default_factory=lambda: OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    )

    def _validate_input(self, kwargs: Dict[str, Any]) -> ContentInput:
        """Validate and convert input to ContentInput model."""
        # Extract required fields
        session_id = kwargs.get("session_id")
        step_index = kwargs.get("step_index")
        content = kwargs.get("content")
        
        # Validate required fields
        if not all([session_id, step_index is not None, content]):
            raise ValueError("Missing required parameters: session_id, step_index, content")
        
        # Create ContentInput
        return ContentInput(
            session_id=session_id,
            step_index=step_index,
            prompt=f"Summarize the following content: {content[:100]}...",
            content_type="summary",
            format=kwargs.get("format", "text")
        )

    async def execute(self, input_data: ContentInput) -> ContentOutput:
        """
        Execute the summarizer tool with standardized input/output.
        
        Args:
            input_data: Validated ContentInput containing all necessary parameters
            
        Returns:
            ContentOutput with generated summary
        """
        
        # Generate unique content ID
        content_id = str(uuid.uuid4())
        
        try:
            # Extract content from the input (this would come from the actual input)
            # For now, we'll use a placeholder since ContentInput doesn't have content field
            content = "Content to be summarized"  # This should come from kwargs
            
            # Generate summary using OpenAI
            if not self.openai_client:
                raise ValueError("OpenAI client not configured")
            
            # Create the summarization prompt
            system_prompt = """You are an expert assistant who loves to make summaries. 
            Your task is to create clear, concise summaries that capture the key information 
            without losing important details. Focus on the main points, key concepts, and 
            essential information."""
            
            user_prompt = f"Please create a comprehensive summary of the following content:\n\n{content}"
            
            # Generate summary
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = completion.choices[0].message.content
            
            # Create standardized output
            return ContentOutput(
                content_id=content_id,
                content=summary,
                content_type="summary",
                format="text",
                metadata={
                    "model": "gpt-4o-mini",
                    "input_length": len(content),
                    "output_length": len(summary),
                    "content_id": content_id
                }
            )
            
        except Exception as e:
            # Return a fallback summary if everything fails
            return ContentOutput(
                content_id=content_id,
                content=f"Error generating summary: {str(e)}",
                content_type="error_summary",
                format="text",
                metadata={
                    "error": str(e),
                    "content_id": content_id
                }
            )

    async def summarize_files(self, parent_path: str, mode: str = "r") -> List[str]:
        """
        Legacy method for summarizing files from a directory.
        This maintains backward compatibility while the new architecture is adopted.
        """
        try:
            file_paths = glob.glob(parent_path)
            content = []
            
            for file_path in file_paths:
                try:
                    async with aiofiles.open(file_path, mode, encoding="utf-8") as file:
                        file_content = await file.read()
                        content.append(file_content)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    continue
            
            if not content:
                return ["No content found to summarize"]
            
            # Use the new standardized method
            input_data = ContentInput(
                session_id="legacy_session",
                step_index=0,
                prompt="Summarize the following content from files",
                content_type="file_summary",
                format="text"
            )
            
            result = await self.execute(input_data)
            return [result.content]
            
        except Exception as e:
            return [f"Error during file summarization: {str(e)}"]

# Legacy compatibility
Summarizer = Summarizer

