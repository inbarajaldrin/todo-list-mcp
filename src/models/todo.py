"""
Todo.py

This file defines the core data model for our Todo application, along with validation
schemas and a factory function for creating new Todo instances.

WHY USE PYDANTIC?
- Pydantic provides runtime type validation, ensuring our data meets specific requirements
- Using models creates a clear contract for each operation's input requirements
- Error messages are automatically generated with clear validation feedback
- Python type hints give us both static type checking and runtime type safety
- Models can be converted to JSON Schema, which is useful for MCP clients
"""
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Todo(BaseModel):
    """
    Todo Interface
    
    This defines the structure of a Todo item in our application.
    We've designed it with several important considerations:
    - IDs use UUID for uniqueness across systems
    - Simple task_name field for the todo content
    - Completion and skipped status tracked as boolean flags
    - Order field determines the position in the list
    """
    id: str
    task_name: str = Field(alias="taskName")  # The task name/content
    completed: bool = False  # Whether the todo is completed
    skipped: bool = False  # Whether the todo is skipped
    order: int = Field(alias="order")  # Position/order in the list
    
    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase


# Input Validation Schemas
# 
# These schemas define the requirements for different operations.
# Each schema serves as both documentation and runtime validation.
# 
# WHY SEPARATE SCHEMAS?
# - Different operations have different validation requirements
# - Keeps validation focused on only what's needed for each operation
# - Makes the API more intuitive by clearly defining what each operation expects

# Schema for creating a new todo - requires task_name and order
class CreateTodoSchema(BaseModel):
    task_name: str = Field(..., min_length=1, description="Task name is required", alias="taskName")
    order: int = Field(..., ge=1, description="Order/position to create at (1-based, required)")


# Schema for creating multiple todos at once
class CreateTodosSchema(BaseModel):
    todos: list[CreateTodoSchema] = Field(..., min_items=1, description="List of todos to create (at least one required, each must have order)")


# Schema for skipping todos - accepts one or more IDs
class SkipTodosSchema(BaseModel):
    ids: list[str] = Field(..., min_items=1, description="List of todo IDs to skip (at least one required)")


# Schema for marking todos as not completed - accepts one or more IDs
class MarkTodosNotCompletedSchema(BaseModel):
    ids: list[str] = Field(..., min_items=1, description="List of todo IDs to mark as not completed (at least one required)")


# Schema for updating a todo - requires ID, task_name and order are optional
class UpdateTodoSchema(BaseModel):
    id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', 
                     description="Invalid Todo ID")
    task_name: Optional[str] = Field(None, min_length=1, description="Task name is optional", alias="taskName")
    order: Optional[int] = Field(None, ge=1, description="Order/position to move todo to (1-based, optional)")


# Schema for completing a todo - requires only ID
class CompleteTodoSchema(BaseModel):
    id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                    description="Invalid Todo ID")


# Schema for deleting a todo - requires only ID
class DeleteTodoSchema(BaseModel):
    id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                    description="Invalid Todo ID")


# Schema for searching todos by task name - requires search term
class SearchTodosByTaskNameSchema(BaseModel):
    task_name: str = Field(..., min_length=1, description="Search term is required", alias="taskName")


# Schema for inserting a todo at a specific order
class InsertTodoSchema(BaseModel):
    task_name: str = Field(..., min_length=1, description="Task name is required", alias="taskName")
    order: Optional[int] = Field(None, ge=1, description="Order/position to insert at (1-based). If not provided, inserts at the end.")


# Schema for inserting multiple todos at specific orders
class InsertTodosSchema(BaseModel):
    todos: list[InsertTodoSchema] = Field(..., min_items=1, description="List of todos to insert (at least one required)")


def create_todo(data: CreateTodoSchema, order: Optional[int] = None) -> Todo:
    """
    Factory Function: create_todo
    
    WHY USE A FACTORY FUNCTION?
    - Centralizes the creation logic in one place
    - Ensures all required fields are set with proper default values
    - Guarantees all todos have the same structure
    - Makes it easy to change the implementation without affecting code that creates todos
    
    Args:
        data: The validated input data (task_name and order)
        order: Optional order override. If None, uses data.order.
    
    Returns:
        A fully formed Todo object with generated ID
    """
    return Todo(
        id=str(uuid4()),
        task_name=data.task_name,
        completed=False,
        skipped=False,
        order=order if order is not None else data.order
    )

