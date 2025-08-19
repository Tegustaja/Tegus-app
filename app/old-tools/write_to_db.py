from datetime import datetime
from app.tool.base import BaseTool
from pydantic import Field
from supabase import create_client, Client
from typing import Optional
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class WriteToDB(BaseTool):
    name: str = "write_to_Supabase"
    description: str = "Write the content you found to the user."
    supabase: Optional[Client] = Field(default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None)
    session_id: Optional[str] = None

    parameters: dict = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The content to save for the current step.",
            },
            "session_id": {
                "type": "string",
                "description": "The session ID this step belongs to.",
            },
            "step_index": {
                "type": "integer",
                "description": "The index of the step being updated.",
            },
            "status": {
                "type": "string",
                "enum": ["finished", "in_progress", "not_started"],
                "description": "The status of the step being updated.",
            },
            "content_type": {  # Added to support the new 'type' field
                "type": ["string", "null"],
                "description": "The type of content being stored.",
            },
        },
        "required": ["content", "session_id", "step_index", "status"],
    }

    async def execute(self, content: str, session_id: str, step_index: int, status: str, content_type: Optional[str] = None) -> str:
        try:
            self.session_id = session_id
            # Validate inputs
            if not session_id or not isinstance(session_id, str):
                return "Error: session_id must be a non-empty string"
            if not isinstance(step_index, int) or step_index < 0:
                return "Error: step_index must be a non-negative integer"
            if status not in ["finished", "in_progress", "not_started"]:
                return "Error: status must be one of 'finished', 'in_progress', or 'not_started'"

            # Fetch the current lesson from Supabase
            if not self.supabase:
                return "DB not configured; content generated"
            response = self.supabase.table("Lessons").select("step_responses").eq("session_id", session_id).execute()
            
            # Check if lesson exists
            if not response.data or len(response.data) == 0:
                return f"No lesson found for session_id: {session_id}"

            # Get the step_responses list
            lesson = response.data[0]
            step_responses = lesson.get("step_responses", [])

            # Ensure step index is within bounds
            if step_index >= len(step_responses):
                return f"Invalid step_index {step_index}. There are {len(step_responses)} steps."

            # Update the specific step with the new nested structure
            if not isinstance(step_responses[step_index], dict):
                step_responses[step_index] = {
                    "status": "not_started",
                    "content": {
                        "type": None,
                        "content": "",
                        "timestamp": None
                    },
                    "step_index": step_index
                }
            
            # Update the step with the new structure
            step_responses[step_index]["status"] = status
            step_responses[step_index]["content"]["content"] = content.strip()
            step_responses[step_index]["content"]["type"] = content_type
            step_responses[step_index]["content"]["timestamp"] = datetime.now().isoformat()

            # Update the lesson in Supabase
            update_response = (
                self.supabase.table("Lessons")
                .update({"step_responses": step_responses})
                .eq("session_id", session_id)
                .execute()
            )

            # Check if update was successful
            if not update_response.data:
                return f"Error: Failed to update step_responses for session_id {session_id}"

            return f"Step {step_index} successfully updated for session {session_id}."

        except Exception as e:
            return f"Unexpected error in WriteToDB: {str(e)}"