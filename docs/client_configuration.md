# MCP Client Configuration

Video MCP operates as a standard JSON-RPC over Standard Input/Output (Stdio) Model Context Protocol server. This guide documents how to attach the server to popular MCP hosts.

---

## 1. Claude Desktop Configuration

Claude Desktop is the flagship environment for MCP servers. To configure Video MCP:

1. Open the configuration file `claude_desktop_config.json`:
   * **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   * **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   * **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Populate the `mcpServers` object with the `video-mcp` definition:

```json
{
  "mcpServers": {
    "video-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--from",
        "video-mcp",
        "video-mcp"
      ],
      "env": {
        "KLING_API_KEY": "your-kling-api-key",
        "ELEVENLABS_API_KEY": "your-elevenlabs-api-key",
        "HAILUO_API_KEY": "your-hailuo-api-key",
        "VEO_API_KEY": "your-veo-api-key",
        "VIDEO_MCP_WORK_DIR": "/path/to/workdir",
        "VIDEO_MCP_ENABLE_CACHE": "true"
      }
    }
  }
}
```

Restart Claude Desktop, and you will see the video camera icon indicating that the 15+ video orchestration tools are attached.

---

## 2. Cursor IDE Integration

Cursor supports attaching command-based MCP servers:

1. Open Cursor Settings and navigate to **Features** $\to$ **MCP**.
2. Click **+ Add New MCP Server**.
3. Fill in the parameters:
   * **Name**: `video-mcp`
   * **Type**: `command`
   * **Command**: `uv run --from video-mcp video-mcp`
4. Provide the environment keys (`KLING_API_KEY`, `ELEVENLABS_API_KEY`, etc.) inside the Cursor MCP panel configuration settings.
5. Click **Save**.

---

## 3. Custom Python client or JSON-RPC scripts
You can spawn and run the server programmatically using the official `mcp` python library:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "--from", "video-mcp", "video-mcp"],
        env={
            "KLING_API_KEY": "your-key",
            "ELEVENLABS_API_KEY": "your-key"
        }
    )
    
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # List available video tools
            tools = await session.list_tools()
            print("Attached tools:", [t.name for t in tools.tools])

if __name__ == "__main__":
    asyncio.run(main())
```
