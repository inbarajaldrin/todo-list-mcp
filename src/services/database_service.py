"""
DatabaseService.py

This file implements a lightweight SQLite database service for the Todo application.

WHY SQLITE?
- SQLite is perfect for small to medium applications like this one
- Requires no separate database server (file-based)
- ACID compliant and reliable
- Minimal configuration required
- Easy to install with minimal dependencies
"""
import sqlite3
from pathlib import Path
from src.config import config, ensure_db_folder


class DatabaseService:
    """
    DatabaseService Class
    
    This service manages the SQLite database connection and schema.
    It follows the singleton pattern to ensure only one database connection exists.
    
    WHY SINGLETON PATTERN?
    - Prevents multiple database connections which could lead to conflicts
    - Provides a central access point to the database throughout the application
    - Makes it easier to manage connection lifecycle (open/close)
    """
    def __init__(self):
        # Ensure the database folder exists before trying to create the database
        ensure_db_folder()
        
        # Initialize the database with the configured path
        self.db = sqlite3.connect(str(config.db.path), check_same_thread=False)
        
        # Set pragmas for performance and safety:
        # - WAL (Write-Ahead Logging): Improves concurrent access performance
        # - foreign_keys: Ensures referential integrity (useful for future expansion)
        self.db.execute('PRAGMA journal_mode = WAL')
        self.db.execute('PRAGMA foreign_keys = ON')
        
        # Initialize the database schema when service is created
        self._init_schema()
    
    def _init_schema(self):
        """
        Initialize the database schema
        
        This creates the todos table if it doesn't already exist.
        The schema design incorporates:
        - TEXT primary key for UUID compatibility
        - NULL completedAt to represent incomplete todos
        - Timestamp fields for tracking creation and updates
        """
        # Create todos table if it doesn't exist
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                completedAt TEXT NULL, -- ISO timestamp, NULL if not completed
                createdAt TEXT NOT NULL,
                updatedAt TEXT NOT NULL
            )
        ''')
        self.db.commit()
    
    def get_db(self) -> sqlite3.Connection:
        """
        Get the database instance
        
        This allows other services to access the database for operations.
        
        Returns:
            The SQLite database connection
        """
        return self.db
    
    def close(self):
        """
        Close the database connection
        
        This should be called when shutting down the application to ensure
        all data is properly saved and resources are released.
        """
        self.db.close()


# Create a singleton instance that will be used throughout the application
database_service = DatabaseService()

