__version__ = "0.1.0"

from video_mcp.client import Client
from video_mcp.errors import ErrorCode, MCPVideoError

__all__ = ["Client", "MCPVideoError", "ErrorCode"]
