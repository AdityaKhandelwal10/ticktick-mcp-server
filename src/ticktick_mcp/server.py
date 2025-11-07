"""MCP server implementation for TickTick."""

import os
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import AnyUrl
from .client import TickTickClient


app = Server("ticktick-mcp")

# Initialize TickTick client
client_id = os.getenv("TICKTICK_CLIENT_ID")
client_secret = os.getenv("TICKTICK_CLIENT_SECRET")

if not client_id or not client_secret:
    raise ValueError(
        "Missing required environment variables:\n"
        "  TICKTICK_CLIENT_ID\n"
        "  TICKTICK_CLIENT_SECRET\n"
        "Get these from: https://developer.ticktick.com"
    )

ticktick = TickTickClient(client_id, client_secret)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="list_projects",
            description="List all TickTick projects",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_tasks",
            description="List tasks, optionally filtered by project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Optional project ID to filter tasks"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="create_task",
            description="Create a new task in TickTick",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Task description/content"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Optional project ID to add task to"
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="complete_task",
            description="Mark a task as complete",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to complete"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project ID the task belongs to"
                    }
                },
                "required": ["task_id", "project_id"]
            }
        ),
        Tool(
            name="delete_task",
            description="Delete a task permanently",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to delete"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project ID the task belongs to"
                    }
                },
                "required": ["task_id", "project_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    
    try:
        if name == "list_projects":
            projects = await ticktick.get_projects()
            result = "\n".join([f"- {p['name']} (ID: {p['id']})" for p in projects])
            return [TextContent(type="text", text=result or "No projects found")]
        
        elif name == "list_tasks":
            project_id = arguments.get("project_id")
            tasks = await ticktick.get_tasks(project_id)
            
            if not tasks:
                return [TextContent(type="text", text="No tasks found")]
            
            result = []
            for task in tasks:
                status = "✓" if task.get("status") == 2 else "○"
                title = task.get("title", "Untitled")
                task_id = task.get("id", "")
                project = task.get("projectId", "")
                result.append(f"{status} {title} (ID: {task_id}, Project: {project})")
            
            return [TextContent(type="text", text="\n".join(result))]
        
        elif name == "create_task":
            title = arguments["title"]
            content = arguments.get("content", "")
            project_id = arguments.get("project_id")
            
            task = await ticktick.create_task(title, content, project_id)
            return [TextContent(
                type="text",
                text=f"Created task: {task['title']} (ID: {task['id']})"
            )]
        
        elif name == "complete_task":
            task_id = arguments["task_id"]
            project_id = arguments["project_id"]
            
            await ticktick.complete_task(task_id, project_id)
            return [TextContent(type="text", text=f"Task {task_id} marked as complete")]
        
        elif name == "delete_task":
            task_id = arguments["task_id"]
            project_id = arguments["project_id"]
            
            await ticktick.delete_task(task_id, project_id)
            return [TextContent(type="text", text=f"Task {task_id} deleted")]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

