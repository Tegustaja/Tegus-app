import os

import aiofiles
import glob
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv


from app.tool.base import BaseTool
from app.tool.file_reader import FileReader

load_dotenv(find_dotenv())
SUMMARIZER_PROMPT = """You are an asisstant who loves to make summaries of stuff. You wil be given a list that has all the content to be summarized. Make sure you do not lose any important information about the content given."""
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class Summarizer(BaseTool):
    name: str = "Summarizer"
    description: str = """Make a summary of all content generated in files."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "parent_path": {
                "type": "string",
                "description": "(required) The parent directory, where all session generated content is saved.",
            },
        },
        "required": ["parent_path"],
    }        
    async def execute(self, parent_path: str, mode:str = "r", **kwargs) -> list:
        try: 
            file_paths = glob.glob(parent_path)
            content = []
            for i in file_paths:
                path = f"{i}*"
                async with aiofiles.open(path, mode, encoding="utf-8") as file:
                    content.append(await file.read())
        
            client = OpenAI()
            completion = client.chat.completions.create(
            model="gpt-4o-mini",
            api_key = OPENAI_API_KEY,
            messages=[
                {"role": "summarizer", "content": SUMMARIZER_PROMPT},
                {"role": "user", "content": content}
            ]
            )
            return completion.choices[0].message   
        except Exception as e:
            return e     

