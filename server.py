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
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import models and schemas
from src.models.todo import (
    CreateTodoSchema,
    CreateTodosSchema,
    UpdateTodoSchema,
    CompleteTodoSchema,
    DeleteTodoSchema,
    SkipTodosSchema,
    MarkTodosNotCompletedSchema,
    InsertTodoSchema,
    InsertTodosSchema,
    SearchTodosByTaskNameSchema
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
# 1. Validates the input (taskName and order)
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
            # Check if it's a single todo or multiple todos
            if "todos" in arguments and isinstance(arguments["todos"], list):
                # Multiple todos
                validated_data = CreateTodosSchema(**arguments)
                created_todos = todo_service.create_todos(validated_data.todos)
                if len(created_todos) == 1:
                    result = format_todo(created_todos[0])
                    return [TextContent(type="text", text=f"✅ Todo Created:\n\n{result}")]
                else:
                    result = format_todo_list(created_todos)
                    return [TextContent(type="text", text=f"✅ {len(created_todos)} Todos Created:\n\n{result}")]
            else:
                # Single todo - order is required
                if "order" not in arguments:
                    return [TextContent(type="text", text=create_error_response("Order is required for create-todo. Please provide an order (1-based) where to create the todo.")["content"][0]["text"])]
                validated_data = CreateTodoSchema(**arguments)
                new_todo = todo_service.create_todo(validated_data)
                result = format_todo(new_todo)
                return [TextContent(type="text", text=f"✅ Todo Created:\n\n{result}")]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to create todo: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "insert-todo":
        try:
            # Check if it's a single todo or multiple todos
            if "todos" in arguments and isinstance(arguments["todos"], list):
                # Multiple todos
                validated_data = InsertTodosSchema(**arguments)
                inserted_todos = todo_service.insert_todos(validated_data.todos)
                if len(inserted_todos) == 1:
                    result = format_todo(inserted_todos[0])
                    return [TextContent(type="text", text=f"✅ Todo Inserted:\n\n{result}")]
                else:
                    result = format_todo_list(inserted_todos)
                    return [TextContent(type="text", text=f"✅ {len(inserted_todos)} Todos Inserted:\n\n{result}")]
            else:
                # Single todo
                validated_data = InsertTodoSchema(**arguments)
                new_todo = todo_service.insert_todo(validated_data)
                result = format_todo(new_todo)
                return [TextContent(type="text", text=f"✅ Todo Inserted:\n\n{result}")]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to insert todo: {str(e)}")["content"][0]["text"])]
    
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
            return [TextContent(type="text", text=f"✓ Todo Completed:\n\n{result}")]
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
            return [TextContent(type="text", text=f"✅ Todo Deleted: \"{todo.task_name}\"")]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to delete todo: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "search-todos-by-task-name":
        try:
            validated_data = SearchTodosByTaskNameSchema(**arguments)
            todos = todo_service.search_by_task_name(validated_data.task_name)
            result = format_todo_list(todos)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to search todos: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "list-active-todos":
        result = safe_execute(
            lambda: format_todo_list(todo_service.get_active_todos()),
            "Failed to list active todos"
        )
        if isinstance(result, Exception):
            return [TextContent(type="text", text=create_error_response(result.args[0] if result.args else "Unknown error")["content"][0]["text"])]
        return [TextContent(type="text", text=result)]
    
    elif tool_name == "skip-todo":
        try:
            validated_data = SkipTodosSchema(**arguments)
            skipped_todos = todo_service.skip_todos(validated_data.ids)
            if len(skipped_todos) == 0:
                return [TextContent(type="text", text=create_error_response("No todos were skipped. All specified todos are either already completed or do not exist.")["content"][0]["text"])]
            elif len(skipped_todos) == 1:
                result = format_todo(skipped_todos[0])
                return [TextContent(type="text", text=f"⁉ Todo Skipped:\n\n{result}")]
            else:
                result = format_todo_list(skipped_todos)
                return [TextContent(type="text", text=f"⁉ {len(skipped_todos)} Todos Skipped:\n\n{result}")]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to skip todos: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "mark-todos-not-completed":
        try:
            validated_data = MarkTodosNotCompletedSchema(**arguments)
            updated_todos = todo_service.mark_todos_not_completed(validated_data.ids)
            if len(updated_todos) == 0:
                return [TextContent(type="text", text=create_error_response("No todos were updated. All specified todos do not exist.")["content"][0]["text"])]
            elif len(updated_todos) == 1:
                result = format_todo(updated_todos[0])
                return [TextContent(type="text", text=f"✗ Todo Marked as Not Completed:\n\n{result}")]
            else:
                result = format_todo_list(updated_todos)
                return [TextContent(type="text", text=f"✗ {len(updated_todos)} Todos Marked as Not Completed:\n\n{result}")]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to mark todos as not completed: {str(e)}")["content"][0]["text"])]
    
    elif tool_name == "read-next-todo":
        result = safe_execute(
            lambda: todo_service.get_next_todo_after_last_completed(),
            "Failed to get next todo after last completed"
        )
        if isinstance(result, Exception):
            return [TextContent(type="text", text=create_error_response(result.args[0] if result.args else "Unknown error")["content"][0]["text"])]
        if result is None:
            return [TextContent(type="text", text="No active todos found.")]
        return [TextContent(type="text", text=f"📖 Next Todo:\n\n{format_todo(result)}")]
    
    elif tool_name == "clear-todo-list":
        try:
            count = todo_service.clear_all_todos()
            if count == 0:
                return [TextContent(type="text", text="Todo list is already empty. No todos were deleted.")]
            else:
                return [TextContent(type="text", text=f"Cleared todo list: {count} todo(s) deleted.")]
        except Exception as e:
            return [TextContent(type="text", text=create_error_response(f"Failed to clear todo list: {str(e)}")["content"][0]["text"])]
    
    else:
        return [TextContent(type="text", text=create_error_response(f"Unknown tool: {tool_name}")["content"][0]["text"])]


# Register tools with proper schemas
# The MCP SDK needs to know about available tools
@server.list_tools()
async def list_tools_handler() -> list[Tool]:
    return [
        Tool(
            name="create-todo",
            description="Create one or more todo items at specific orders. Accepts either a single todo (taskName, order) or multiple todos (todos array). Order is required (1-based). For single todo, provide 'taskName' and 'order'. For multiple todos, provide 'todos' array with each having taskName and order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taskName": {"type": "string", "minLength": 1, "description": "Task name for single todo (use with order)"},
                    "order": {"type": "integer", "minimum": 1, "description": "Order to create at (1-based, required for single todo)"},
                    "todos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "taskName": {"type": "string", "minLength": 1},
                                "order": {"type": "integer", "minimum": 1, "description": "Order to create at (1-based, required)"}
                            },
                            "required": ["taskName", "order"]
                        },
                        "minItems": 1,
                        "description": "Array of todos to create (each with taskName and order). Use this for multiple todos."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="insert-todo",
            description="Insert one or more todo items at a specific order. Accepts either a single todo (taskName, optional order) or multiple todos (todos array). For single todo, provide 'taskName' and optionally 'order' (1-based). For multiple todos, provide 'todos' array.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taskName": {"type": "string", "minLength": 1, "description": "Task name for single todo"},
                    "order": {"type": "integer", "minimum": 1, "description": "Order to insert at (1-based, optional). If not provided, inserts at the end."},
                    "todos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "taskName": {"type": "string", "minLength": 1},
                                "order": {"type": "integer", "minimum": 1, "description": "Order to insert at (1-based, optional)"}
                            },
                            "required": ["taskName"]
                        },
                        "minItems": 1,
                        "description": "Array of todos to insert (each with taskName and optionally order). Use this for multiple todos."
                    }
                }
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
                    "id": {"type": "string", "description": "Todo ID (UUID format)"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="update-todo",
            description="Update a todo's task name or order. All fields are optional except id.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Todo ID (UUID format)"},
                    "taskName": {"type": "string", "minLength": 1, "description": "New task name (optional)"},
                    "order": {"type": "integer", "minimum": 1, "description": "New order/position (1-based, optional). If provided, the todo will be moved to this position."}
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
                    "id": {"type": "string", "description": "Todo ID (UUID format)"}
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
                    "id": {"type": "string", "description": "Todo ID (UUID format)"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="search-todos-by-task-name",
            description="Search todos by task name (case insensitive partial match)",
            inputSchema={
                "type": "object",
                "properties": {
                    "taskName": {"type": "string", "minLength": 1, "description": "Search term is required"}
                },
                "required": ["taskName"]
            }
        ),
        Tool(
            name="list-active-todos",
            description="List all non-completed todos",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="read-next-todo",
            description="Get the next todo after the most recently completed todo. Returns the first active (non-completed) todo that comes after the last completed todo in order. If no todos are completed, returns the first active todo in the list.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="skip-todo",
            description="Mark one or more non-completed todos as skipped. Skipped status can be overwritten by completing the todo later.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "description": "List of todo IDs to skip (at least one required, UUID format)"
                    }
                },
                "required": ["ids"]
            }
        ),
        Tool(
            name="mark-todos-not-completed",
            description="Mark one or more todos as not completed (active). This clears both completed and skipped status, making the todos active again.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "description": "List of todo IDs to mark as not completed (at least one required, UUID format)"
                    }
                },
                "required": ["ids"]
            }
        ),
        Tool(
            name="clear-todo-list",
            description="Clear all todos from the list. This permanently deletes all todos in the database.",
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
    except KeyboardInterrupt:
        print('Shutting down...', file=sys.stderr)
    except Exception as error:
        print(f"Failed to start Todo MCP Server: {error}", file=sys.stderr)
    finally:
        # Always close the database on exit
        database_service.close()


if __name__ == "__main__":
    asyncio.run(main())
