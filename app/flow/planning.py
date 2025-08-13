import json
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
from supabase import create_client, Client
from pydantic import Field
import uuid
import os
from dotenv import find_dotenv, load_dotenv

from app.agent.base import BaseAgent
from app.flow.base import BaseFlow
from app.llm import LLM
from app.logger import logger
from app.schema import AgentState, Message, ToolChoice
from app.tool import PlanningTool


load_dotenv(find_dotenv())

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class PlanningFlow(BaseFlow):
    """A flow that manages planning and execution of tasks using agents."""

    llm: LLM = Field(default_factory=lambda: LLM())
    planning_tool: PlanningTool = Field(default_factory=PlanningTool)
    executor_keys: List[str] = Field(default_factory=list)
    active_plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4()}")
    current_step_index: Optional[int] = None
    session_id: Optional[str] = None
    supabase: Optional[Client] = Field(default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None)

    def __init__(
        self, agents: Union[BaseAgent, List[BaseAgent], Dict[str, BaseAgent]], **data
    ):
        if "executors" in data:
            data["executor_keys"] = data.pop("executors")

        if "plan_id" in data:
            data["active_plan_id"] = data.pop("plan_id")

        if "session_id" in data:
            session_id = data.pop("session_id")
            data["session_id"] = session_id

        if "planning_tool" not in data:
            data["planning_tool"] = PlanningTool()

        super().__init__(agents, **data)

        if not self.executor_keys and isinstance(self.agents, dict):
            self.executor_keys = list(self.agents.keys())


    def get_executor(self, step_type: Optional[str] = None) -> BaseAgent:
        if not self.agents:
            raise ValueError("No agents available")
        
        # Check if we have a session_id to track tool usage
        if hasattr(self, 'session_id') and self.session_id and self.supabase:
            import random
            
            try:
                # Get the last used tool from the database
                response = self.supabase.table("Lessons").select("step_responses").eq("session_id", self.session_id).execute()
                
                if response.data and len(response.data) > 0:
                    step_responses = response.data[0].get("step_responses", [])
                    
                    # Find the last completed step
                    last_tool_type = None
                    for step in reversed(step_responses):
                        if step.get("status") == "finished" and "content" in step:
                            content = step.get("content", {})
                            if "tool_type" in content:
                                last_tool_type = content.get("tool_type")
                                break
                    
                    # If we found the last tool type and it matches the current step_type
                    if last_tool_type and step_type and last_tool_type == step_type:
                        logger.info(f"Same tool requested consecutively: {step_type}")
                        
                        # 50% chance to choose a different tool
                        if random.random() < 0.5:
                            logger.info(f"Randomizing tool selection instead of using {step_type} again")
                            
                            # Get all available tools except the last used one
                            available_tools = [key for key in self.executor_keys if key != step_type and key in self.agents]
                            
                            if available_tools:
                                # Choose a random alternative tool
                                alternative_step_type = random.choice(available_tools)
                                logger.info(f"Chose alternative tool: {alternative_step_type}")
                                return self.agents[alternative_step_type]
            
            except Exception as e:
                logger.error(f"Error checking last tool usage: {e}")
                # Continue with normal tool selection if check fails
        
        # Normal tool selection logic
        if step_type and step_type in self.agents:
            return self.agents[step_type]
        
        for key in self.executor_keys:
            if key in self.agents:
                return self.agents[key]
        
        return self.primary_agent or list(self.agents.values())[0]

    async def execute(self, input_text: str, session_id: str) -> str:
        try:
            if not self.primary_agent:
                raise ValueError("No primary agent available")

            

            self.session_id = session_id

            if not input_text:
                return "No input text provided"

            current_plan = await self._create_initial_plan(input_text)
            if not current_plan or not current_plan.tool_calls:
                logger.error("Plan creation failed - no tool calls returned")
                return f"Failed to create plan for: {input_text}"

            args = json.loads(current_plan.tool_calls[0].function.arguments)
            steps = args.get("steps", [])
            plan_data = {
                "session_id": session_id,
                "title": input_text,
                "steps": steps,
                "step_statuses": ["not_started"] * len(steps),
                "step_responses": [
                                    {   "step_index": i +1,
                                        "status": "not_started",
                                        "content": {"timestamp":None,
                                                    "type": None,
                                                    "content":""}
                                        
                                    } for i in range(len(steps))
                                    
                                ],
                "created_at": datetime.now().isoformat()
            }
            
            
            try:
                result = self.supabase.table("Lessons").insert(plan_data).execute()
                logger.info(f"Successfully inserted plan data: {result}")
            except Exception as e:
                logger.error(f"Error inserting data into Supabase: {e}")
                raise
                
            return f"Successfully created plan with {len(steps)} steps"
            
        except Exception as e:
            logger.error(f"Error in PlanningFlow.execute: {str(e)}")
            return f"Error creating plan: {str(e)}"

    async def _create_initial_plan(self, request: str) -> Optional[AgentState]:
        logger.info(f"Creating initial plan with ID: {self.active_plan_id}")

        system_message = Message.system_message(
            """You are Tegus's planning assistant. Create a concise but thorough actionable plan with clear steps
            Focus on separating topics covered in the lesson
            Focus on key milestones and cover topics not key definitions"""
        )

        user_message = Message.user_message(
            f"Create a reasonable plan with clear steps to accomplish the task: {request}"
        )

        response = await self.llm.ask_tool(
            messages=[user_message],
            system_msgs=[system_message],
            tools=[self.planning_tool.to_param()],
            tool_choice=ToolChoice.AUTO,
        )

        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.function.name == "planning":
                    args = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                    args["plan_id"] = self.active_plan_id
                    await self.planning_tool.execute(**args)
                    return response

        logger.warning("Creating default plan")
        default_response = await self.planning_tool.execute(
            command="create",
            plan_id=self.active_plan_id,
            title=f"Plan for: {request[:50]}{'...' if len(request) > 50 else ''}",
            steps=["Analyze request", "Execute task", "Verify results"]
        )
        return default_response

    async def _get_current_step_info(self, session_id: str, step_id:int) -> Tuple[Optional[int], Optional[dict]]:
        

        try:
            response = self.supabase.table("Lessons").select("*").eq("session_id", session_id).execute()
            if not response.data:
                logger.error(f"No lesson found for session_id: {session_id}")
                return None, None
                
            lesson_data = response.data[0]
            steps = lesson_data.get("steps", [])
            step_statuses = lesson_data.get("step_statuses", [])
            
            
            step_info = {"text": steps[step_id]}
            step_lower = step_info.get("text",[]).lower()
            
            if "define" in step_lower:
                step_info["type"] = "definition"
            elif "research" in step_lower:
                step_info["type"] = "research"
            elif "gather" in step_lower:
                step_info["type"] = "gather"
            elif "analyze" in step_lower:
                step_info["type"] = "analysis"
            elif "create" in step_lower:
                step_info["type"] = "summary"
            else:
                step_info["type"] = "general"
            
            step_statuses[step_id] = "in_progress"
            try:
                self.supabase.table("Lessons").update({"step_statuses": step_statuses}).eq("session_id", session_id).execute()
                # Modern Supabase client doesn't have .error attribute
                # Instead, it raises exceptions on errors
            except Exception as update_error:
                logger.error(f"Error updating step status: {update_error}")
                
            return step_id, step_info
                    
            
        except Exception as e:
            logger.error(f"Error finding current step index: {e}")
            return None, None

    async def _execute_step(self, executor: BaseAgent, session_id: str, step_id:int) -> str:
        self.session_id = session_id
        current_step_index, step_info = await self._get_current_step_info(session_id, step_id)
        if current_step_index is None or step_info is None:
            return "No active steps remaining"
            
        self.current_step_index = current_step_index
        step_text = step_info["text"]
        step_type = step_info["type"]
        
        # Get the appropriate executor for this step type
        executor = self.get_executor(step_type)
        
        # Store the current step index in the executor for tools to access
        executor.current_step_index = current_step_index
        executor.session_id = session_id
        
        plan_status = await self._get_plan_text(self.session_id)
        
        step_prompt = f"""
        CURRENT PLAN STATUS:
        {plan_status}

        YOUR CURRENT TASK:
        You are now working on step {current_step_index}: "{step_text}"
        Here is also the session_id: {session_id}

        Please execute this step using the appropriate tools. When you're done, provide a summary of what you accomplished.
        """
        
        try:
            # Check the agent's state before running
            initial_state = executor.state
            
            # Run the step
            step_result = await executor.run(step_prompt)
            
            # Check if the agent's state changed to FINISHED (terminate was called)
            if executor.state != initial_state and executor.state == AgentState.FINISHED:
                logger.info("Agent state changed to FINISHED - terminate tool was used")
                await self._mark_step_completed()
                
                # Mark all remaining steps as skipped
                try:
                    response = self.supabase.table("Lessons").select("step_statuses").eq("session_id", session_id).execute()
                    if response.data and len(response.data) > 0:
                        step_statuses = response.data[0].get("step_statuses", [])
                        
                        # Mark all remaining steps as skipped
                        for i in range(current_step_index + 1, len(step_statuses)):
                            step_statuses[i] = "skipped"
                        
                        # Update the database
                        self.supabase.table("Lessons").update({
                            "step_statuses": step_statuses
                        }).eq("session_id", session_id).execute()
                except Exception as e:
                    logger.error(f"Error updating remaining steps as skipped: {e}")
                
                return "Execution terminated by agent."
            
            # Also check the result string for "terminate" as a fallback
            if isinstance(step_result, str) and "terminate" in step_result.lower():
                await self._mark_step_completed()
                logger.info("Terminate tool was used (detected in result string). Ending execution.")
                return "Execution terminated."

            # Format the output based on the tool used
            formatted_result = await self._format_step_output(step_result, step_type)
            
            # Only store RagSearch outputs in the database
            if isinstance(step_result, list) and any("rag_search" in str(item).lower() for item in step_result):
                await self._store_step_result(current_step_index, formatted_result, "finished")
            
            await self._mark_step_completed()
            return formatted_result
        except Exception as e:
            logger.error(f"Error executing step {current_step_index}: {e}")
            return f"Error executing step {current_step_index}: {str(e)}"

    async def _store_step_result(self, step_index: int, content: str, status: str) -> None:
        """Store the RagSearch result in the database with proper formatting."""
        try:
            response = self.supabase.table("Lessons").select("step_responses").eq("session_id", self.session_id).execute()
            if response.data:
                step_responses = response.data[0].get("step_responses", [])
                if step_index < len(step_responses):
                    step_responses[step_index].update({
                        "status": status,
                        "content": {
                            "timestamp": int(datetime.now().timestamp()),
                            "content": content
                        }
                    })
                    self.supabase.table("Lessons").update({
                        "step_responses": step_responses
                    }).eq("session_id", self.session_id).execute()
        except Exception as e:
            logger.error(f"Failed to store RagSearch result: {e}")

    async def _mark_step_completed(self) -> None:

        try:
            response = self.supabase.table("Lessons").select("*").eq("session_id", self.session_id).execute()
            if not response.data:
                logger.error(f"No lesson found for session_id: {self.session_id}")
                return
                
            lesson_data = response.data[0]
            step_statuses = lesson_data.get("step_statuses", [])
            #step_responses = lesson_data.get("step_responses", [])
            
            if self.current_step_index >= len(step_statuses):
                logger.error(f"Invalid step index: {self.current_step_index}")
                return
                
            step_statuses[self.current_step_index] = "finished"
            
            #last_response = self.primary_agent.memory.messages[-1].content if self.primary_agent.memory.messages else ""
            #step_responses[self.current_step_index] = last_response
            
            self.supabase.table("Lessons").update({
                "step_statuses": step_statuses
            }).eq("session_id", self.session_id).execute()
            
            logger.info(f"Marked step {self.current_step_index} as finished")
            
        except Exception as e:
            logger.error(f"Failed to update step status: {e}")
            raise

    async def _get_plan_text(self,session_id:str) -> str:

        try:
            response = self.supabase.table("Lessons").select("*").eq("session_id", session_id).execute()
            if not response.data:
                return "No lesson found"
                
            lesson_data = response.data[0]
            title = lesson_data.get("title", "Untitled Plan")
            steps = lesson_data.get("steps", [])
            step_statuses = lesson_data.get("step_statuses", [])
            
            status_counts = {"finished": 0, "in_progress": 0, "not_started": 0}
            for status in step_statuses:
                status_counts[status] = status_counts.get(status, 0) + 1
            
            completed = status_counts["finished"]
            total = len(steps)
            progress = (completed / total) * 100 if total > 0 else 0
            
            plan_text = f"Plan: {title}\n" + "=" * len(f"Plan: {title}") + "\n\n"
            plan_text += f"Progress: {completed}/{total} steps completed ({progress:.1f}%)\n"
            plan_text += f"Status: {status_counts['finished']} finished, {status_counts['in_progress']} in progress, {status_counts['not_started']} not started\n\n"
            plan_text += "Steps:\n"
            
            for i, (step, status) in enumerate(zip(steps, step_statuses)):
                status_mark = "✓" if status == "finished" else "→" if status == "in_progress" else "○"
                plan_text += f"{i}. {status_mark} {step}\n"
            
            return plan_text
            
        except Exception as e:
            logger.error(f"Error getting plan text: {e}")
            return f"Error retrieving plan: {str(e)}"

    async def _finalize_plan(self) -> str:

        plan_text = await self._get_plan_text(self.session_id)
        
        try:
            system_message = Message.system_message(
                """You are Tegus's planning assistant summarizer. Your job is to make a summary of all the things Tegus has found and thought of."""
            )
            user_message = Message.user_message(
                f"The plan has been completed. Here is the final plan status:\n\n{plan_text}\n\nPlease provide your final report on the content. Make a thorough and well-thought-out summary."
            )
            
            response = await self.llm.ask(
                messages=[user_message],
                system_msgs=[system_message]
            )
            return f"Plan completed:\n\n{response}"
        except Exception as e:
            logger.error(f"Error finalizing plan with LLM: {e}")
            try:
                summary_prompt = f"""
                The plan has been completed. Here is the final plan status:

                {plan_text}

                Please provide a summary of what was accomplished and any final thoughts.
                """
                summary = await self.primary_agent.run(summary_prompt)
                return f"Plan completed:\n\n{summary}"
            except Exception as e2:
                logger.error(f"Error finalizing plan with agent: {e2}")
                return "Plan completed. Error generating summary."
    
