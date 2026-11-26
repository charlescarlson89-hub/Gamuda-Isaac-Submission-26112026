import os
import sys

STDIO = os.path.join(os.path.dirname(__file__), "server", "stdio")

tavily_api_key = os.getenv("TAVILY_API_KEY")
SERVERS = {
    "random_number": {
        "command": sys.executable,
        "args": [os.path.join(STDIO, "random_number.py")],
        "transport": "stdio",
    },
    "roll_dice": {
        "url": "http://localhost:8000/mcp",
        "transport": "streamable_http",
    },
        "tavily": {
        "url": "https://mcp.tavily.com/mcp/",
        "transport": "streamable_http",
        "headers": {"Authorization": f"Bearer {tavily_api_key}"},
    },
        "postgres": {
        "command": sys.executable,
        "args": [os.path.join(STDIO, "postgres_server.py")],
        "env": {"DATABASE_URL": os.environ["DATABASE_URL"]},
        "transport": "stdio",
    },
}