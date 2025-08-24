"""Collection classes for managing multiple tools using standardized architecture."""
from typing import Any, Dict, List, Optional
from app.tool.base import BaseTool, StandardizedToolResult, ToolType, ContentSubject, DifficultyLevel
from app.exceptions import ToolError


class ToolCollection:
    """A collection of defined tools."""

    def __init__(self, *tools: BaseTool):
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}

    def __iter__(self):
        return iter(self.tools)

    def to_params(self) -> List[Dict[str, Any]]:
        return [tool.to_param() for tool in self.tools]

    async def execute(
        self, *, name: str, tool_input: Dict[str, Any] = None
    ) -> StandardizedToolResult:
        """Execute a specific tool by name."""
        tool = self.tool_map.get(name)
        if not tool:
            # Return standardized error result
            from app.tool.base import StandardizedToolResult, ToolMetadata
            return StandardizedToolResult(
                success=False,
                data=None,
                metadata=ToolMetadata(
                    tool_name=name,
                    execution_time=0.0,
                    session_id=tool_input.get("session_id", "unknown") if tool_input else "unknown",
                    step_index=tool_input.get("step_index", -1) if tool_input else -1,
                    success=False,
                    error_message=f"Tool {name} not found in collection"
                ),
                error=f"Tool {name} not found in collection"
            )
        
        try:
            result = await tool(**tool_input)
            return result
        except Exception as e:
            # Return standardized error result
            from app.tool.base import StandardizedToolResult, ToolMetadata
            return StandardizedToolResult(
                success=False,
                data=None,
                metadata=ToolMetadata(
                    tool_name=tool.name,
                    execution_time=0.0,
                    session_id=tool_input.get("session_id", "unknown") if tool_input else "unknown",
                    step_index=tool_input.get("step_index", -1) if tool_input else -1,
                    success=False,
                    error_message=str(e)
                ),
                error=str(e)
            )

    async def execute_all(self) -> List[StandardizedToolResult]:
        """Execute all tools in the collection sequentially."""
        results = []
        for tool in self.tools:
            try:
                result = await tool()
                results.append(result)
            except Exception as e:
                # Return standardized error result
                from app.tool.base import StandardizedToolResult, ToolMetadata
                error_result = StandardizedToolResult(
                    success=False,
                    data=None,
                    metadata=ToolMetadata(
                        tool_name=tool.name,
                        execution_time=0.0,
                        session_id="unknown",
                        step_index=-1,
                        success=False,
                        error_message=str(e)
                    ),
                    error=str(e)
                )
                results.append(error_result)
        return results

    def get_tool(self, name: str) -> BaseTool:
        return self.tool_map.get(name)

    def add_tool(self, tool: BaseTool):
        self.tools += (tool,)
        self.tool_map[tool.name] = tool
        return self

    def add_tools(self, *tools: BaseTool):
        for tool in tools:
            self.add_tool(tool)
        return self

    def get_tools_by_type(self, tool_type: ToolType) -> List[BaseTool]:
        """Get all tools of a specific type."""
        return [tool for tool in self.tools if hasattr(tool, 'tool_type') and tool.tool_type == tool_type]

    def get_tools_by_subject(self, subject: ContentSubject) -> List[BaseTool]:
        """Get all tools that support a specific subject."""
        return [tool for tool in self.tools if hasattr(tool, 'supported_subjects') and subject in tool.supported_subjects]

    def get_tools_by_difficulty(self, difficulty: DifficultyLevel) -> List[BaseTool]:
        """Get all tools that support a specific difficulty level."""
        return [tool for tool in self.tools if hasattr(tool, 'supported_difficulties') and difficulty in tool.supported_difficulties]

    def list_tool_capabilities(self) -> Dict[str, Any]:
        """Get a summary of all tool capabilities."""
        capabilities = {}
        for tool in self.tools:
            capabilities[tool.name] = {
                "type": getattr(tool, 'tool_type', 'unknown'),
                "subjects": getattr(tool, 'supported_subjects', []),
                "difficulties": getattr(tool, 'supported_difficulties', []),
                "version": getattr(tool, 'version', '1.0.0')
            }
        return capabilities
