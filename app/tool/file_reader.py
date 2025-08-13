import os

import aiofiles

from app.tool.base import BaseTool


class FileReader(BaseTool):
    name: str = "file_reader"
    description: str = """Read content from a specified path
Use this tool when you need to read text, code, or generated content from a file on the local filesystem.
The tool accepts a file path, and returns the content of the file.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "(required) The file path content is being read from, including filename and extension.",
            },
            "mode": {
                "type": "string",
                "description": "(optional) The file opening mode. Default is 'r'.",
                "enum": ["r"],
                "default": "r",
            },
        },
        "required": ["file_path"],
    }

    async def execute(self, file_path: str, mode: str = "r") -> str:
        """
        Read content from a pecified file path.

        Args:
            file_path (str): The path where the content is read from
            mode (str, optional): The file opening mode. Default is 'r'

        Returns:
            str: File contents
        """
        try:
            # Ensure the directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                # Write directly to the file
                async with aiofiles.open(directory, mode, encoding="utf-8") as file:
                    return f"Content extracted: \n {await file.read()}"

            
        except Exception as e:
            return f"Error saving file: {str(e)}"
