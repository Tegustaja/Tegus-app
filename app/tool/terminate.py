from app.tool.base import BaseTool, ToolType, ContentSubject, DifficultyLevel
from typing import List


_TERMINATE_DESCRIPTION = """Terminate the interaction when the request is met OR if the assistant cannot proceed further with the task.
When you have finished all the tasks, call this tool to end the work."""


class Terminate(BaseTool):
    name: str = "terminate"
    description: str = _TERMINATE_DESCRIPTION
    tool_type: ToolType = ToolType.UTILITY
    version: str = "2.0.0"
    
    # Tool capabilities
    supported_subjects: List[ContentSubject] = [ContentSubject.GENERAL]
    supported_difficulties: List[DifficultyLevel] = [DifficultyLevel.INTERMEDIATE]
    
    # Configuration
    max_execution_time: float = 5.0
    parameters: dict = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "The finish status of the interaction.",
                "enum": ["success", "failure"],
            }
        },
        "required": ["status"],
    }

    async def execute(self, status: str) -> str:
        """Finish the current execution"""
        return f"The interaction has been completed with status: {status}"