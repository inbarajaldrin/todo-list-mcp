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
from datetime import datetime
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class Todo(BaseModel):
    """
    Todo Interface
    
    This defines the structure of a Todo item in our application.
    We've designed it with several important considerations:
    - IDs use UUID for uniqueness across systems
    - Timestamps track creation and updates for data lifecycle management
    - Description supports markdown for rich text formatting
    - Completion status is tracked both as a boolean flag and with a timestamp
    - Skipped status is tracked with a timestamp (can be overwritten by completion)
    - Order field determines the position in the list
    """
    id: str
    title: str
    description: str  # Markdown format
    completed: bool  # Computed from completedAt for backward compatibility
    completed_at: Optional[str] = Field(None, alias="completedAt")  # ISO timestamp when completed, None if not completed
    skipped: bool = False  # Computed from skippedAt
    skipped_at: Optional[str] = Field(None, alias="skippedAt")  # ISO timestamp when skipped, None if not skipped
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
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

# Schema for creating a new todo - requires title, description, and order
class CreateTodoSchema(BaseModel):
    title: str = Field(..., min_length=1, description="Title is required")
    description: str = Field(..., min_length=1, description="Description is required")
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


# Schema for updating a todo - requires ID, title, description, and order are optional
class UpdateTodoSchema(BaseModel):
    id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', 
                     description="Invalid Todo ID")
    title: Optional[str] = Field(None, min_length=1, description="Title is optional")
    description: Optional[str] = Field(None, min_length=1, description="Description is optional")
    order: Optional[int] = Field(None, ge=1, description="Order/position to move todo to (1-based, optional)")


# Schema for completing a todo - requires only ID
class CompleteTodoSchema(BaseModel):
    id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                    description="Invalid Todo ID")


# Schema for deleting a todo - requires only ID
class DeleteTodoSchema(BaseModel):
    id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                    description="Invalid Todo ID")


# Schema for searching todos by title - requires search term
class SearchTodosByTitleSchema(BaseModel):
    title: str = Field(..., min_length=1, description="Search term is required")


# Schema for searching todos by date - requires date in YYYY-MM-DD format
class SearchTodosByDateSchema(BaseModel):
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="Date must be in YYYY-MM-DD format")


# Schema for inserting a todo at a specific order
class InsertTodoSchema(BaseModel):
    title: str = Field(..., min_length=1, description="Title is required")
    description: str = Field(..., min_length=1, description="Description is required")
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
        data: The validated input data (title, description, and order)
        order: Optional order override. If None, uses data.order.
    
    Returns:
        A fully formed Todo object with generated ID and timestamps
    """
    now = datetime.utcnow().isoformat()
    return Todo(
        id=str(uuid4()),
        title=data.title,
        description=data.description,
        completed=False,
        completed_at=None,
        skipped=False,
        skipped_at=None,
        created_at=now,
        updated_at=now,
        order=order if order is not None else data.order
    )

