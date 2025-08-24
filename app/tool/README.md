# 🛠️ Standardized Tool Architecture

This directory contains a comprehensive, standardized system for creating and managing educational tools in the Tegus application. The new architecture provides consistent input/output models, error handling, and tool management capabilities.

## 🏗️ Architecture Overview

### Core Components

1. **`base.py`** - Enhanced base classes and standardized models
2. **`tool_factory.py`** - Tool registry, factory, and execution management
3. **`tool_template.py`** - Comprehensive templates for creating new tools
4. **`multiple_choice_exercise_standardized.py`** - Example implementation

## 🎯 Key Benefits

- **Consistency**: All tools follow the same input/output patterns
- **Type Safety**: Full Pydantic validation and type checking
- **Error Handling**: Graceful fallbacks and comprehensive error reporting
- **Monitoring**: Built-in execution tracking and performance metrics
- **Extensibility**: Easy to add new tools and capabilities
- **Backward Compatibility**: Existing tools continue to work

## 🚀 Quick Start

### 1. Using Existing Tools

```python
from app.tool.tool_factory import execute_tool, get_available_tools

# List available tools
print(get_available_tools())

# Execute a tool
result = await execute_tool(
    "multiple_choice_exercise",
    query="What is the Pythagorean theorem?",
    session_id="123e4567-e89b-12d3-a456-426614174000",
    step_index=0,
    subject="mathematics",
    difficulty="intermediate"
)

if result.success:
    exercise_output = result.get_exercise_output()
    print(f"Question: {exercise_output.question}")
```

### 2. Creating a New Tool

```python
from app.tool.base import BaseTool, ToolType, ExerciseInput, ExerciseOutput
from app.tool.tool_factory import register_tool

class MyNewTool(BaseTool):
    name = "my_new_tool"
    description = "My custom educational tool"
    tool_type = ToolType.EXERCISE
    
    def _validate_input(self, kwargs):
        return ExerciseInput(**kwargs)
    
    async def execute(self, input_data):
        # Your tool logic here
        return ExerciseOutput(...)

# Register the tool
register_tool(MyNewTool)
```

## 📋 Standardized Models

### Input Models

- **`BaseToolInput`** - Common fields for all tools
- **`ExerciseInput`** - For exercise generation tools
- **`AssessmentInput`** - For assessment/evaluation tools
- **`ContentInput`** - For content generation tools

### Output Models

- **`ExerciseOutput`** - Structured exercise data
- **`AssessmentOutput`** - Assessment results and feedback
- **`ContentOutput`** - Generated content
- **`StandardizedToolResult`** - Wrapper with metadata and error handling

### Enums

- **`ToolType`** - Exercise, Assessment, Content, Interaction, Utility
- **`ExerciseType`** - Multiple Choice, Calculation, True/False, etc.
- **`DifficultyLevel`** - Beginner, Intermediate, Advanced
- **`ContentSubject`** - Math, Physics, Chemistry, Biology, etc.

## 🔧 Tool Configuration

### Required Fields

Every tool must define:

```python
class MyTool(BaseTool):
    name: str = "tool_name"
    description: str = "Tool description"
    tool_type: ToolType = ToolType.EXERCISE
    version: str = "1.0.0"
    
    # Capabilities
    supported_subjects: List[ContentSubject] = [...]
    supported_difficulties: List[DifficultyLevel] = [...]
    
    # Configuration
    max_execution_time: float = 30.0
    parameters: dict = {...}  # For function calling
```

### Input Validation

Implement `_validate_input()` to convert raw kwargs to validated models:

```python
def _validate_input(self, kwargs: dict) -> ExerciseInput:
    # Extract and validate required fields
    session_id = kwargs.get("session_id")
    step_index = kwargs.get("step_index")
    query = kwargs.get("query")
    
    if not all([session_id, step_index is not None, query]):
        raise ValueError("Missing required parameters")
    
    return ExerciseInput(
        session_id=session_id,
        step_index=step_index,
        query=query,
        subject=ContentSubject(kwargs.get("subject", "general")),
        difficulty=DifficultyLevel(kwargs.get("difficulty", "intermediate"))
    )
```

### Main Execution

Implement `execute()` with your tool logic:

```python
async def execute(self, input_data: ExerciseInput) -> ExerciseOutput:
    try:
        # Your tool logic here
        result = await self._process_input(input_data)
        
        return ExerciseOutput(
            exercise_id=str(uuid.uuid4()),
            exercise_type=ExerciseType.MULTIPLE_CHOICE,
            question=result["question"],
            options=result["options"],
            correct_answer=result["correct_answer"],
            difficulty=input_data.difficulty,
            subject=input_data.subject
        )
    except Exception as e:
        # Return fallback output
        return self._create_fallback_output(input_data, str(e))
```

## 🏭 Tool Management

### Registry

The tool registry automatically discovers and manages all available tools:

```python
from app.tool.tool_factory import tool_manager

# List all tools
print(tool_manager.get_available_tools())

# Get tool information
tool_info = tool_manager.get_tool_info("multiple_choice_exercise")

# Filter by capabilities
math_tools = tool_manager.get_tools_by_capability(
    subject=ContentSubject.MATH,
    difficulty=DifficultyLevel.INTERMEDIATE
)
```

### Execution

Execute tools individually or in chains:

```python
# Single tool
result = await tool_manager.execute_tool("tool_name", **params)

# Tool chain
tool_chain = [
    {"tool_name": "tool1", "param1": "value1"},
    {"tool_name": "tool2", "param2": "value2"}
]
results = await tool_manager.execute_tool_chain(tool_chain)
```

### Monitoring

Track execution performance and success rates:

```python
# Get execution statistics
stats = tool_manager.get_execution_stats()
print(f"Success rate: {stats['success_rate']:.2%}")

# Get execution history
history = tool_manager.executor.get_execution_history("tool_name", limit=10)
```

## 📊 Database Integration

### Storing Results

Tools can optionally store results in the database:

```python
async def store_result(self, input_data, output):
    try:
        if self.supabase_client:
            result = self.supabase_client.table("tool_results").insert({
                "session_id": input_data.session_id,
                "step_index": input_data.step_index,
                "tool_name": self.name,
                "input_data": input_data.dict(),
                "output_data": output.dict(),
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            return result.data is not None
    except Exception as e:
        logger.error(f"Error storing result: {e}")
        return False
```

## 🧪 Testing

### Running Examples

```bash
# Test the standardized multiple choice tool
python3 -m app.tool.multiple_choice_exercise_standardized

# Test the tool factory
python3 -m app.tool.tool_factory

# Test the template
python3 -m app.tool.tool_template
```

### Creating Test Cases

```python
import pytest
from app.tool.tool_template import TemplateTool

@pytest.mark.asyncio
async def test_template_tool():
    tool = TemplateTool()
    
    input_data = {
        "query": "Test query",
        "session_id": "test-session",
        "step_index": 0
    }
    
    result = await tool(**input_data)
    assert result.success
    assert result.get_exercise_output() is not None
```

## 🔄 Migration Guide

### From Old Tools

1. **Update imports**: Use new base classes
2. **Add tool type**: Specify `tool_type` and capabilities
3. **Implement validation**: Add `_validate_input()` method
4. **Update execute method**: Use typed input/output models
5. **Register tool**: Add to the tool registry

### Example Migration

**Before:**
```python
class OldTool(BaseTool):
    async def execute(self, **kwargs):
        # Direct parameter access
        query = kwargs.get("query")
        # ... tool logic
        return result
```

**After:**
```python
class NewTool(BaseTool):
    tool_type = ToolType.EXERCISE
    supported_subjects = [ContentSubject.MATH]
    
    def _validate_input(self, kwargs):
        return ExerciseInput(**kwargs)
    
    async def execute(self, input_data: ExerciseInput):
        # Typed input access
        query = input_data.query
        # ... tool logic
        return ExerciseOutput(...)
```

## 📚 Best Practices

### 1. Error Handling
- Always return fallback output on errors
- Log errors with context
- Use try-catch blocks in critical sections

### 2. Performance
- Set appropriate `max_execution_time`
- Use async operations for I/O
- Implement caching where appropriate

### 3. Validation
- Validate all input parameters
- Use Pydantic validators for complex validation
- Provide clear error messages

### 4. Documentation
- Document tool capabilities clearly
- Include usage examples
- Specify supported subjects and difficulties

### 5. Testing
- Test with various input combinations
- Verify error handling
- Test performance under load

## 🚨 Common Issues

### 1. Import Errors
- Ensure all dependencies are installed
- Check import paths are correct
- Verify Python environment

### 2. Validation Errors
- Check required parameters are provided
- Verify parameter types match expected values
- Ensure session_id is a valid UUID

### 3. Execution Failures
- Check tool registration
- Verify tool parameters
- Review error logs

## 🔮 Future Enhancements

- **Plugin System**: Dynamic tool loading
- **Performance Metrics**: Advanced monitoring and analytics
- **Tool Composition**: Building complex tools from simpler ones
- **A/B Testing**: Tool performance comparison
- **Machine Learning**: Adaptive tool selection based on user behavior

## 📞 Support

For questions or issues with the tool architecture:

1. Check this README for common solutions
2. Review the template files for examples
3. Check the test files for usage patterns
4. Review existing tool implementations

---

**Happy Tool Building! 🎉**
