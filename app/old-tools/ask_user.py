from app.tool.base import BaseTool
from app.backtofront.connect_db import get_data, insert_data
from datetime import datetime
import asyncio

TABLE_NAME = "lesson_sessions"
ROW_ID = "your_row_id"  # Or dynamically from kwargs/session

class AskUser(BaseTool):
    name: str = "ask_user"
    description: str = """You can ask the user for input, use this tool to ask the user further questions. Use this tool mainly to confirm if the user understood the explanation."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "(required)The question to be asked from the user",
            },
        },
        "required": ["question"],
    }

    async def execute(self, question: str, **kwargs) -> str:
        session_id = kwargs.get("session_id", ROW_ID)
        if not session_id:
            return "Error: No session_id provided."

        # Step 1: Get current messages
        messages_data = get_data(TABLE_NAME, "messages", session_id)
        if not isinstance(messages_data, list):
            return "Error: Could not load messages."

        # Step 2: Get current max ID
        current_max_id = max((msg["id"] for msg in messages_data), default=0)

        # Step 3: Add bot question
        new_bot_msg = {
            "id": current_max_id + 1,
            "text": question,
            "sender": "bot",
            "timestamp": datetime.utcnow().isoformat()
        }
        messages_data.append(new_bot_msg)
        insert_data(TABLE_NAME, "messages", messages_data, session_id)

        # Step 4: Wait for user response (poll every 3s for up to 60s)
        timeout = 60
        interval = 3
        start_time = datetime.utcnow()

        while (datetime.now() - start_time).seconds < timeout:
            updated_data = get_data(TABLE_NAME, "messages", session_id)
            user_replies = [
                msg for msg in updated_data
                if msg["sender"] == "user" and msg["id"] > new_bot_msg["id"]
            ]
            if user_replies:
                return user_replies[-1]["text"]

            await asyncio.sleep(interval)

        return "User did not respond in time."