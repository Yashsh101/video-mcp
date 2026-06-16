# 🎥 Video-MCP: AI-Native Video Generation MCP Server

[![CI Status](https://github.com/Yashsh101/video-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Yashsh101/video-mcp/actions)
[![PyPI version](https://badge.fury.io/py/video-mcp.svg)](https://badge.fury.io/py/video-mcp)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)

An AI-native Model Context Protocol (MCP) server that integrates Kling AI, ElevenLabs, Hailuo, and Google Veo to turn scripts directly into vertical social reels in a single prompt.

Unlike traditional video editing servers that only wrap local FFmpeg operations, **Video-MCP contains an intelligent AI generation layer** enabling LLM agents (like Claude or Gemini) to create, voice, caption, and compile complete short-form reels autonomously.

---

## 🚀 Quick Activation (Claude Desktop)

To use Video-MCP in your Claude Desktop client, add this server block to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "video-mcp": {
      "command": "uvx",
      "args": ["--from", "video-mcp", "video-mcp"],
      "env": {
        "KLING_API_KEY": "your-kling-key",
        "ELEVENLABS_API_KEY": "your-elevenlabs-key"
      }
    }
  }
}
```

---

## 📦 Installation

Install globally using `uv` (recommended) or `pip`:

```bash
# Using uv tool (recommended)
uv tool install video-mcp

# Using pip
pip install video-mcp

# Running directly inside Docker
docker run -e KLING_API_KEY="key" -e ELEVENLABS_API_KEY="key" ghcr.io/yashsh101/video-mcp:latest
```

---

## 🛠️ Tool Registry

Video-MCP exposes 15+ high-value tools to LLM agents for script-to-video reels creation:

| Category | Tool Name | Description |
|---|---|---|
| **Orchestrator** | `create_reel_from_brief` | **Flagship:** Compiles script text to vertical reels |
| **AI Video** | `generate_video_from_image` | Creates motion clips using Kling, Hailuo, or Veo |
| **AI Video** | `generate_video_from_text` | Generates video directly from text description |
| **AI Audio** | `generate_voiceover` | Generates spoken voiceover MP3 using ElevenLabs TTS |
| **Consistency** | `create_character_profile` | Saves character details for consistent facial looks |
| **Consistency** | `generate_scene_with_character` | Generates a scene with character face-lock |
| **Assembly** | `assemble_reel` | Concats clips, overlays audio, and burns captions |
| **Assembly** | `add_subtitles` | Burns SRT captions directly into the video pixels |
| **Assembly** | `resize_to_platform` | Auto center-crops for Reels/TikTok/Shorts |
| **Utility** | `normalize_audio` | Normalizes audio tracks to -14 LUFS |
| **Utility** | `search_tools` | Keyword search for tool capabilities |

---

## 🐍 Python Client Example

You can also use Video-MCP as a standard Python library:

```python
from video_mcp import Client

# Initialize synchronous client
client = Client()

# Create character profile for Bob
profile = client.create_character_profile(
    reference_images=["/path/to/bob.jpg"],
    character_name="Bob Campana",
    style="pixar"
)

# Compile reel from script
result = client.create_reel_from_brief(
    script="Bob started as a dishwasher. [SCENE] Bob wash dishes. [SCENE] Bob eating steak.",
    character_name="Bob Campana",
    platform="instagram",
    style="pixar"
)

print(f"🎉 Reel created at: {result.output_path}")
print(f"Storyboard: {result.storyboard_path}")
```

---

## 🖥️ Command Line Interface (CLI)

Video-MCP comes with a click-based CLI for local development and configuration checks:

```bash
# Verify environment and FFmpeg binaries
video-mcp doctor

# Generate a single clip from CLI
video-mcp generate --image ./ref.png --prompt "orbit shot, slow zoom" --output ./output.mp4

# Check active AI providers
video-mcp providers
```

---

## 🤝 Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for guidelines on how to run tests locally, write custom providers, or format code.

## 📄 License
This project is licensed under the Apache-2.0 License. See `LICENSE` for details.
