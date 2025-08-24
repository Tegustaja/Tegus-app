from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid

# ============================================================================
# ENUMS FOR STANDARDIZED VALUES
# ============================================================================

class ToolType(str, Enum):
    """Standardized tool types for categorization"""
    EXERCISE = "exercise"
    ASSESSMENT = "assessment"
    CONTENT = "content"
    INTERACTION = "interaction"
    UTILITY = "utility"

class ExerciseType(str, Enum):
    """Standardized exercise types"""
    MULTIPLE_CHOICE = "multiple_choice"
    CALCULATION = "calculation"
    TRUE_FALSE = "true_false"
    OPEN_ENDED = "open_ended"
    MATCHING = "matching"
    FILL_BLANK = "fill_blank"

class DifficultyLevel(str, Enum):
    """Standardized difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ContentSubject(str, Enum):
    """Standardized subject categories"""
    MATH = "mathematics"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    LANGUAGE = "language"
    COMPUTER_SCIENCE = "computer_science"
    GENERAL = "general"

# ============================================================================
# STANDARDIZED INPUT MODELS
# ============================================================================

class BaseToolInput(BaseModel):
    """Base input model for all tools"""
    session_id: str = Field(..., description="Unique session identifier")
    step_index: int = Field(..., description="Current step index (0-based)")
    user_id: Optional[str] = Field(None, description="User identifier if available")
    
    @validator('session_id')
    def validate_session_id(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('session_id must be a valid UUID')
    
    @validator('step_index')
    def validate_step_index(cls, v):
        if v < 0:
            raise ValueError('step_index must be non-negative')
        return v

class ExerciseInput(BaseToolInput):
    """Standardized input for exercise tools"""
    query: str = Field(..., description="Exercise query or description")
    subject: ContentSubject = Field(ContentSubject.GENERAL, description="Subject category")
    difficulty: DifficultyLevel = Field(DifficultyLevel.INTERMEDIATE, description="Difficulty level")
    topic: Optional[str] = Field(None, description="Specific topic within subject")
    custom_prompt: Optional[str] = Field(None, description="Custom instructions for exercise generation")

class AssessmentInput(BaseToolInput):
    """Standardized input for assessment tools"""
    question: str = Field(..., description="Question or exercise to assess")
    expected_answer: Optional[str] = Field(None, description="Expected correct answer if known")
    context: Optional[str] = Field(None, description="Additional context for assessment")

class ContentInput(BaseToolInput):
    """Standardized input for content generation tools"""
    prompt: str = Field(..., description="Content generation prompt")
    content_type: str = Field(..., description="Type of content to generate")
    format: Optional[str] = Field("text", description="Output format preference")

# ============================================================================
# STANDARDIZED OUTPUT MODELS
# ============================================================================

class ExerciseOutput(BaseModel):
    """Standardized output for exercise tools"""
    exercise_id: str = Field(..., description="Unique exercise identifier")
    exercise_type: ExerciseType = Field(..., description="Type of exercise")
    question: str = Field(..., description="The exercise question")
    options: Optional[List[str]] = Field(None, description="Answer options for multiple choice")
    correct_answer: Optional[str] = Field(None, description="Correct answer")
    explanation: Optional[str] = Field(None, description="Explanation of the answer")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    subject: ContentSubject = Field(..., description="Subject category")
    topic: Optional[str] = Field(None, description="Specific topic")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class AssessmentOutput(BaseModel):
    """Standardized output for assessment tools"""
    assessment_id: str = Field(..., description="Unique assessment identifier")
    question: str = Field(..., description="The assessed question")
    user_answer: str = Field(..., description="User's provided answer")
    is_correct: bool = Field(..., description="Whether the answer is correct")
    score: float = Field(..., description="Numerical score (0.0 to 1.0)")
    feedback: str = Field(..., description="Detailed feedback for the user")
    correct_answer: Optional[str] = Field(None, description="Correct answer if available")
    explanation: Optional[str] = Field(None, description="Explanation of the correct answer")
    suggestions: Optional[List[str]] = Field(None, description="Suggestions for improvement")

class ContentOutput(BaseModel):
    """Standardized output for content generation tools"""
    content_id: str = Field(..., description="Unique content identifier")
    content: str = Field(..., description="Generated content")
    content_type: str = Field(..., description="Type of content generated")
    format: str = Field(..., description="Output format used")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ToolMetadata(BaseModel):
    """Standardized metadata for all tool executions"""
    tool_name: str = Field(..., description="Name of the executed tool")
    execution_time: float = Field(..., description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    session_id: str = Field(..., description="Session identifier")
    step_index: int = Field(..., description="Step index")
    success: bool = Field(..., description="Whether execution was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")

# ============================================================================
# ENHANCED BASE TOOL CLASS
# ============================================================================

class BaseTool(ABC, BaseModel):
    """Enhanced base tool class with standardized input/output handling"""
    
    # Basic tool information
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    tool_type: ToolType = Field(..., description="Type of tool")
    version: str = Field("1.0.0", description="Tool version")
    
    # Tool capabilities
    supported_subjects: List[ContentSubject] = Field(default=[ContentSubject.GENERAL], description="Supported subjects")
    supported_difficulties: List[DifficultyLevel] = Field(default=[DifficultyLevel.INTERMEDIATE], description="Supported difficulty levels")
    
    # Configuration
    parameters: Optional[Dict[str, Any]] = Field(None, description="Tool parameters schema")
    max_execution_time: Optional[float] = Field(30.0, description="Maximum execution time in seconds")
    
    class Config:
        arbitrary_types_allowed = True

    async def __call__(self, **kwargs) -> "StandardizedToolResult":
        """Execute the tool with standardized input/output handling."""
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            validated_input = self._validate_input(kwargs)
            
            # Execute tool logic
            result = await self.execute(validated_input)
            
            # Create standardized output
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            metadata = ToolMetadata(
                tool_name=self.name,
                execution_time=execution_time,
                session_id=validated_input.session_id,
                step_index=validated_input.step_index,
                success=True
            )
            
            return StandardizedToolResult(
                success=True,
                data=result,
                metadata=metadata,
                error=None
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            metadata = ToolMetadata(
                tool_name=self.name,
                execution_time=execution_time,
                session_id=kwargs.get('session_id', 'unknown'),
                step_index=kwargs.get('step_index', -1),
                success=False,
                error_message=str(e)
            )
            
            return StandardizedToolResult(
                success=False,
                data=None,
                metadata=metadata,
                error=str(e)
            )

    @abstractmethod
    async def execute(self, input_data: BaseToolInput) -> Any:
        """Execute the tool with validated input data."""
        pass

    def _validate_input(self, kwargs: Dict[str, Any]) -> BaseToolInput:
        """Validate and convert input to appropriate input model."""
        # This should be implemented by subclasses based on their input type
        raise NotImplementedError("Subclasses must implement _validate_input")

    def to_param(self) -> Dict:
        """Convert tool to function call format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

# ============================================================================
# ENHANCED TOOL RESULT CLASSES
# ============================================================================

class StandardizedToolResult(BaseModel):
    """Enhanced standardized result for all tools"""
    
    success: bool = Field(..., description="Whether the tool execution was successful")
    data: Optional[Any] = Field(None, description="Tool execution result data")
    metadata: ToolMetadata = Field(..., description="Execution metadata")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Additional fields for specific result types
    exercise_output: Optional[ExerciseOutput] = Field(None, description="Exercise-specific output")
    assessment_output: Optional[AssessmentOutput] = Field(None, description="Assessment-specific output")
    content_output: Optional[ContentOutput] = Field(None, description="Content-specific output")
    
    class Config:
        arbitrary_types_allowed = True

    def __bool__(self):
        return self.success

    def __str__(self):
        if self.success:
            return f"Success: {self.data}"
        return f"Error: {self.error}"

    def get_exercise_output(self) -> Optional[ExerciseOutput]:
        """Get exercise output if available."""
        return self.exercise_output

    def get_assessment_output(self) -> Optional[AssessmentOutput]:
        """Get assessment output if available."""
        return self.assessment_output

    def get_content_output(self) -> Optional[ContentOutput]:
        """Get content output if available."""
        return self.content_output

# ============================================================================
# LEGACY SUPPORT (for backward compatibility)
# ============================================================================

class ToolResult(StandardizedToolResult):
    """Legacy ToolResult for backward compatibility"""
    output: Optional[Any] = Field(None, description="Legacy output field")
    system: Optional[str] = Field(None, description="Legacy system field")
    
    def __init__(self, **data):
        # Map legacy fields to new structure
        if 'output' in data:
            data['data'] = data.pop('output')
        if 'system' in data:
            data['metadata'] = ToolMetadata(
                tool_name="legacy",
                execution_time=0.0,
                session_id=data.get('session_id', 'unknown'),
                step_index=data.get('step_index', -1),
                success=data.get('error') is None
            )
        super().__init__(**data)

class CLIResult(ToolResult):
    """A ToolResult that can be rendered as a CLI output."""
    pass

class ToolFailure(ToolResult):
    """A ToolResult that represents a failure."""
    pass

class AgentAwareTool:
    """Legacy agent awareness support"""
    agent: Optional = None
