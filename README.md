# Todo List MCP Server (Python)

A Model Context Protocol (MCP) server that provides a comprehensive API for managing todo items. This is a Python port of the original [Node.js implementation](https://github.com/RegiByte/todo-list-mcp).

> **Note**: This is a Python rewrite of the original TypeScript/Node.js implementation by [RegiByte](https://github.com/RegiByte/todo-list-mcp). All credit for the original design and architecture goes to the original repository.

## Features

- Create, insert, update, complete, delete, and skip todos
- Bulk create multiple todos at once
- Insert todos at specific orders in the list
- Search todos by title or creation date
- List active todos
- Clear entire todo list
- SQLite database for persistence

## Tools

1. `create-todo` - Create one or more todo items
2. `insert-todo` - Insert one or more todo items at a specific order
3. `list-todos` - List all todos
4. `get-todo` - Get a specific todo by ID
5. `update-todo` - Update a todo's title or description
6. `complete-todo` - Mark a todo as completed
7. `delete-todo` - Delete a todo
8. `skip-todo` - Mark one or more non-completed todos as skipped
9. `search-todos-by-title` - Search todos by title (case-insensitive)
10. `search-todos-by-date` - Search todos by creation date (YYYY-MM-DD)
11. `list-active-todos` - List all non-completed todos
12. `read-next-todo` - Get the next todo after the most recently completed todo
13. `mark-todos-not-completed` - Mark one or more todos as not completed (active)
14. `clear-todo-list` - Clear all todos from the list

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd todo-list-mcp

# Install dependencies with uv
uv sync

# Or with pip
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
python server.py
```

### Configuring with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "todo": {
      "command": "python",
      "args": ["/absolute/path/to/todo-list-mcp/server.py"]
    }
  }
}
```

### Configuring with Cursor

- Go to "Cursor Settings" -> MCP
- Add a new MCP server with a "command" type
- Command: `python`
- Args: `/absolute/path/to/todo-list-mcp/server.py`

## Project Structure

```
src/
├── models/       # Data structures and validation schemas
├── services/     # Business logic and database operations
├── utils/        # Helper functions and formatters
└── config.py     # Configuration settings
```

## License

MIT
