import os
import aiofiles
from datetime import datetime
from app.tool.base import BaseTool
from app.backtofront.connect_db import insert_data, get_data

class WriteToDB(BaseTool):
    name: str = "write_to_Supabase"
    description: str = """Save content to the central database. This tool requires content which is to be saved."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": """(required) The content to save to the database as a string""",
            },
        },
        "required": ["content"],
    }
    
    async def execute(self, content: str, session_id: str) -> str:
        try:
            # Fetch existing responses
            responses_data = get_data("Lessons", "step_responses", session_id)
            
            # Check if get_data returned an error
            if isinstance(responses_data, Exception):
                return f"Error fetching responses: {str(responses_data)}"
            
            # Ensure responses_data is valid
            if not responses_data or not isinstance(responses_data, list):
                return "Error: No valid response data returned from database"
            
            # Safely get existing responses
            existing_responses = responses_data[0].get('responses', [])
            
            # Calculate next ID
            next_id = 1 if not existing_responses else max(resp['id'] for resp in existing_responses) + 1

            # Create new response object
            new_response = {
                'id': next_id,
                'timestamp': datetime.utcnow().isoformat(),  # Changed to utcnow() for consistency
                'content': content
            }

            # Update responses array
            updated_responses = existing_responses + [new_response]

            # Insert into database
            update_result = insert_data("lesson_sessions", {'responses': updated_responses}, session_id)
            
            # Check if insert_data returned an error
            if isinstance(update_result, Exception):
                return f"Error updating responses: {str(update_result)}"

            # Return success as JSON string
            return f'{{"success": true, "id": {next_id}, "content": "{content}"}}'

        except Exception as e:
            return f"Error in WriteToDB: {str(e)}"

