"""Test script to verify TickTick MCP setup locally."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from src.ticktick_mcp.client import TickTickClient

# Load environment variables from .env file
load_dotenv()


async def main():
    """Test the TickTick client setup."""
    
    # Get credentials from environment
    client_id = os.getenv("TICKTICK_CLIENT_ID")
    client_secret = os.getenv("TICKTICK_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ Missing credentials!")
        print("\nSet environment variables:")
        print("  export TICKTICK_CLIENT_ID='your-client-id'")
        print("  export TICKTICK_CLIENT_SECRET='your-client-secret'")
        return
    
    print("🔧 Testing TickTick MCP Setup...")
    print(f"📋 Client ID: {client_id[:10]}...")
    
    try:
        # Initialize client
        client = TickTickClient(client_id, client_secret)
        
        # Test authentication and API call
        print("\n🔐 Authenticating...")
        projects = await client.get_projects()
        
        print("\n✅ Success! Connected to TickTick")
        print(f"\n📁 Found {len(projects)} projects:")
        for project in projects[:5]:  # Show first 5
            print(f"  - {project['name']} (ID: {project['id']})")
        
        # Debug: Print first project structure to see all fields
        if projects:
            print(f"\n🔍 Debug - First project structure:")
            print(f"Keys: {list(projects[0].keys())}")
        
        # Test getting tasks - try with first project if available
        print("\n📝 Fetching tasks...")
        if projects:
            print(f"Trying to fetch tasks from project: {projects[0]['name']}")
            try:
                tasks = await client.get_tasks(projects[0]['id'])
                print(f"✅ Found {len(tasks)} tasks in first project")
            except Exception as e:
                print(f"⚠️ Failed to get tasks from project: {e}")
                print("Trying to get all tasks...")
                tasks = await client.get_tasks()
                print(f"✅ Found {len(tasks)} total tasks")
        else:
            tasks = await client.get_tasks()
            print(f"✅ Found {len(tasks)} total tasks")
        
        print("\n🎉 All tests passed! Your setup is working.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your Client ID and Secret")
        print("  2. Ensure redirect URI is set to: http://localhost:8080/callback")
        print("  3. Try deleting ~/.ticktick-mcp/tokens.json and re-auth")


if __name__ == "__main__":
    asyncio.run(main())

