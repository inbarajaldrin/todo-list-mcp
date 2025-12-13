"""
TodoService.py

This service implements the core business logic for managing todos.
It acts as an intermediary between the data model and the database,
handling all CRUD operations and search functionality.

WHY A SERVICE LAYER?
- Separates business logic from database operations
- Provides a clean API for the application to work with
- Makes it easier to change the database implementation later
- Encapsulates complex operations into simple method calls
"""
from typing import Optional
from src.models.todo import (
    Todo, 
    create_todo, 
    CreateTodoSchema, 
    UpdateTodoSchema,
    InsertTodoSchema,
    InsertTodosSchema
)
from src.services.database_service import database_service


class TodoService:
    """
    TodoService Class
    
    This service follows the repository pattern to provide a clean
    interface for working with todos. It encapsulates all database
    operations and business logic in one place.
    """
    
    def create_todo(self, data: CreateTodoSchema) -> Todo:
        """
        Create a new todo at a specific order
        
        This method:
        1. Shifts existing todos at or after the order to make room
        2. Uses the factory function to create a new Todo object
        3. Persists it to the database at the specified order
        4. Returns the created Todo
        
        Args:
            data: Validated input data (task_name and order)
        
        Returns:
            The newly created Todo
        """
        # Get the database instance
        db = database_service.get_db()
        
        # Shift todos at or after the insert order to make room
        db.execute('''
            UPDATE todos
            SET "order" = "order" + 1
            WHERE "order" >= ?
        ''', (data.order,))
        
        # Use the factory function to create a Todo with the specified order
        todo = create_todo(data, order=data.order)
        
        # Prepare the SQL statement for inserting a new todo
        db.execute('''
            INSERT INTO todos (id, task_name, completed, skipped, "order")
            VALUES (?, ?, ?, ?, ?)
        ''', (
            todo.id,
            todo.task_name,
            1 if todo.completed else 0,
            1 if todo.skipped else 0,
            todo.order
        ))
        db.commit()
        
        # Return the created todo
        return todo
    
    def create_todos(self, todos_data: list) -> list[Todo]:
        """
        Create multiple todos at once at specific orders
        
        This method inserts todos in the order they appear in the list.
        Each todo must have an order specified, and existing todos will be shifted.
        
        Args:
            todos_data: List of validated todo data (task_name and order)
        
        Returns:
            List of newly created Todos
        """
        created_todos = []
        db = database_service.get_db()
        
        # Sort todos by order to process them in order
        sorted_todos = sorted(todos_data, key=lambda x: x.order)
        
        for data in sorted_todos:
            # Shift todos at or after the insert order
            db.execute('''
                UPDATE todos
                SET "order" = "order" + 1
                WHERE "order" >= ?
            ''', (data.order,))
            
            # Create and insert the todo
            todo = create_todo(data, order=data.order)
            db.execute('''
                INSERT INTO todos (id, task_name, completed, skipped, "order")
                VALUES (?, ?, ?, ?, ?)
            ''', (
                todo.id,
                todo.task_name,
                1 if todo.completed else 0,
                1 if todo.skipped else 0,
                todo.order
            ))
            created_todos.append(todo)
        
        db.commit()
        return created_todos
    
    def get_todo(self, id: str) -> Optional[Todo]:
        """
        Get a todo by ID
        
        This method:
        1. Queries the database for a todo with the given ID
        2. Converts the database row to a Todo object if found
        
        Args:
            id: The UUID of the todo to retrieve
        
        Returns:
            The Todo if found, None otherwise
        """
        db = database_service.get_db()
        
        # Use parameterized query to prevent SQL injection
        cursor = db.execute('SELECT * FROM todos WHERE id = ?', (id,))
        row = cursor.fetchone()
        
        # Return None if no todo was found
        if not row:
            return None
        
        # Convert the database row to a Todo object
        return self._row_to_todo(row)
    
    def get_all_todos(self) -> list[Todo]:
        """
        Get all todos
        
        This method returns all todos in the database ordered by their order.
        
        Returns:
            List of all Todos ordered by order
        """
        db = database_service.get_db()
        cursor = db.execute('SELECT * FROM todos ORDER BY "order" ASC')
        rows = cursor.fetchall()
        
        # Convert each database row to a Todo object
        return [self._row_to_todo(row) for row in rows]
    
    def get_active_todos(self) -> list[Todo]:
        """
        Get all active (non-completed) todos
        
        This method returns only todos that haven't been marked as completed.
        A todo is considered active when its completed field is 0.
        
        Returns:
            List of active Todos ordered by order
        """
        db = database_service.get_db()
        cursor = db.execute('SELECT * FROM todos WHERE completed = 0 ORDER BY "order" ASC')
        rows = cursor.fetchall()
        
        # Convert each database row to a Todo object
        return [self._row_to_todo(row) for row in rows]
    
    def update_todo(self, data: UpdateTodoSchema) -> Optional[Todo]:
        """
        Update a todo
        
        This method:
        1. Checks if the todo exists
        2. Updates the specified fields (title, description, order)
        3. If order is changed, shifts other todos appropriately
        4. Returns the updated todo
        
        Args:
            data: The update data (id required, task_name/order optional)
        
        Returns:
            The updated Todo if found, None otherwise
        """
        # First check if the todo exists
        todo = self.get_todo(data.id)
        if not todo:
            return None
        
        db = database_service.get_db()
        
        # Handle order change if provided and different from current
        if data.order is not None and data.order != todo.order:
            old_order = todo.order
            new_order = data.order
            
            if new_order > old_order:
                # Moving to a higher order: shift todos between old and new down by 1
                db.execute('''
                    UPDATE todos
                    SET "order" = "order" - 1
                    WHERE "order" > ? AND "order" <= ? AND id != ?
                ''', (old_order, new_order, todo.id))
            else:
                # Moving to a lower order: shift todos between new and old up by 1
                db.execute('''
                    UPDATE todos
                    SET "order" = "order" + 1
                    WHERE "order" >= ? AND "order" < ? AND id != ?
                ''', (new_order, old_order, todo.id))
        
        # Update with new values or keep existing ones if not provided
        new_order = data.order if data.order is not None else todo.order
        new_task_name = data.task_name if data.task_name else todo.task_name
        db.execute('''
            UPDATE todos
            SET task_name = ?, "order" = ?
            WHERE id = ?
        ''', (
            new_task_name,
            new_order,
            todo.id
        ))
        db.commit()
        
        # Return the updated todo
        return self.get_todo(todo.id)
    
    def update_todos(self, todos_data: list) -> list[Todo]:
        """
        Update multiple todos at once
        
        This method:
        1. Checks which todos exist
        2. Updates the specified fields for each todo
        3. Returns the list of updated todos
        
        Args:
            todos_data: List of validated update data (each with id, optional task_name)
        
        Returns:
            List of updated Todos (only those that were found and updated)
        """
        updated_todos = []
        db = database_service.get_db()
        
        for data in todos_data:
            # Check if at least one field is provided
            if not data.task_name:
                continue  # Skip if no fields to update
            
            # Check if the todo exists
            todo = self.get_todo(data.id)
            if not todo:
                continue  # Skip if todo doesn't exist
            
            # Update with new values or keep existing ones if not provided
            db.execute('''
                UPDATE todos
                SET task_name = ?
                WHERE id = ?
            ''', (
                data.task_name if data.task_name else todo.task_name,
                todo.id
            ))
            updated_todos.append(self.get_todo(todo.id))
        
        db.commit()
        return updated_todos
    
    def complete_todo(self, id: str) -> Optional[Todo]:
        """
        Mark a todo as completed
        
        This method:
        1. Checks if the todo exists
        2. Sets the completed flag to True
        3. Clears the skipped flag (completion overwrites skipped status)
        4. Returns the updated todo
        
        Args:
            id: The UUID of the todo to complete
        
        Returns:
            The updated Todo if found, None otherwise
        """
        # First check if the todo exists
        todo = self.get_todo(id)
        if not todo:
            return None
        
        db = database_service.get_db()
        
        # Set completed flag and clear skipped flag (completion overwrites skipped)
        db.execute('''
            UPDATE todos
            SET completed = 1, skipped = 0
            WHERE id = ?
        ''', (id,))
        db.commit()
        
        # Return the updated todo
        return self.get_todo(id)
    
    def skip_todos(self, ids: list[str]) -> list[Todo]:
        """
        Mark one or more todos as skipped (only non-completed ones)
        
        This method:
        1. Checks which todos exist and are not completed
        2. Sets the skipped flag for those todos
        3. Returns the list of skipped todos
        
        Args:
            ids: List of UUIDs of todos to skip
        
        Returns:
            List of skipped Todos (only non-completed ones)
        """
        skipped_todos = []
        db = database_service.get_db()
        
        for todo_id in ids:
            todo = self.get_todo(todo_id)
            # Only skip if todo exists and is not completed
            if todo and not todo.completed:
                db.execute('''
                    UPDATE todos
                    SET skipped = 1
                    WHERE id = ? AND completed = 0
                ''', (todo_id,))
                skipped_todos.append(self.get_todo(todo_id))
        
        db.commit()
        return skipped_todos
    
    def mark_todos_not_completed(self, ids: list[str]) -> list[Todo]:
        """
        Mark one or more todos as not completed (active)
        
        This method:
        1. Checks which todos exist
        2. Clears both completed and skipped flags for those todos
        3. Returns the list of updated todos
        
        Args:
            ids: List of UUIDs of todos to mark as not completed
        
        Returns:
            List of updated Todos (marked as not completed)
        """
        updated_todos = []
        db = database_service.get_db()
        
        for todo_id in ids:
            todo = self.get_todo(todo_id)
            # Only update if todo exists
            if todo:
                db.execute('''
                    UPDATE todos
                    SET completed = 0, skipped = 0
                    WHERE id = ?
                ''', (todo_id,))
                updated_todos.append(self.get_todo(todo_id))
        
        db.commit()
        return updated_todos
    
    def delete_todo(self, id: str) -> bool:
        """
        Delete a todo
        
        This method removes a todo from the database permanently.
        
        Args:
            id: The UUID of the todo to delete
        
        Returns:
            True if deleted, False if not found or not deleted
        """
        db = database_service.get_db()
        cursor = db.execute('DELETE FROM todos WHERE id = ?', (id,))
        db.commit()
        
        # Check if any rows were affected
        return cursor.rowcount > 0
    
    def clear_all_todos(self) -> int:
        """
        Clear all todos from the database
        
        This method removes all todos from the database permanently.
        
        Returns:
            Number of todos that were deleted
        """
        db = database_service.get_db()
        cursor = db.execute('DELETE FROM todos')
        db.commit()
        
        # Return the number of rows deleted
        return cursor.rowcount
    
    def search_by_task_name(self, task_name: str) -> list[Todo]:
        """
        Search todos by task name
        
        This method performs a case-insensitive partial match search
        on todo task names.
        
        Args:
            task_name: The search term to look for in task names
        
        Returns:
            List of matching Todos
        """
        # Add wildcards to the search term for partial matching
        search_term = f'%{task_name}%'
        
        db = database_service.get_db()
        
        # COLLATE NOCASE makes the search case-insensitive
        cursor = db.execute('SELECT * FROM todos WHERE task_name LIKE ? COLLATE NOCASE ORDER BY "order" ASC', (search_term,))
        rows = cursor.fetchall()
        
        return [self._row_to_todo(row) for row in rows]
    
    def summarize_active_todos(self) -> str:
        """
        Generate a summary of active todos
        
        This method creates a markdown-formatted summary of all active todos.
        
        WHY RETURN FORMATTED STRING?
        - Provides ready-to-display content for the MCP client
        - Encapsulates formatting logic in the service
        - Makes it easy for LLMs to present a readable summary
        
        Returns:
            Markdown-formatted summary string
        """
        active_todos = self.get_active_todos()
        
        # Handle the case when there are no active todos
        if len(active_todos) == 0:
            return "No active todos found."
        
        # Create a bulleted list of todo task names
        summary = '\n'.join(f'- {todo.task_name}' for todo in active_todos)
        return f"# Active Todos Summary\n\nThere are {len(active_todos)} active todos:\n\n{summary}"
    
    def insert_todo(self, data: InsertTodoSchema) -> Todo:
        """
        Insert a todo at a specific order
        
        This method:
        1. Determines the order (if not provided, inserts at end)
        2. Shifts existing todos to make room if needed
        3. Creates and inserts the new todo
        4. Returns the created todo
        
        Args:
            data: Validated input data (task_name, optional order)
        
        Returns:
            The newly inserted Todo
        """
        db = database_service.get_db()
        
        # Determine the order
        if data.order is not None:
            # Insert at specific order (1-based)
            insert_order = data.order
        else:
            # Insert at the end
            cursor = db.execute('SELECT COALESCE(MAX("order"), 0) FROM todos')
            max_order = cursor.fetchone()[0]
            insert_order = max_order + 1
        
        # Shift todos at or after the insert order to make room
        db.execute('''
            UPDATE todos
            SET "order" = "order" + 1
            WHERE "order" >= ?
        ''', (insert_order,))
        
        # Create the todo with the specified order
        todo = create_todo(CreateTodoSchema(task_name=data.task_name, order=insert_order), order=insert_order)
        
        # Insert the new todo
        db.execute('''
            INSERT INTO todos (id, task_name, completed, skipped, "order")
            VALUES (?, ?, ?, ?, ?)
        ''', (
            todo.id,
            todo.task_name,
            1 if todo.completed else 0,
            1 if todo.skipped else 0,
            todo.order
        ))
        db.commit()
        
        return todo
    
    def insert_todos(self, todos_data: list[InsertTodoSchema]) -> list[Todo]:
        """
        Insert multiple todos at specific orders
        
        This method inserts todos in the order they appear in the list.
        If orders are specified, they are inserted at those orders (shifting others).
        If not specified, they are inserted at the end.
        
        Args:
            todos_data: List of validated todo data with optional orders
        
        Returns:
            List of newly inserted Todos
        """
        db = database_service.get_db()
        inserted_todos = []
        
        # Sort todos by order (None orders go to end)
        sorted_todos = sorted(todos_data, key=lambda x: (x.order is None, x.order or 0))
        
        for data in sorted_todos:
            # Determine order
            if data.order is not None:
                insert_order = data.order
            else:
                # Get current max order
                cursor = db.execute('SELECT COALESCE(MAX("order"), 0) FROM todos')
                max_order = cursor.fetchone()[0]
                insert_order = max_order + 1
            
            # Shift todos at or after the insert order
            db.execute('''
                UPDATE todos
                SET "order" = "order" + 1
                WHERE "order" >= ?
            ''', (insert_order,))
            
            # Create and insert the todo
            todo = create_todo(CreateTodoSchema(task_name=data.task_name, order=insert_order), order=insert_order)
            db.execute('''
                INSERT INTO todos (id, task_name, completed, skipped, "order")
                VALUES (?, ?, ?, ?, ?)
            ''', (
                todo.id,
                todo.task_name,
                1 if todo.completed else 0,
                1 if todo.skipped else 0,
                todo.order
            ))
            inserted_todos.append(todo)
        
        db.commit()
        return inserted_todos
    
    def get_next_todo_after_last_completed(self) -> Optional[Todo]:
        """
        Get the next todo after the most recently completed todo
        
        This method:
        1. Finds the most recently completed todo (by order, highest order among completed)
        2. Gets the next todo in order that is not completed
        3. If no todos are completed, returns the first active todo
        4. Returns None if there's no next todo or no active todos
        
        Returns:
            The next Todo after the last completed one, or the first active todo if none are completed, or None if not found
        """
        db = database_service.get_db()
        
        # Find the most recently completed todo (highest order among completed)
        cursor = db.execute('''
            SELECT * FROM todos 
            WHERE completed = 1 
            ORDER BY "order" DESC 
            LIMIT 1
        ''')
        row = cursor.fetchone()
        
        if not row:
            # No completed todos exist, return the first active todo
            cursor = db.execute('''
                SELECT * FROM todos 
                WHERE completed = 0 
                ORDER BY "order" ASC 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            if not row:
                # No active todos found
                return None
            return self._row_to_todo(row)
        
        last_completed = self._row_to_todo(row)
        
        # Find the next todo in order that is not completed
        cursor = db.execute('''
            SELECT * FROM todos 
            WHERE "order" > ? AND completed = 0 
            ORDER BY "order" ASC 
            LIMIT 1
        ''', (last_completed.order,))
        
        row = cursor.fetchone()
        
        if not row:
            # No next todo found
            return None
        
        return self._row_to_todo(row)
    
    def _row_to_todo(self, row: tuple) -> Todo:
        """
        Helper to convert a database row to a Todo object
        
        This private method handles the conversion between the database
        representation and the application model.
        
        WHY SEPARATE THIS LOGIC?
        - Avoids repeating the conversion code in multiple methods
        - Creates a single place to update if the model changes
        - Isolates database-specific knowledge from the rest of the code
        
        Args:
            row: The database row data (tuple from sqlite3)
        
        Returns:
            A properly formatted Todo object
        """
        # SQLite returns rows as tuples: (id, task_name, completed, skipped, order)
        # New simplified schema (5 columns)
        return Todo(
            id=row[0],
            task_name=row[1],
            completed=bool(row[2]),  # Convert integer (0/1) to boolean
            skipped=bool(row[3]),    # Convert integer (0/1) to boolean
            order=row[4]
        )


# Create a singleton instance for use throughout the application
todo_service = TodoService()

