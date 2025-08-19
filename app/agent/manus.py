from typing import Any
from datetime import datetime

from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.tool import Terminate, ToolCollection
from app.tool.rag_model import RagSearch
from app.tool.check_solution import CheckSolution
from app.tool.multiple_choise_exercise import MultipleChoiceExercise
from app.tool.true_false_exercise import TrueFalseExercise
from app.tool.calculation_exercise import CalculationExercise




class Manus(ToolCallAgent):
    """
    A versatile general-purpose agent that uses planning to solve various tasks.

    This agent extends PlanningAgent with a comprehensive set of tools and capabilities,
    including Python execution, web browsing, file operations, and information retrieval
    to handle a wide range of user requests.
    """

    name: str = "Manus"
    description: str = (
        "A versatile agent that can solve various tasks using multiple tools"
    )

    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = 2000
    max_steps: int = 7

    # Add general-purpose tools to the tool collection
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            Terminate(), RagSearch(), CheckSolution(), MultipleChoiceExercise(), TrueFalseExercise(), CalculationExercise()
        )
    )

    async def _handle_special_tool(self, name: str, result: Any, **kwargs):
        if not self._is_special_tool(name):
            return
        else:
            await super()._handle_special_tool(name, result, **kwargs)

    async def _handle_terminate_tool(self, step_responses=None, session_id=None, status="success"):
        # Handle case when terminate is called early (before steps are finished)
        if step_responses is None or session_id is None:
            print("Terminate called before steps were completed - no database update needed")
            return
            
        # Update the database with only step_responses
        update_data = {
            "step_responses": step_responses,
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            self.supabase.table("Lessons").update(update_data).eq("session_id", session_id).execute()
            # Modern Supabase client doesn't have .error attribute
            # Instead, it raises exceptions on errors
        except Exception as update_error:
            print(f"Error updating database in terminate tool: {update_error}")
