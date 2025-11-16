# Todo List MCP Server (Python)

A Model Context Protocol (MCP) server that provides a comprehensive API for managing todo items. This is a Python port of the original [Node.js implementation](https://github.com/RegiByte/todo-list-mcp).

> **Note**: This is a Python rewrite of the original TypeScript/Node.js implementation by [RegiByte](https://github.com/RegiByte/todo-list-mcp). All credit for the original design and architecture goes to the original repository.

## Features

- Create, update, complete, and delete todos
- Search todos by title or creation date
- List active todos and generate summaries
- SQLite database for persistence

## Tools

1. `create-todo` - Create a new todo item
2. `list-todos` - List all todos
3. `get-todo` - Get a specific todo by ID
4. `update-todo` - Update a todo's title or description
5. `complete-todo` - Mark a todo as completed
6. `delete-todo` - Delete a todo
7. `search-todos-by-title` - Search todos by title (case-insensitive)
8. `search-todos-by-date` - Search todos by creation date (YYYY-MM-DD)
9. `list-active-todos` - List all non-completed todos
10. `summarize-active-todos` - Generate a summary of active todos

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
