"""
formatters.py

This file contains utility functions for formatting data in the application.
These utilities handle the transformation of internal data structures into
human-readable formats appropriate for display to LLMs and users.

WHY SEPARATE FORMATTERS?
- Keeps formatting logic separate from business logic
- Allows consistent formatting across the application
- Makes it easier to change display formats without affecting core functionality
- Centralizes presentation concerns in one place
"""
from src.models.todo import Todo


def format_todo(todo: Todo) -> str:
    """
    Format a todo item to a readable string representation
    
    This formatter converts a Todo object into a markdown-formatted string
    with clear visual indicators for completion status (emojis).
    
    WHY USE MARKDOWN?
    - Provides structured, readable output
    - Works well with LLMs which understand markdown syntax
    - Allows rich formatting like headers, lists, and emphasis
    - Can be displayed directly in many UI contexts
    
    Args:
        todo: The Todo object to format
    
    Returns:
        A markdown-formatted string representation
    """
    # Determine status emoji
    if todo.completed:
        status_emoji = '✓'
    elif todo.skipped:
        status_emoji = '⁉'
    else:
        status_emoji = '✗'
    
    status_text = ""
    if todo.completed:
        status_text = "Status: Completed"
    elif todo.skipped:
        status_text = "Status: Skipped"
    else:
        status_text = "Status: Not completed"
    
    return f"""
## {todo.order}. {todo.task_name} {status_emoji}

Order: {todo.order}
ID: {todo.id}
{status_text}
""".strip()


def format_todo_list(todos: list[Todo]) -> str:
    """
    Format a list of todos to a readable string representation
    
    This formatter takes a list of Todo objects and creates a complete
    markdown document with a title and formatted entries.
    
    Args:
        todos: List of Todo objects to format
    
    Returns:
        A markdown-formatted string with the complete list
    """
    if len(todos) == 0:
        return "No todos found."
    
    todo_items = '\n\n---\n\n'.join(format_todo(todo) for todo in todos)
    return f"# Todo List ({len(todos)} items)\n\n{todo_items}"


def create_success_response(message: str) -> dict:
    """
    Create success response for MCP tool calls
    
    This utility formats successful responses according to the MCP protocol.
    It wraps the message in the expected content structure.
    
    WHY THIS FORMAT?
    - Follows the MCP protocol's expected response structure
    - Allows the message to be properly displayed by MCP clients
    - Clearly indicates success status
    
    Args:
        message: The success message to include
    
    Returns:
        A properly formatted MCP response object
    """
    return {
        "content": [
            {
                "type": "text",
                "text": message,
            },
        ],
    }


def create_error_response(message: str) -> dict:
    """
    Create error response for MCP tool calls
    
    This utility formats error responses according to the MCP protocol.
    It includes the isError flag to indicate failure.
    
    Args:
        message: The error message to include
    
    Returns:
        A properly formatted MCP error response object
    """
    return {
        "content": [
            {
                "type": "text",
                "text": message,
            },
        ],
        "isError": True,
    }

