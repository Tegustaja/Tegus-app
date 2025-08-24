"""
Tool Template
This is a comprehensive template for creating new standardized tools.
Copy this file and modify it according to your needs.
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import Field

from app.tool.base import (
    BaseTool, 
    ToolType, 
    ExerciseType, 
    DifficultyLevel, 
    ContentSubject,
    ExerciseInput,
    ExerciseOutput,
    AssessmentInput,
    AssessmentOutput,
    ContentInput,
    ContentOutput,
    StandardizedToolResult
)

# ============================================================================
# TEMPLATE: NEW TOOL CLASS
# ============================================================================

class TemplateTool(BaseTool):
    """
    Template for creating new standardized tools.
    
    This template demonstrates:
    1. Proper tool configuration
    2. Input validation
    3. Output standardization
    4. Error handling
    5. Database integration
    6. Logging and monitoring
    """
    
    # ========================================================================
    # TOOL CONFIGURATION
    # ========================================================================
    
    # Basic identification
    name: str = "template_tool"
    description: str = "Template tool for educational purposes"
    tool_type: ToolType = ToolType.EXERCISE  # Choose appropriate type
    version: str = "1.0.0"
    
    # Tool capabilities
    supported_subjects: List[ContentSubject] = [
        ContentSubject.MATH,
        ContentSubject.PHYSICS,
        ContentSubject.GENERAL
    ]
    supported_difficulties: List[DifficultyLevel] = [
        DifficultyLevel.BEGINNER,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED
    ]
    
    # Configuration
    max_execution_time: float = 30.0
    
    # Tool parameters schema (for function calling)
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Main query or input for the tool",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID this step belongs to",
            },
            "step_index": {
                "type": "integer",
                "description": "Current step index (0-based)",
            },
            "subject": {
                "type": "string",
                "enum": ["mathematics", "physics", "chemistry", "biology", "history", "language", "computer_science", "general"],
                "description": "Subject category",
            },
            "difficulty": {
                "type": "string",
                "enum": ["beginner", "intermediate", "advanced"],
                "description": "Difficulty level",
            },
            "topic": {
                "type": "string",
                "description": "Specific topic within subject",
            },
            "custom_prompt": {
                "type": "string",
                "description": "Custom instructions or prompts",
            }
        },
        "required": ["query", "session_id", "step_index"],
    }
    
    # ========================================================================
    # DEPENDENCIES AND EXTERNAL SERVICES
    # ========================================================================
    
    # Add your external service clients here
    # Example:
    # openai_client: Optional[OpenAI] = Field(default_factory=lambda: OpenAI() if os.getenv("OPENAI_API_KEY") else None)
    # supabase_client: Optional[Client] = Field(default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None)
    
    # ========================================================================
    # INPUT VALIDATION
    # ========================================================================
    
    def _validate_input(self, kwargs: dict) -> ExerciseInput:  # Change to appropriate input type
        """
        Validate and convert input to appropriate input model.
        
        Choose the appropriate input type:
        - ExerciseInput: For exercise generation tools
        - AssessmentInput: For assessment/evaluation tools
        - ContentInput: For content generation tools
        - BaseToolInput: For utility tools
        """
        
        # Extract required fields
        session_id = kwargs.get("session_id")
        step_index = kwargs.get("step_index")
        query = kwargs.get("query")
        
        # Validate required fields
        if not all([session_id, step_index is not None, query]):
            raise ValueError("Missing required parameters: session_id, step_index, query")
        
        # Create appropriate input model
        return ExerciseInput(  # Change to appropriate input type
            session_id=session_id,
            step_index=step_index,
            query=query,
            subject=ContentSubject(kwargs.get("subject", "general")),
            difficulty=DifficultyLevel(kwargs.get("difficulty", "intermediate")),
            topic=kwargs.get("topic"),
            user_id=kwargs.get("user_id"),
            custom_prompt=kwargs.get("custom_prompt")
        )
    
    # ========================================================================
    # MAIN EXECUTION LOGIC
    # ========================================================================
    
    async def execute(self, input_data: ExerciseInput) -> ExerciseOutput:  # Change to appropriate output type
        """
        Execute the tool with validated input data.
        
        This is the main method where your tool logic goes.
        It should:
        1. Process the input data
        2. Perform the main operation
        3. Return standardized output
        4. Handle errors gracefully
        """
        
        # Generate unique ID for this execution
        execution_id = str(uuid.uuid4())
        
        try:
            # ====================================================================
            # MAIN TOOL LOGIC GOES HERE
            # ====================================================================
            
            # Example: Process the query
            processed_result = await self._process_query(input_data.query)
            
            # Example: Generate exercise content
            exercise_content = await self._generate_exercise_content(
                input_data, 
                processed_result
            )
            
            # ====================================================================
            # CREATE STANDARDIZED OUTPUT
            # ====================================================================
            
            # Choose appropriate output type based on your tool
            return ExerciseOutput(  # Change to appropriate output type
                exercise_id=execution_id,
                exercise_type=ExerciseType.MULTIPLE_CHOICE,  # Adjust as needed
                question=exercise_content["question"],
                options=exercise_content["options"],
                correct_answer=exercise_content["correct_answer"],
                explanation=exercise_content.get("explanation"),
                difficulty=input_data.difficulty,
                subject=input_data.subject,
                topic=input_data.topic,
                metadata={
                    "source": "template_tool",
                    "query": input_data.query,
                    "generation_method": "template_generation",
                    "execution_id": execution_id
                }
            )
            
        except Exception as e:
            # Return fallback output if everything fails
            return ExerciseOutput(  # Change to appropriate output type
                exercise_id=execution_id,
                exercise_type=ExerciseType.MULTIPLE_CHOICE,
                question=f"Fallback exercise based on: {input_data.query}",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer="Option A",
                explanation="This is a fallback exercise generated when the tool execution failed.",
                difficulty=input_data.difficulty,
                subject=input_data.subject,
                topic=input_data.topic,
                metadata={
                    "source": "fallback_generation",
                    "error": str(e),
                    "query": input_data.query,
                    "execution_id": execution_id
                }
            )
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _process_query(self, query: str) -> Dict[str, Any]:
        """
        Process the input query.
        
        This is where you implement your specific query processing logic.
        """
        # Example implementation
        return {
            "processed_query": query.lower().strip(),
            "query_length": len(query),
            "has_keywords": any(keyword in query.lower() for keyword in ["math", "physics", "calculate"])
        }
    
    async def _generate_exercise_content(self, input_data: ExerciseInput, processed_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate exercise content based on processed input.
        
        This is where you implement your specific content generation logic.
        """
        # Example implementation
        return {
            "question": f"Based on the query '{input_data.query}', create a {input_data.difficulty.value} level exercise.",
            "options": [
                "Option A: First option",
                "Option B: Second option",
                "Option C: Third option",
                "Option D: Fourth option"
            ],
            "correct_answer": "Option A: First option",
            "explanation": f"This exercise was generated for {input_data.subject.value} at {input_data.difficulty.value} level."
        }
    
    # ========================================================================
    # DATABASE INTEGRATION (OPTIONAL)
    # ========================================================================
    
    async def store_result(self, input_data: ExerciseInput, output: ExerciseOutput) -> bool:
        """
        Store the tool result in the database.
        
        This is optional but recommended for tracking and analytics.
        """
        try:
            # Example database storage
            # if self.supabase_client:
            #     result = self.supabase_client.table("tool_results").insert({
            #         "session_id": input_data.session_id,
            #         "step_index": input_data.step_index,
            #         "tool_name": self.name,
            #         "input_data": input_data.dict(),
            #         "output_data": output.dict(),
            #         "created_at": datetime.utcnow().isoformat()
            #     }).execute()
            #     return result.data is not None
            
            # For now, just return True (simulated success)
            return True
            
        except Exception as e:
            print(f"Error storing tool result: {e}")
            return False
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get comprehensive information about this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tool_type": self.tool_type.value,
            "supported_subjects": [s.value for s in self.supported_subjects],
            "supported_difficulties": [d.value for d in self.supported_difficulties],
            "max_execution_time": self.max_execution_time,
            "parameters": self.parameters
        }
    
    def validate_capabilities(self, subject: ContentSubject, difficulty: DifficultyLevel) -> bool:
        """Check if this tool supports the given subject and difficulty."""
        return (
            subject in self.supported_subjects and 
            difficulty in self.supported_difficulties
        )

# ============================================================================
# TEMPLATE: ASSESSMENT TOOL
# ============================================================================

class TemplateAssessmentTool(BaseTool):
    """Template for assessment tools (e.g., checking answers, evaluating responses)"""
    
    name: str = "template_assessment_tool"
    description: str = "Template assessment tool for educational purposes"
    tool_type: ToolType = ToolType.ASSESSMENT
    version: str = "1.0.0"
    
    supported_subjects: List[ContentSubject] = [ContentSubject.GENERAL]
    supported_difficulties: List[DifficultyLevel] = [DifficultyLevel.INTERMEDIATE]
    max_execution_time: float = 20.0
    
    parameters: dict = {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Question to assess"},
            "user_answer": {"type": "string", "description": "User's answer to assess"},
            "session_id": {"type": "string", "description": "Session ID"},
            "step_index": {"type": "integer", "description": "Step index"},
        },
        "required": ["question", "user_answer", "session_id", "step_index"],
    }
    
    def _validate_input(self, kwargs: dict) -> AssessmentInput:
        """Validate input for assessment tools."""
        return AssessmentInput(
            question=kwargs["question"],
            user_answer=kwargs["user_answer"],
            session_id=kwargs["session_id"],
            step_index=kwargs["step_index"]
        )
    
    async def execute(self, input_data: AssessmentInput) -> AssessmentOutput:
        """Execute assessment logic."""
        assessment_id = str(uuid.uuid4())
        
        # Example assessment logic
        is_correct = input_data.user_answer.lower().strip() == "correct answer"
        score = 1.0 if is_correct else 0.0
        
        return AssessmentOutput(
            assessment_id=assessment_id,
            question=input_data.question,
            user_answer=input_data.user_answer,
            is_correct=is_correct,
            score=score,
            feedback="This is template feedback. Implement your assessment logic here.",
            correct_answer="correct answer",
            explanation="This is a template explanation."
        )

# ============================================================================
# TEMPLATE: CONTENT GENERATION TOOL
# ============================================================================

class TemplateContentTool(BaseTool):
    """Template for content generation tools (e.g., explanations, summaries)"""
    
    name: str = "template_content_tool"
    description: str = "Template content generation tool for educational purposes"
    tool_type: ToolType = ToolType.CONTENT
    version: str = "1.0.0"
    
    supported_subjects: List[ContentSubject] = [ContentSubject.GENERAL]
    supported_difficulties: List[DifficultyLevel] = [DifficultyLevel.INTERMEDIATE]
    max_execution_time: float = 25.0
    
    parameters: dict = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Content generation prompt"},
            "content_type": {"type": "string", "description": "Type of content to generate"},
            "session_id": {"type": "string", "description": "Session ID"},
            "step_index": {"type": "integer", "description": "Step index"},
        },
        "required": ["prompt", "content_type", "session_id", "step_index"],
    }
    
    def _validate_input(self, kwargs: dict) -> ContentInput:
        """Validate input for content tools."""
        return ContentInput(
            prompt=kwargs["prompt"],
            content_type=kwargs["content_type"],
            session_id=kwargs["session_id"],
            step_index=kwargs["step_index"]
        )
    
    async def execute(self, input_data: ContentInput) -> ContentOutput:
        """Execute content generation logic."""
        content_id = str(uuid.uuid4())
        
        # Example content generation
        generated_content = f"Generated content based on prompt: {input_data.prompt}"
        
        return ContentOutput(
            content_id=content_id,
            content=generated_content,
            content_type=input_data.content_type,
            format="text",
            metadata={"prompt": input_data.prompt}
        )

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_usage():
    """Example of how to use the template tools."""
    
    # Create tool instances
    exercise_tool = TemplateTool()
    assessment_tool = TemplateAssessmentTool()
    content_tool = TemplateContentTool()
    
    # Example input data
    exercise_input = {
        "query": "Create a math exercise about algebra",
        "session_id": str(uuid.uuid4()),
        "step_index": 0,
        "subject": "mathematics",
        "difficulty": "intermediate"
    }
    
    # Execute tools
    exercise_result = await exercise_tool(**exercise_input)
    print(f"Exercise tool result: {exercise_result.success}")
    
    # Get tool information
    tool_info = exercise_tool.get_tool_info()
    print(f"Tool info: {tool_info}")

if __name__ == "__main__":
    asyncio.run(example_usage())
