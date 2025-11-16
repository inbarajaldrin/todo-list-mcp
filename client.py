#!/usr/bin/env python3
"""
Python MCP client for the Todo MCP Server.

Usage:
    python client.py
"""

import asyncio
import subprocess
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    server_path = script_dir / "dist" / "index.js"
    
    if not server_path.exists():
        print(f"Error: Server file not found at {server_path}")
        print("Please run 'npm run build' first to build the server.")
        return
    
    # Create server parameters for stdio transport
    server_params = StdioServerParameters(
        command="node",
        args=[str(server_path)],
    )
    
    # Connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("✅ Connected to Todo MCP Server")
            
            # List available tools
            print("\n📋 Listing available tools...")
            tools_result = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools_result.tools]}")
            
            # Create a test todo
            print("\n➕ Creating a test todo...")
            create_result = await session.call_tool(
                "create-todo",
                arguments={
                    "title": "Test from Python",
                    "description": "# Test Todo\n\nThis is a test from the Python MCP client."
                }
            )
            print(create_result.content[0].text if create_result.content else "No content")
            
            # List all todos
            print("\n📝 Listing all todos...")
            list_result = await session.call_tool("list-todos", arguments={})
            print(list_result.content[0].text if list_result.content else "No content")
            
            print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
