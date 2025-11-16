#!/usr/bin/env python3
"""
server.py

This is the main entry point for the Todo MCP server.
It defines all the tools provided by the server and handles
connecting to clients.

WHAT IS MCP?
The Model Context Protocol (MCP) allows AI models like Claude
to interact with external tools and services. This server implements
the MCP specification to provide a Todo list functionality that
Claude can use.

HOW THE SERVER WORKS:
1. It creates an MCP server instance with identity information
2. It defines a set of tools for managing todos
3. It connects to a transport (stdio in this case)
4. It handles incoming tool calls from clients (like Claude)
"""
import asyncio
import signal
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import models and schemas
from src.models.todo import (
    CreateTodoSchema,
    UpdateTodoSchema,
    CompleteTodoSchema,
    DeleteTodoSchema,
    SearchTodosByTitleSchema,
    SearchTodosByDateSchema
)

# Import services
from src.services.todo_service import todo_service
from src.services.database_service import database_service

# Import utilities
from src.utils.formatters import (
    create_success_response,
    create_error_response,
    format_todo,
    format_todo_list
)
from src.config import config

# Create the MCP server
# 
# We initialize with identity information that helps clients
# understand what they're connecting to.
server = Server("Todo-MCP-Server", version="1.0.0")


def safe_execute(operation, error_message: str):
    """
    Helper function to safely execute operations
    
    This function:
    1. Attempts to execute an operation
    2. Catches any errors
    3. Returns either the result or an Error object
    
    WHY USE THIS PATTERN?
    - Centralizes error handling
    - Prevents crashes from uncaught exceptions
    - Makes error reporting consistent across all tools
    - Simplifies the tool implementations
    
    Args:
        operation: The function to execute (callable)
        error_message: The message to include if an error occurs
    
    Returns:
        Either the operation result or an Error
    """
    try:
        return operation()
    except Exception as error:
        print(f"{error_message}: {error}", file=sys.stderr)
        if isinstance(error, Exception):
            return Exception(f"{error_message}: {str(error)}")
        return Exception(error_message)


# Tool 1: Create a new todo
# 
# This tool:
# 1. Validates the input (title and description)
# 2. Creates a new todo using the service
# 3. Returns the formatted todo
# 
# PATTERN FOR ALL TOOLS:
# - Register with server.call_tool()
# - Define name, description, and parameter schema
# - Implement the async handler function
# - Use safe_execute for error handling
# - Return properly formatted response
@server.call_tool()
async def handle_tool_call(tool_name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle all tool calls - routes to appropriate handler based on tool_name"""
    if tool_name == "create-todo":
        try:
            validated_data = CreateTodoSchema(**arguments)
            new_todo = todo_service.create_todo(validated_data)
            result = format_todo(new_todo)
            return [TextContent(type="text", text=f"✅ Todo Created:\n\n{result}")]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to create todo: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "list-todos":
        result = safe_execute(
            lambda: format_todo_list(todo_service.get_all_todos()),
            "Failed to list todos"
        )
        if isinstance(result, Exception):
            return [TextContent(type="text", text=create_error_response(result.args[0] if result.args else "Unknown error")["content"][0]["text"])]
        return [TextContent(type="text", text=result)]
    
    elif tool_name == "get-todo":
        todo = todo_service.get_todo(arguments.get("id", ""))
        if not todo:
            return [TextContent(type="text", text=create_error_response(f"Todo with ID {arguments.get('id')} not found")["content"][0]["text"])]
        result = safe_execute(
            lambda: format_todo(todo),
            "Failed to get todo"
        )
        if isinstance(result, Exception):
            return [TextContent(type="text", text=create_error_response(result.args[0] if result.args else "Unknown error")["content"][0]["text"])]
        return [TextContent(type="text", text=result)]
    
    elif tool_name == "update-todo":
        try:
            validated_data = UpdateTodoSchema(**arguments)
            if not validated_data.title and not validated_data.description:
                return [TextContent(type="text", text=create_error_response("At least one field (title or description) must be provided")["content"][0]["text"])]
            updated_todo = todo_service.update_todo(validated_data)
            if not updated_todo:
                return [TextContent(type="text", text=create_error_response(f"Todo with ID {validated_data.id} not found")["content"][0]["text"])]
            result = format_todo(updated_todo)
            return [TextContent(type="text", text=f"✅ Todo Updated:\n\n{result}")]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to update todo: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "complete-todo":
        try:
            validated_data = CompleteTodoSchema(**arguments)
            completed_todo = todo_service.complete_todo(validated_data.id)
            if not completed_todo:
                return [TextContent(type="text", text=create_error_response(f"Todo with ID {validated_data.id} not found")["content"][0]["text"])]
            result = format_todo(completed_todo)
            return [TextContent(type="text", text=f"✅ Todo Completed:\n\n{result}")]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to complete todo: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "delete-todo":
        try:
            validated_data = DeleteTodoSchema(**arguments)
            todo = todo_service.get_todo(validated_data.id)
            if not todo:
                return [TextContent(type="text", text=create_error_response(f"Todo with ID {validated_data.id} not found")["content"][0]["text"])]
            success = todo_service.delete_todo(validated_data.id)
            if not success:
                return [TextContent(type="text", text=create_error_response(f"Failed to delete todo with ID {validated_data.id}")["content"][0]["text"])]
            return [TextContent(type="text", text=f"✅ Todo Deleted: \"{todo.title}\"")]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to delete todo: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "search-todos-by-title":
        try:
            validated_data = SearchTodosByTitleSchema(**arguments)
            todos = todo_service.search_by_title(validated_data.title)
            result = format_todo_list(todos)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to search todos: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "search-todos-by-date":
        try:
            validated_data = SearchTodosByDateSchema(**arguments)
            todos = todo_service.search_by_date(validated_data.date)
            result = format_todo_list(todos)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to search todos by date: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "list-active-todos":
        result = safe_execute(
            lambda: format_todo_list(todo_service.get_active_todos()),
            "Failed to list active todos"
        )
        if isinstance(result, Exception):
            return [TextContent(type="text", text=create_error_response(result.args[0] if result.args else "Unknown error")["content"][0]["text"])]
        return [TextContent(type="text", text=result)]
    
    elif tool_name == "summarize-active-todos":
        result = safe_execute(
            lambda: todo_service.summarize_active_todos(),
            "Failed to summarize active todos"
        )
        if isinstance(result, Exception):
            return [TextContent(type="text", text=create_error_response(result.args[0] if result.args else "Unknown error")["content"][0]["text"])]
        return [TextContent(type="text", text=result)]
    
    else:
        return [TextContent(type="text", text=create_error_response(f"Unknown tool: {tool_name}")["content"][0]["text"])]


# Register tools with proper schemas
# The MCP SDK needs to know about available tools
@server.list_tools()
async def list_tools_handler() -> list[Tool]:
    return [
        Tool(
            name="create-todo",
            description="Create a new todo item",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "minLength": 1, "description": "Title is required"},
                    "description": {"type": "string", "minLength": 1, "description": "Description is required"}
                },
                "required": ["title", "description"]
            }
        ),
        Tool(
            name="list-todos",
            description="List all todos",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get-todo",
            description="Get a specific todo by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", "description": "Invalid Todo ID"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="update-todo",
            description="Update a todo title or description",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", "description": "Invalid Todo ID"},
                    "title": {"type": "string", "minLength": 1, "description": "Title is required"},
                    "description": {"type": "string", "minLength": 1, "description": "Description is required"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="complete-todo",
            description="Mark a todo as completed",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", "description": "Invalid Todo ID"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="delete-todo",
            description="Delete a todo",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", "description": "Invalid Todo ID"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="search-todos-by-title",
            description="Search todos by title (case insensitive partial match)",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "minLength": 1, "description": "Search term is required"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="search-todos-by-date",
            description="Search todos by creation date (format: YYYY-MM-DD)",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$", "description": "Date must be in YYYY-MM-DD format"}
                },
                "required": ["date"]
            }
        ),
        Tool(
            name="list-active-todos",
            description="List all non-completed todos",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="summarize-active-todos",
            description="Generate a summary of all active (non-completed) todos",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


async def main():
    """
    Main function to start the server
    
    This function:
    1. Initializes the server
    2. Sets up graceful shutdown handlers
    3. Connects to the transport
    
    WHY USE STDIO TRANSPORT?
    - Works well with the MCP protocol
    - Simple to integrate with LLM platforms like Claude Desktop
    - No network configuration required
    - Easy to debug and test
    """
    print("Starting Todo MCP Server...", file=sys.stderr)
    print(f"SQLite database path: {config.db.path}", file=sys.stderr)
    
    try:
        # Database is automatically initialized when the service is imported
        
        # Set up graceful shutdown to close the database
        # 
        # This ensures data is properly saved when the server is stopped.
        # Both SIGINT (Ctrl+C) and SIGTERM (kill command) are handled.
        def shutdown_handler(signum, frame):
            print('Shutting down...', file=sys.stderr)
            database_service.close()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
        
        # Connect to stdio transport
        # 
        # The stdio_server uses standard input/output for communication,
        # which is how Claude Desktop and other MCP clients connect to the server.
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
        
        print("Todo MCP Server running on stdio transport", file=sys.stderr)
    except Exception as error:
        print(f"Failed to start Todo MCP Server: {error}", file=sys.stderr)
        database_service.close()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
