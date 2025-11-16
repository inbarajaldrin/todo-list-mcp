"""
config.py

This file manages the application configuration settings.
It provides a centralized place for all configuration values,
making them easier to change and maintain.

WHY A SEPARATE CONFIG FILE?
- Single source of truth for configuration values
- Easy to update settings without searching through the codebase
- Allows for environment-specific overrides
- Makes configuration values available throughout the application
"""
import os
from pathlib import Path

# Database configuration defaults
# 
# We use the user's home directory for database storage by default,
# which provides several advantages:
# - Works across different operating systems
# - Available without special permissions
# - Persists across application restarts
# - Doesn't get deleted when updating the application
DEFAULT_DB_FOLDER = Path.home() / '.todo-list-mcp'
DEFAULT_DB_FILE = 'todos.sqlite'


class DatabaseConfig:
    """
    Database configuration class
    
    This class provides access to database configuration settings.
    It uses environment variables when available, falling back to defaults.
    
    WHY USE ENVIRONMENT VARIABLES?
    - Allows configuration without changing code
    - Follows the 12-factor app methodology for configuration
    - Enables different settings per environment (dev, test, prod)
    - Keeps sensitive information out of the code
    """
    def __init__(self):
        self.folder = Path(os.getenv('TODO_DB_FOLDER', str(DEFAULT_DB_FOLDER)))
        self.filename = os.getenv('TODO_DB_FILE', DEFAULT_DB_FILE)
    
    @property
    def path(self) -> Path:
        """
        Full path to the database file
        
        This property computes the complete path dynamically,
        ensuring consistency even if the folder or filename change.
        """
        return self.folder / self.filename


class Config:
    """Application configuration object"""
    def __init__(self):
        self.db = DatabaseConfig()


# Create a singleton config instance
config = Config()


def ensure_db_folder():
    """
    Ensure the database folder exists
    
    This utility function makes sure the folder for the database file exists,
    creating it if necessary. This prevents errors when trying to open the
    database file in a non-existent directory.
    """
    config.db.folder.mkdir(parents=True, exist_ok=True)

