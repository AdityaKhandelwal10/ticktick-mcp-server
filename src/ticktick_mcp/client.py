"""TickTick API client with OAuth2 authentication."""

import json
import httpx
import webbrowser
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth callback."""
    auth_code = None
    
    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        if 'code' in params:
            CallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Authorization successful! You can close this window.</h1>')
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logs


class TickTickClient:
    """Client for TickTick OpenAPI with OAuth2 authentication."""

    BASE_URL = "https://api.ticktick.com/open/v1"
    AUTH_URL = "https://ticktick.com/oauth/authorize"
    TOKEN_URL = "https://ticktick.com/oauth/token"
    REDIRECT_URI = "http://localhost:8080/callback"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_file = Path.home() / ".ticktick-mcp" / "tokens.json"
        self.token_file.parent.mkdir(exist_ok=True)
        
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        self._load_tokens()

    def _load_tokens(self):
        """Load tokens from local storage."""
        if self.token_file.exists():
            try:
                data = json.loads(self.token_file.read_text())
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                expires_at = data.get("expires_at")
                if expires_at:
                    self.token_expires_at = datetime.fromisoformat(expires_at)
            except Exception:
                pass

    def _save_tokens(self):
        """Save tokens to local storage."""
        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None
        }
        self.token_file.write_text(json.dumps(data, indent=2))

    def start_oauth_flow(self):
        """Start OAuth flow with automatic callback capture."""
        auth_url = (
            f"{self.AUTH_URL}?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=tasks:read tasks:write"
        )
        
        # Start local server to capture callback
        server = HTTPServer(('localhost', 8080), CallbackHandler)
        server_thread = threading.Thread(target=server.handle_request)
        server_thread.start()
        
        print(f"\n🔐 Opening browser for TickTick authorization...")
        print(f"If browser doesn't open, visit: {auth_url}\n")
        webbrowser.open(auth_url)
        
        # Wait for callback
        server_thread.join(timeout=120)
        server.server_close()
        
        if CallbackHandler.auth_code:
            return CallbackHandler.auth_code
        else:
            raise Exception("Authorization failed or timed out")

    async def ensure_authenticated(self):
        """Ensure we have a valid access token."""
        if not self.access_token or self._is_token_expired():
            if self.refresh_token:
                await self._refresh_access_token()
            else:
                # Start OAuth flow automatically
                code = self.start_oauth_flow()
                await self.exchange_code_for_token(code)
                print("✅ Authentication successful! Tokens saved.")

    def _is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.token_expires_at:
            return True
        return datetime.now() >= self.token_expires_at - timedelta(minutes=5)

    async def exchange_code_for_token(self, code: str):
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.REDIRECT_URI,
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Debug: print response to see what TickTick returns
            print(f"Token response: {data}")
            
            if "access_token" not in data:
                raise Exception(f"No access_token in response: {data}")
            
            self.access_token = data["access_token"]
            self.refresh_token = data.get("refresh_token")  # May not exist
            expires_in = data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self._save_tokens()

    async def _refresh_access_token(self):
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            raise Exception("No refresh token available. Please re-authenticate.")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                }
            )
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data["access_token"]
            if "refresh_token" in data:
                self.refresh_token = data["refresh_token"]
            expires_in = data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self._save_tokens()

    async def _request(self, method: str, endpoint: str, **kwargs):
        """Make authenticated request to TickTick API."""
        await self.ensure_authenticated()
        
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Content-Type"] = "application/json"
        
        url = f"{self.BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                )
                print(f"Request: {method} {url}")
                print(f"Status: {response.status_code}")
                if response.status_code >= 400:
                    print(f"Error response: {response.text}")
                response.raise_for_status()
                return response.json() if response.content else None
            except Exception as e:
                print(f"Request failed: {method} {url}")
                print(f"Headers: {headers}")
                print(f"Error: {e}")
                raise

    async def get_projects(self):
        """Get all projects."""
        return await self._request("GET", "/project")

    async def get_tasks(self, project_id: Optional[str] = None):
        """Get tasks, optionally filtered by project."""
        # Use project data endpoint which returns project with tasks
        if project_id:
            data = await self._request("GET", f"/project/{project_id}/data")
        else:
            # Get all projects with their data
            projects = await self._request("GET", "/project")
            # For each project, collect all tasks
            all_tasks = []
            for project in projects:
                proj_data = await self._request("GET", f"/project/{project['id']}/data")
                if isinstance(proj_data, dict) and 'tasks' in proj_data:
                    all_tasks.extend(proj_data['tasks'])
            return all_tasks
        
        # Handle response - could be dict with 'tasks' key or list
        if isinstance(data, dict):
            return data.get('tasks', [])
        elif isinstance(data, list):
            return data
        else:
            print(f"Unexpected data type: {type(data)}, value: {data}")
            return []

    async def create_task(self, title: str, content: str = "", project_id: Optional[str] = None):
        """Create a new task."""
        data = {
            "title": title,
            "content": content,
        }
        if project_id:
            data["projectId"] = project_id
        
        return await self._request("POST", "/task", json=data)

    async def complete_task(self, task_id: str, project_id: str):
        """Complete a task."""
        return await self._request("POST", f"/task/{task_id}/{project_id}/complete")

    async def delete_task(self, task_id: str, project_id: str):
        """Delete a task."""
        return await self._request("DELETE", f"/task/{task_id}/{project_id}")

    async def update_task(self, task_id: str, project_id: str, **updates):
        """Update a task with new properties."""
        # Get current task first
        data = await self._request("GET", f"/project/{project_id}/data")
        tasks = data.get('tasks', []) if isinstance(data, dict) else []
        current_task = next((t for t in tasks if t.get('id') == task_id), None)
        
        if not current_task:
            raise Exception(f"Task {task_id} not found in project {project_id}")
        
        # Merge updates with current task
        updated_task = {**current_task, **updates}
        return await self._request("POST", f"/task/{task_id}/{project_id}", json=updated_task)

    async def create_project(self, name: str, color: Optional[str] = None, view_mode: Optional[str] = None):
        """Create a new project."""
        data = {"name": name}
        if color:
            data["color"] = color
        if view_mode:
            data["viewMode"] = view_mode
        return await self._request("POST", "/project", json=data)

    async def search_tasks(self, keyword: str):
        """Search tasks by keyword in title or content."""
        # Get all tasks and filter client-side since API may not have search
        all_tasks = await self.get_tasks()
        keyword_lower = keyword.lower()
        return [
            task for task in all_tasks
            if keyword_lower in task.get('title', '').lower() 
            or keyword_lower in task.get('content', '').lower()
        ]

    async def get_tasks_today(self):
        """Get tasks due today."""
        from datetime import datetime, timezone
        all_tasks = await self.get_tasks()
        today = datetime.now(timezone.utc).date()
        return [
            task for task in all_tasks
            if task.get('dueDate') and 
            datetime.fromisoformat(task['dueDate'].replace('Z', '+00:00')).date() == today
        ]

    async def get_tasks_overdue(self):
        """Get overdue tasks."""
        from datetime import datetime, timezone
        all_tasks = await self.get_tasks()
        now = datetime.now(timezone.utc)
        return [
            task for task in all_tasks
            if task.get('dueDate') and 
            datetime.fromisoformat(task['dueDate'].replace('Z', '+00:00')) < now
            and task.get('status') != 2  # Not completed
        ]

    async def get_tasks_by_priority(self, priority: int):
        """Get tasks by priority level (0=none, 1=low, 3=medium, 5=high)."""
        all_tasks = await self.get_tasks()
        return [task for task in all_tasks if task.get('priority') == priority]

    async def list_tags(self):
        """Get all tags used across tasks."""
        all_tasks = await self.get_tasks()
        tags = set()
        for task in all_tasks:
            if 'tags' in task and task['tags']:
                tags.update(task['tags'])
        return sorted(list(tags))

    async def add_tag_to_task(self, task_id: str, project_id: str, tag_name: str):
        """Add a tag to a task."""
        # Get current task
        data = await self._request("GET", f"/project/{project_id}/data")
        tasks = data.get('tasks', []) if isinstance(data, dict) else []
        current_task = next((t for t in tasks if t.get('id') == task_id), None)
        
        if not current_task:
            raise Exception(f"Task {task_id} not found")
        
        # Add tag if not already present
        tags = current_task.get('tags', [])
        if tag_name not in tags:
            tags.append(tag_name)
            current_task['tags'] = tags
            return await self._request("POST", f"/task/{task_id}/{project_id}", json=current_task)
        
        return current_task

