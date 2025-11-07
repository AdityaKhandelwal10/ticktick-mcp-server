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
        ),
        Tool(
            name="update_task",
            description="Update an existing task (title, content, priority, due date, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to update"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project ID the task belongs to"
                    },
                    "title": {
                        "type": "string",
                        "description": "New task title"
                    },
                    "content": {
                        "type": "string",
                        "description": "New task description/content"
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Priority level: 0=none, 1=low, 3=medium, 5=high"
                    },
                    "dueDate": {
                        "type": "string",
                        "description": "Due date in ISO format (e.g., 2024-12-31T10:00:00Z)"
                    }
                },
                "required": ["task_id", "project_id"]
            }
        ),
        Tool(
            name="create_project",
            description="Create a new project/list",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "color": {
                        "type": "string",
                        "description": "Optional color for the project"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="search_tasks",
            description="Search for tasks by keyword in title or content",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Search keyword"
                    }
                },
                "required": ["keyword"]
            }
        ),
        Tool(
            name="get_tasks_today",
            description="Get all tasks due today",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_tasks_overdue",
            description="Get all overdue tasks",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_tasks_by_priority",
            description="Get tasks filtered by priority level",
            inputSchema={
                "type": "object",
                "properties": {
                    "priority": {
                        "type": "integer",
                        "description": "Priority level: 0=none, 1=low, 3=medium, 5=high"
                    }
                },
                "required": ["priority"]
            }
        ),
        Tool(
            name="list_tags",
            description="List all tags used in tasks",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="add_tag_to_task",
            description="Add a tag to a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project ID the task belongs to"
                    },
                    "tag_name": {
                        "type": "string",
                        "description": "Tag name to add"
                    }
                },
                "required": ["task_id", "project_id", "tag_name"]
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
        
        elif name == "update_task":
            task_id = arguments["task_id"]
            project_id = arguments["project_id"]
            
            # Build updates dict from provided arguments
            updates = {}
            if "title" in arguments:
                updates["title"] = arguments["title"]
            if "content" in arguments:
                updates["content"] = arguments["content"]
            if "priority" in arguments:
                updates["priority"] = arguments["priority"]
            if "dueDate" in arguments:
                updates["dueDate"] = arguments["dueDate"]
            
            task = await ticktick.update_task(task_id, project_id, **updates)
            return [TextContent(
                type="text",
                text=f"Updated task: {task.get('title', task_id)}"
            )]
        
        elif name == "create_project":
            name_arg = arguments["name"]
            color = arguments.get("color")
            
            project = await ticktick.create_project(name_arg, color)
            return [TextContent(
                type="text",
                text=f"Created project: {project['name']} (ID: {project['id']})"
            )]
        
        elif name == "search_tasks":
            keyword = arguments["keyword"]
            tasks = await ticktick.search_tasks(keyword)
            
            if not tasks:
                return [TextContent(type="text", text=f"No tasks found matching '{keyword}'")]
            
            result = []
            for task in tasks:
                status = "✓" if task.get("status") == 2 else "○"
                title = task.get("title", "Untitled")
                task_id = task.get("id", "")
                result.append(f"{status} {title} (ID: {task_id})")
            
            return [TextContent(
                type="text",
                text=f"Found {len(tasks)} tasks matching '{keyword}':\n" + "\n".join(result)
            )]
        
        elif name == "get_tasks_today":
            tasks = await ticktick.get_tasks_today()
            
            if not tasks:
                return [TextContent(type="text", text="No tasks due today")]
            
            result = []
            for task in tasks:
                status = "✓" if task.get("status") == 2 else "○"
                title = task.get("title", "Untitled")
                result.append(f"{status} {title}")
            
            return [TextContent(
                type="text",
                text=f"Tasks due today ({len(tasks)}):\n" + "\n".join(result)
            )]
        
        elif name == "get_tasks_overdue":
            tasks = await ticktick.get_tasks_overdue()
            
            if not tasks:
                return [TextContent(type="text", text="No overdue tasks! 🎉")]
            
            result = []
            for task in tasks:
                title = task.get("title", "Untitled")
                due = task.get("dueDate", "")
                result.append(f"⚠️ {title} (Due: {due})")
            
            return [TextContent(
                type="text",
                text=f"Overdue tasks ({len(tasks)}):\n" + "\n".join(result)
            )]
        
        elif name == "get_tasks_by_priority":
            priority = arguments["priority"]
            tasks = await ticktick.get_tasks_by_priority(priority)
            
            priority_names = {0: "None", 1: "Low", 3: "Medium", 5: "High"}
            priority_name = priority_names.get(priority, str(priority))
            
            if not tasks:
                return [TextContent(type="text", text=f"No tasks with priority: {priority_name}")]
            
            result = []
            for task in tasks:
                status = "✓" if task.get("status") == 2 else "○"
                title = task.get("title", "Untitled")
                result.append(f"{status} {title}")
            
            return [TextContent(
                type="text",
                text=f"Tasks with {priority_name} priority ({len(tasks)}):\n" + "\n".join(result)
            )]
        
        elif name == "list_tags":
            tags = await ticktick.list_tags()
            
            if not tags:
                return [TextContent(type="text", text="No tags found")]
            
            return [TextContent(
                type="text",
                text=f"Tags ({len(tags)}):\n" + "\n".join([f"#{tag}" for tag in tags])
            )]
        
        elif name == "add_tag_to_task":
            task_id = arguments["task_id"]
            project_id = arguments["project_id"]
            tag_name = arguments["tag_name"]
            
            await ticktick.add_tag_to_task(task_id, project_id, tag_name)
            return [TextContent(
                type="text",
                text=f"Added tag '#{tag_name}' to task {task_id}"
            )]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

