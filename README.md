# TickTick MCP Server

MCP server for TickTick task management - enables AI assistants like Claude to manage your tasks.

## Features

### Core Task Management
- ✅ List projects and tasks
- ✅ Create new tasks
- ✅ Update tasks (title, content, priority, due date)
- ✅ Complete tasks
- ✅ Delete tasks

### Advanced Features
- ✅ Search tasks by keyword
- ✅ Get tasks due today
- ✅ Get overdue tasks
- ✅ Filter tasks by priority
- ✅ Tag management (list tags, add tags to tasks)
- ✅ Create new projects

### Authentication
- ✅ OAuth2 authentication with automatic token refresh

## Setup

### 1. Get TickTick API Credentials

1. Go to [TickTick Developer Portal](https://developer.ticktick.com)
2. Create a new app
3. Set redirect URI to: `http://localhost:8080/callback`
4. Save your `Client ID` and `Client Secret`

### 2. Install the Package

```bash
cd tick-tick-mcp
pip install -r requirements.txt
# or
pip install -e .
```

### 2.5. Create .env File (for local testing)

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```
TICKTICK_CLIENT_ID=your-actual-client-id
TICKTICK_CLIENT_SECRET=your-actual-client-secret
```

### 3. Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "python",
      "args": ["-m", "ticktick_mcp"],
      "env": {
        "TICKTICK_CLIENT_ID": "your-client-id-here",
        "TICKTICK_CLIENT_SECRET": "your-client-secret-here"
      }
    }
  }
}
```

### 4. Configure Cursor (Alternative)

For Cursor IDE, add the same config to:
`~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

### 5. First Use

On first use, the MCP server will:

1. Automatically open your browser to TickTick authorization page
2. You authorize the app
3. Tokens are saved automatically to `~/.ticktick-mcp/tokens.json`
4. Future requests auto-refresh tokens - no re-auth needed!

## Usage

Once configured, you can ask Claude or Cursor:

**Basic Operations:**
- "List my TickTick projects"
- "Show me all my tasks"
- "Create a task called 'Review PR'"
- "Complete task XYZ"
- "Delete task ABC"

**Advanced Queries:**
- "Search for tasks about 'meeting'"
- "What tasks are due today?"
- "Show me all overdue tasks"
- "List my high priority tasks"
- "Update task XYZ to high priority"
- "Add tag 'urgent' to task ABC"
- "Create a new project called 'Personal'"
- "What tags am I using?"

## Tools Available (13 total)

### Project Management
- `list_projects` - Get all projects
- `create_project` - Create a new project/list

### Task Operations
- `list_tasks` - Get tasks (optionally filter by project)
- `create_task` - Create a new task
- `update_task` - Update task properties (title, content, priority, due date)
- `complete_task` - Mark task complete
- `delete_task` - Delete a task

### Search & Filtering
- `search_tasks` - Search tasks by keyword
- `get_tasks_today` - Get tasks due today
- `get_tasks_overdue` - Get overdue tasks
- `get_tasks_by_priority` - Filter by priority (0=none, 1=low, 3=medium, 5=high)

### Tags
- `list_tags` - List all tags
- `add_tag_to_task` - Add a tag to a task

## Development

```bash
# Install in development mode
pip install -e .

# Run directly
python -m ticktick_mcp
```

## Security

- Tokens are stored locally in `~/.ticktick-mcp/tokens.json`
- Never commit your Client ID/Secret to version control
- Each user needs their own TickTick developer app

## License

MIT

