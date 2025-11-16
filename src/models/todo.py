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
    """
    id: str
    title: str
    description: str  # Markdown format
    completed: bool  # Computed from completedAt for backward compatibility
    completed_at: Optional[str] = Field(None, alias="completedAt")  # ISO timestamp when completed, None if not completed
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    
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

# Schema for creating a new todo - requires title and description
class CreateTodoSchema(BaseModel):
    title: str = Field(..., min_length=1, description="Title is required")
    description: str = Field(..., min_length=1, description="Description is required")


# Schema for updating a todo - requires ID, title and description are optional
class UpdateTodoSchema(BaseModel):
    id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', 
                     description="Invalid Todo ID")
    title: Optional[str] = Field(None, min_length=1, description="Title is required")
    description: Optional[str] = Field(None, min_length=1, description="Description is required")


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


def create_todo(data: CreateTodoSchema) -> Todo:
    """
    Factory Function: create_todo
    
    WHY USE A FACTORY FUNCTION?
    - Centralizes the creation logic in one place
    - Ensures all required fields are set with proper default values
    - Guarantees all todos have the same structure
    - Makes it easy to change the implementation without affecting code that creates todos
    
    Args:
        data: The validated input data (title and description)
    
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
        created_at=now,
        updated_at=now
    )

