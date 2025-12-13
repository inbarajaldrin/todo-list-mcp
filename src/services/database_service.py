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
        - Boolean flags for completion and skipped status
        - Order field for positioning in the list
        """
        # Check if old table exists with old schema
        cursor = self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='todos'")
        old_table_exists = cursor.fetchone() is not None
        
        if old_table_exists:
            # Check if we need to migrate from old schema
            cursor = self.db.execute("PRAGMA table_info(todos)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'title' in columns or 'description' in columns or 'createdAt' in columns:
                # Migrate from old schema to new schema
                self._migrate_to_new_schema()
        else:
            # Create new table with simplified schema
            self.db.execute('''
                CREATE TABLE todos (
                    id TEXT PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0, -- 0 = not completed, 1 = completed
                    skipped INTEGER NOT NULL DEFAULT 0, -- 0 = not skipped, 1 = skipped
                    "order" INTEGER NOT NULL DEFAULT 0 -- Order/position in the list
                )
            ''')
            self.db.commit()
    
    def _migrate_to_new_schema(self):
        """
        Migrate from old schema (with timestamps, title, description) to new schema (task_name only)
        """
        # Create new table with simplified schema
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS todos_new (
                id TEXT PRIMARY KEY,
                task_name TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                skipped INTEGER NOT NULL DEFAULT 0,
                "order" INTEGER NOT NULL DEFAULT 0
            )
        ''')
        
        # Migrate data: combine title and description into task_name
        try:
            cursor = self.db.execute('''
                SELECT id, title, description, 
                       CASE WHEN completedAt IS NOT NULL THEN 1 ELSE 0 END as completed,
                       CASE WHEN skippedAt IS NOT NULL THEN 1 ELSE 0 END as skipped,
                       "order"
                FROM todos
            ''')
            
            for row in cursor.fetchall():
                todo_id, title, description, completed, skipped, order = row
                # Combine title and description into task_name
                task_name = f"{title}"
                if description:
                    task_name = f"{title}: {description}" if title else description
                
                self.db.execute('''
                    INSERT INTO todos_new (id, task_name, completed, skipped, "order")
                    VALUES (?, ?, ?, ?, ?)
                ''', (todo_id, task_name, completed, skipped, order or 0))
            
            # Drop old table and rename new table
            self.db.execute('DROP TABLE todos')
            self.db.execute('ALTER TABLE todos_new RENAME TO todos')
            self.db.commit()
        except sqlite3.OperationalError as e:
            # If migration fails, just create the new table structure
            # This handles the case where the table structure is already updated
            self.db.rollback()
            try:
                self.db.execute('DROP TABLE IF EXISTS todos_new')
            except:
                pass
    
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

