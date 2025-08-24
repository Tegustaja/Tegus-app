# app.py (or main.py)
import json
import time
from typing import Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client, Client
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv, find_dotenv


from app.agent.base import BaseAgent
from app.flow.base import BaseFlow
from app.llm import LLM
from app.logger import logger
from app.schema import Message, ToolChoice
from app.tool import PlanningTool

# Supabase configuration (best stored in environment variables in production)


load_dotenv(find_dotenv())

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# FastAPI app

# Pydantic model for request validation


# PlanningFlow class (from previous response)
class PlanningFlow(BaseFlow):
    llm: LLM = Field(default_factory=lambda: LLM())
    planning_tool: PlanningTool = Field(default_factory=PlanningTool)
    supabase: Optional[Client] = Field(default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None)
    
    def __init__(self, agents: Union[BaseAgent, List[BaseAgent], Dict[str, BaseAgent]], **data):
        super().__init__(agents, **data)
        self._primary_agent = list(self.agents.values())[0] if isinstance(self.agents, dict) else self.agents if isinstance(self.agents, BaseAgent) else self.agents[0]

    async def execute(self, input_text: str) -> str:
        """Implement the abstract execute method from BaseFlow."""
        try:
            session_id = str(uuid.uuid4())  # Generate UUID
            plan_text = await self.create_and_store_plan(input_text, session_id)
            step_result = await self.execute_next_step(session_id)
            return f"{plan_text}\nFirst step result: {step_result}"
        except Exception as e:
            logger.error(f"Error in execute: {str(e)}")
            return f"Error: {str(e)}"
    def get_executor(self, step_type: Optional[str] = None) -> BaseAgent:
        """
        Get an appropriate executor agent for the current step.
        Can be extended to select agents based on step type/requirements.
        """
        # If step type is provided and matches an agent key, use that agent
        if step_type and step_type in self.agents:
            return self.agents[step_type]

        # Otherwise use the first available executor or fall back to primary agent
        for key in self.executor_keys:
            if key in self.agents:
                return self.agents[key]

        # Fallback to primary agent
        return self.primary_agent
    async def _execute_step(self, executor: BaseAgent, step_info: dict) -> str:
        """Execute the current step with the specified agent using agent.run()."""
        # Prepare context for the agent with current plan status
        plan_status = await self._get_plan_text()
        step_text = step_info.get("text", f"Step {self.current_step_index}")

        # Create a prompt for the agent to execute the current step
        step_prompt = f"""
        CURRENT PLAN STATUS:
        {plan_status}

        YOUR CURRENT TASK:
        You are now working on step {self.current_step_index}: "{step_text}"

        Please execute this step using the appropriate tools. When you're done, provide a summary of what you accomplished.
        """

        # Use agent.run() to execute the step
        try:
            step_result = await executor.run(step_prompt)

            # Mark the step as completed after successful execution
            await self._mark_step_completed()

            return step_result
        except Exception as e:
            logger.error(f"Error executing step {self.current_step_index}: {e}")
            return f"Error executing step {self.current_step_index}: {str(e)}"

    async def create_and_store_plan(self, prompt: str, session_id: str) -> str:
        try:
                    # Get the complete planning prompt from the database
        try:
            from app.services.prompt_service import get_prompt_service
            prompt_service = get_prompt_service()
            system_prompt = await prompt_service.get_combined_prompt("planning")
            
            if not system_prompt:
                # Fallback to default if database prompt not found
                system_prompt = """Oled Teguse planeerimisassistent. Koosta lühike, kuid põhjalik teostatav plaan selge sammudega.
                Fokusseeri õppetundis käsitletud teemadele
                Fokusseeri põhilistele verstapostidele ja katke teemad, mitte põhilisi definitsioone"""
        except Exception as e:
            logger.warning(f"Failed to fetch planning prompt from database: {e}")
            # Fallback to default
            system_prompt = """Oled Teguse planeerimisassistent. Koosta lühike, kuid põhjalik teostatav plaan selge sammudega.
            Fokusseeri õppetundis käsitletud teemadele
            Fokusseeri põhilistele verstapostidele ja katke teemad, mitte põhilisi definitsioone"""

        system_message = Message.system_message(system_prompt)
                    response = await self.llm.ask_tool(
            messages=[],
            system_msgs=[system_message],
            tools=[self.planning_tool.to_param()],
            tool_choice=ToolChoice.AUTO,
        )

            if response.tool_calls and response.tool_calls[0].function.name == "planning":
                args = json.loads(response.tool_calls[0].function.arguments)
                steps = args.get("steps", [])
                plan_title = args.get("title", f"Plan for: {prompt[:50]}")
            else:
                steps = ["Analyze request", "Execute task", "Verify results"]
                plan_title = f"Plan for: {prompt[:50]}"

            plan_data = {
                "session_id": session_id,
                "title": plan_title,
                "steps": steps,
                "step_statuses": ["not_started"] * len(steps),
                "step_responses": [""] * len(steps),
                "created_at": datetime.fromtimestamp(time.time()).isoformat()
            }

            if self.supabase:
                self.supabase.table("Lessons").insert(plan_data).execute()
            return self._format_plan(plan_data)

        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating plan: {str(e)}")

    async def execute_next_step(self, session_id: str) -> str:
        try:
            response = self.supabase.table("Lessons").select("*").eq("session_id", session_id).execute()
            if not response.data or len(response.data) == 0:
                raise HTTPException(status_code=404, detail=f"No plan found for session_id: {session_id}")

            plan_data = response.data[0]
            print(plan_data)
            steps = plan_data["steps"]
            statuses = plan_data["step_statuses"]
            responses = plan_data["step_responses"]
            print(f"Steps: {steps}")
            print(f"satatuses: {statuses}")
            print(f"akjsfvbakj: {responses}")

            print("-------------")
            current_step_index = None
            for i, status in enumerate(statuses):
                if status == "not_started":
                    current_step_index = i
                    break
            print("jkbsfn")
            if current_step_index is None:
                return "All steps completed"

            step_text = steps[current_step_index]
            step_prompt = f"Execute this step: {step_text}"
            print(step_prompt)
            step_result = await self._primary_agent.run(step_prompt)
            print(step_result)
            statuses[current_step_index] = "completed"
            responses[current_step_index] = step_result

            update_data = {
                "step_statuses": statuses,
                "step_responses": responses,
                "updated_at": int(time.time())
            }
            print("**************************")
            self.supabase.table("Lessons").update(update_data).eq("session_id", session_id).execute()

            return step_result

        except Exception as e:
            logger.error(f"Error executing step: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error executing step: {str(e)}")

    def _format_plan(self, plan_data: dict) -> str:
        plan_text = f"Plan: {plan_data['title']} (Session ID: {plan_data['session_id']})\n"
        plan_text += "=" * len(plan_text) + "\n\n"
        plan_text += "Steps:\n"
        
        for i, (step, status) in enumerate(zip(plan_data["steps"], plan_data["step_statuses"])):
            status_mark = "✓" if status == "completed" else "□"
            plan_text += f"{i}. {status_mark} {step}\n"
        
        return plan_text

# Initialize flow with a dummy agent (replace with your actual agent implementation)
