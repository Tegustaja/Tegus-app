"""
Tool Factory System
This module provides a factory pattern for creating and managing standardized tools.
"""

from typing import Dict, Type, List, Optional, Any
from enum import Enum
import asyncio
import logging
from datetime import datetime

from app.tool.base import (
    BaseTool, 
    ToolType, 
    ContentSubject, 
    DifficultyLevel,
    StandardizedToolResult,
    BaseToolInput
)

logger = logging.getLogger(__name__)

class ToolCategory(str, Enum):
    """Categories for organizing tools"""
    EXERCISE_GENERATION = "exercise_generation"
    ASSESSMENT = "assessment"
    CONTENT_CREATION = "content_creation"
    INTERACTION = "interaction"
    UTILITY = "utility"
    DATA_PROCESSING = "data_processing"

class ToolRegistry:
    """Registry for managing all available tools"""
    
    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._categories: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}
    
    def register_tool(self, tool_class: Type[BaseTool], category: ToolCategory = None) -> None:
        """Register a tool class in the registry."""
        # Handle both Pydantic models and regular classes
        if hasattr(tool_class, '__fields__'):
            # Pydantic model - get from model fields
            tool_name = tool_class.__fields__.get('name', {}).default
            description = tool_class.__fields__.get('description', {}).default
            tool_type = tool_class.__fields__.get('tool_type', {}).default
            version = tool_class.__fields__.get('version', {}).default
            supported_subjects = tool_class.__fields__.get('supported_subjects', {}).default or []
            supported_difficulties = tool_class.__fields__.get('supported_difficulties', {}).default or []
            max_execution_time = tool_class.__fields__.get('max_execution_time', {}).default
        else:
            # Regular class - get attributes directly
            tool_name = getattr(tool_class, 'name', None)
            description = getattr(tool_class, 'description', None)
            tool_type = getattr(tool_class, 'tool_type', None)
            version = getattr(tool_class, 'version', '1.0.0')
            supported_subjects = getattr(tool_class, 'supported_subjects', [])
            supported_difficulties = getattr(tool_class, 'supported_difficulties', [])
            max_execution_time = getattr(tool_class, 'max_execution_time', 30.0)
        
        if not tool_name:
            logger.error(f"Tool class {tool_class.__name__} missing 'name' attribute")
            return
        
        if tool_name in self._tools:
            logger.warning(f"Tool {tool_name} is already registered. Overwriting.")
        
        self._tools[tool_name] = tool_class
        
        # Extract metadata
        self._tool_metadata[tool_name] = {
            "name": tool_name,
            "description": description or "No description provided",
            "tool_type": tool_type.value if hasattr(tool_type, 'value') else str(tool_type) if tool_type else "unknown",
            "version": version or "1.0.0",
            "supported_subjects": [s.value for s in supported_subjects if hasattr(s, 'value')] if supported_subjects else [],
            "supported_difficulties": [d.value for d in supported_difficulties if hasattr(d, 'value')] if supported_difficulties else [],
            "max_execution_time": max_execution_time or 30.0,
            "category": category.value if category else "uncategorized",
            "registered_at": datetime.utcnow().isoformat()
        }
        
        # Add to category
        if category:
            self._categories[category].append(tool_name)
        else:
            self._categories[ToolCategory.UTILITY].append(tool_name)
        
        logger.info(f"Registered tool: {tool_name} in category: {category}")
    
    def get_tool(self, tool_name: str) -> Optional[Type[BaseTool]]:
        """Get a tool class by name."""
        return self._tools.get(tool_name)
    
    def get_tool_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific tool."""
        return self._tool_metadata.get(tool_name)
    
    def list_tools(self, category: ToolCategory = None) -> List[str]:
        """List all tools, optionally filtered by category."""
        if category:
            return self._categories[category].copy()
        return list(self._tools.keys())
    
    def list_categories(self) -> Dict[ToolCategory, List[str]]:
        """List all categories and their tools."""
        return {cat: tools.copy() for cat, tools in self._categories.items()}
    
    def get_tools_by_subject(self, subject: ContentSubject) -> List[str]:
        """Get tools that support a specific subject."""
        return [
            tool_name for tool_name, metadata in self._tool_metadata.items()
            if subject.value in metadata["supported_subjects"]
        ]
    
    def get_tools_by_difficulty(self, difficulty: DifficultyLevel) -> List[str]:
        """Get tools that support a specific difficulty level."""
        return [
            tool_name for tool_name, metadata in self._tool_metadata.items()
            if difficulty.value in metadata["supported_difficulties"]
        ]

class ToolFactory:
    """Factory for creating tool instances with proper configuration"""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self._instances: Dict[str, BaseTool] = {}
    
    def create_tool(self, tool_name: str, **kwargs) -> Optional[BaseTool]:
        """Create a tool instance with the given parameters."""
        tool_class = self.registry.get_tool(tool_name)
        if not tool_class:
            logger.error(f"Tool {tool_name} not found in registry")
            return None
        
        try:
            # Create tool instance
            tool_instance = tool_class(**kwargs)
            
            # Store instance for potential reuse
            instance_key = f"{tool_name}_{id(tool_instance)}"
            self._instances[instance_key] = tool_instance
            
            logger.info(f"Created tool instance: {tool_name}")
            return tool_instance
            
        except Exception as e:
            logger.error(f"Failed to create tool {tool_name}: {e}")
            return None
    
    def create_tool_batch(self, tool_configs: List[Dict[str, Any]]) -> List[BaseTool]:
        """Create multiple tool instances from configurations."""
        tools = []
        for config in tool_configs:
            tool_name = config.pop("tool_name", None)
            if tool_name:
                tool = self.create_tool(tool_name, **config)
                if tool:
                    tools.append(tool)
        return tools
    
    def get_tool_instance(self, tool_name: str, instance_id: str) -> Optional[BaseTool]:
        """Get a specific tool instance by ID."""
        instance_key = f"{tool_name}_{instance_id}"
        return self._instances.get(instance_key)
    
    def cleanup_instances(self) -> None:
        """Clean up stored tool instances."""
        self._instances.clear()
        logger.info("Cleaned up all tool instances")

class ToolExecutor:
    """Executor for running tools with proper error handling and monitoring"""
    
    def __init__(self, factory: ToolFactory):
        self.factory = factory
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute_tool(self, tool_name: str, **kwargs) -> StandardizedToolResult:
        """Execute a tool with the given parameters."""
        start_time = datetime.utcnow()
        
        # Create tool instance
        tool = self.factory.create_tool(tool_name, **kwargs)
        if not tool:
            return StandardizedToolResult(
                success=False,
                data=None,
                metadata=None,
                error=f"Failed to create tool: {tool_name}"
            )
        
        try:
            # Execute tool
            result = await tool(**kwargs)
            
            # Record execution
            execution_record = {
                "tool_name": tool_name,
                "execution_time": (datetime.utcnow() - start_time).total_seconds(),
                "success": result.success,
                "timestamp": start_time.isoformat(),
                "parameters": kwargs,
                "result_summary": str(result)[:200]  # Truncate for storage
            }
            self.execution_history.append(execution_record)
            
            return result
            
        except Exception as e:
            execution_record = {
                "tool_name": tool_name,
                "execution_time": (datetime.utcnow() - start_time).total_seconds(),
                "success": False,
                "timestamp": start_time.isoformat(),
                "parameters": kwargs,
                "error": str(e)
            }
            self.execution_history.append(execution_record)
            
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return StandardizedToolResult(
                success=False,
                data=None,
                metadata=None,
                error=f"Execution failed: {str(e)}"
            )
    
    async def execute_tool_chain(self, tool_chain: List[Dict[str, Any]]) -> List[StandardizedToolResult]:
        """Execute a chain of tools in sequence."""
        results = []
        
        for i, tool_config in enumerate(tool_chain):
            tool_name = tool_config.pop("tool_name")
            logger.info(f"Executing tool {i+1}/{len(tool_chain)}: {tool_name}")
            
            result = await self.execute_tool(tool_name, **tool_config)
            results.append(result)
            
            # Stop chain if tool fails
            if not result.success:
                logger.error(f"Tool chain stopped at {tool_name} due to failure")
                break
        
        return results
    
    def get_execution_history(self, tool_name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history, optionally filtered by tool name."""
        history = self.execution_history
        
        if tool_name:
            history = [h for h in history if h["tool_name"] == tool_name]
        
        return history[-limit:] if limit else history
    
    def get_success_rate(self, tool_name: str = None) -> float:
        """Calculate success rate for tool executions."""
        history = self.get_execution_history(tool_name)
        if not history:
            return 0.0
        
        successful = sum(1 for h in history if h["success"])
        return successful / len(history)

class ToolManager:
    """Main manager class that coordinates all tool operations"""
    
    def __init__(self):
        self.registry = ToolRegistry()
        self.factory = ToolFactory(self.registry)
        self.executor = ToolExecutor(self.factory)
        
        # Auto-register tools from the base module
        self._auto_register_tools()
    
    def _auto_register_tools(self):
        """Automatically discover and register available tools."""
        try:
            # Import and register all available tools
            from multiple_choice_exercise import MultipleChoiceExercise
            from calculation_exercise import CalculationExercise
            from true_false_exercise import TrueFalseExercise
            from check_solution import CheckSolution
            
            # Register exercise tools
            self.registry.register_tool(
                MultipleChoiceExercise, 
                ToolCategory.EXERCISE_GENERATION
            )
            
            self.registry.register_tool(
                CalculationExercise, 
                ToolCategory.EXERCISE_GENERATION
            )
            
            self.registry.register_tool(
                TrueFalseExercise, 
                ToolCategory.EXERCISE_GENERATION
            )
            
            # Register assessment tools
            self.registry.register_tool(
                CheckSolution, 
                ToolCategory.ASSESSMENT
            )
            
        except ImportError as e:
            logger.warning(f"Could not auto-register some tools: {e}")
    
    def register_tool(self, tool_class: Type[BaseTool], category: ToolCategory = None) -> None:
        """Register a new tool."""
        self.registry.register_tool(tool_class, category)
    
    async def execute_tool(self, tool_name: str, **kwargs) -> StandardizedToolResult:
        """Execute a single tool."""
        return await self.executor.execute_tool(tool_name, **kwargs)
    
    async def execute_tool_chain(self, tool_chain: List[Dict[str, Any]]) -> List[StandardizedToolResult]:
        """Execute a chain of tools."""
        return await self.executor.execute_tool_chain(tool_chain)
    
    def get_available_tools(self, category: ToolCategory = None) -> List[str]:
        """Get list of available tools."""
        return self.registry.list_tools(category)
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tool."""
        return self.registry.get_tool_metadata(tool_name)
    
    def get_tools_by_capability(self, subject: ContentSubject = None, difficulty: DifficultyLevel = None) -> List[str]:
        """Get tools filtered by capabilities."""
        if subject and difficulty:
            subject_tools = set(self.registry.get_tools_by_subject(subject))
            difficulty_tools = set(self.registry.get_tools_by_difficulty(difficulty))
            return list(subject_tools.intersection(difficulty_tools))
        elif subject:
            return self.registry.get_tools_by_subject(subject)
        elif difficulty:
            return self.registry.get_tools_by_difficulty(difficulty)
        else:
            return self.registry.list_tools()
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "total_executions": len(self.executor.execution_history),
            "success_rate": self.executor.get_success_rate(),
            "tools_available": len(self.registry.list_tools()),
            "categories": self.registry.list_categories()
        }

# ============================================================================
# GLOBAL TOOL MANAGER INSTANCE
# ============================================================================

# Create a global instance for easy access
tool_manager = ToolManager()

# Convenience functions for common operations
def register_tool(tool_class: Type[BaseTool], category: ToolCategory = None) -> None:
    """Register a tool with the global manager."""
    tool_manager.register_tool(tool_class, category)

async def execute_tool(tool_name: str, **kwargs) -> StandardizedToolResult:
    """Execute a tool using the global manager."""
    return await tool_manager.execute_tool(tool_name, **kwargs)

def get_available_tools(category: ToolCategory = None) -> List[str]:
    """Get available tools from the global manager."""
    return tool_manager.get_available_tools(category)

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_usage():
    """Example of how to use the tool management system."""
    
    # Get available tools
    print("Available tools:", get_available_tools())
    
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
        print("Tool executed successfully!")
        print(f"Result: {result.data}")
    else:
        print(f"Tool execution failed: {result.error}")
    
    # Get execution stats
    stats = tool_manager.get_execution_stats()
    print(f"Execution stats: {stats}")

if __name__ == "__main__":
    asyncio.run(example_usage())
