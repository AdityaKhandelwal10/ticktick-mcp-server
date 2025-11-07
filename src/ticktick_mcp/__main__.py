"""Entry point for running the TickTick MCP server."""

import asyncio
from mcp.server.stdio import stdio_server
from .server import app


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

