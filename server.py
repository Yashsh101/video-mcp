import os
import sys
from fastmcp import FastMCP
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

mcp = FastMCP("video-mcp")

@mcp.tool
def health_check() -> dict:
    return {"status": "ok", "server": "video-mcp"}

@mcp.tool
def generate_video_prompt(topic: str, style: str = "cinematic", duration: str = "8s") -> dict:
    prompt = f"Create a {style} AI video about {topic}. Duration: {duration}. High detail, smooth motion, strong composition, natural lighting."
    return {
        "topic": topic,
        "style": style,
        "duration": duration,
        "prompt": prompt,
    }

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), path="/mcp/")