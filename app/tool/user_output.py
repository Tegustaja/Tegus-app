from app.tool.base import BaseTool


class OutputUser(BaseTool):
    name: str = "output_user"
    description: str = """Output content to the user. Output to user without including your own thoughts, only output text you want the user to see. Remove all unnecessary content from the output."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "(required) The output given to the user.",
            },
        },
        "required": ["output"],
    }

    async def execute(self, content:str, **kwargs) -> str:
        OKGREEN = '\033[92m'
        ENDC = '\033[0m'
        print(OKGREEN + content + ENDC)
        return 