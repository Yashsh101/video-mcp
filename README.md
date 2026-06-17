# 🎥 Video MCP: The Production-Grade AI Video Generation MCP Server

[![CI Status](https://github.com/Yashsh101/video-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Yashsh101/video-mcp/actions)
[![PyPI version](https://badge.fury.io/py/video-mcp.svg)](https://badge.fury.io/py/video-mcp)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)

An AI-native Model Context Protocol (MCP) server that integrates Kling AI, ElevenLabs, Hailuo, and Google Veo to turn scripts directly into platform-ready, vertical social reels in a single prompt.

Unlike traditional video editing servers that only wrap local FFmpeg operations, **Video MCP contains an intelligent orchestration and caching layer** enabling LLM agents (like Claude or Gemini) to create, voice, caption, maintain character consistency, and compile complete short-form reels autonomously.

---

## 📖 Table of Contents
1. [🚀 Quick Activation (Claude Desktop)](#-quick-activation-claude-desktop)
2. [📦 Installation](#-installation)
3. [💡 Core Architecture](#-core-architecture)
4. [🛠️ Tool Registry & API Reference](#%EF%B8%8F-tool-registry--api-reference)
5. [⚡ Caching, Checkpointing, and Resilience](#-caching-checkpointing-and-resilience)
6. [🖥️ CLI & Troubleshooting](#%EF%B8%8F-cli--troubleshooting)
7. [🤝 Contributing & Community](#-contributing--community)

---

## 🚀 Quick Activation (Claude Desktop)

To activate Video MCP inside Claude Desktop, update your configuration file:
* **macOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the following block to your `mcpServers` object:

```json
{
  "mcpServers": {
    "video-mcp": {
      "command": "uvx",
      "args": ["--from", "video-mcp", "video-mcp"],
      "env": {
        "KLING_API_KEY": "your-kling-api-key",
        "ELEVENLABS_API_KEY": "your-elevenlabs-api-key",
        "HAILUO_API_KEY": "your-hailuo-api-key",
        "VEO_API_KEY": "your-veo-api-key",
        "VIDEO_MCP_WORK_DIR": "/path/to/writable/work/directory",
        "VIDEO_MCP_ENABLE_CACHE": "true"
      }
    }
  }
}
```

---

## 📦 Installation

Prerequisites:
* **Python**: 3.11 or 3.12
* **FFmpeg**: Required locally for timeline stitching and audio mixing.
  * **macOS**: `brew install ffmpeg`
  * **Linux**: `sudo apt-get install -y ffmpeg`
  * **Windows**: Add FFmpeg binaries to your user `PATH`.

Install using [uv](https://github.com/astral-sh/uv) (recommended) or `pip`:

```bash
# Install tool globally
uv tool install video-mcp

# Or run instantly via Docker
docker run -d \
  -e KLING_API_KEY="your-key" \
  -e ELEVENLABS_API_KEY="your-key" \
  -v /local/workdir:/tmp/video-mcp \
  ghcr.io/yashsh101/video-mcp:latest
```

---

## 💡 Core Architecture

Video MCP operates as an orchestrator coordinating three distinct subsystems:

```
┌────────────────────────────────────────────────────────┐
│                      MCP Client                        │
│             (Claude Desktop, Cursor, LLM)              │
└──────────────────────────┬─────────────────────────────┘
                           │ MCP JSON-RPC
                           ▼
┌────────────────────────────────────────────────────────┐
│                   Video MCP Server                     │
│  ┌───────────────────────┬──────────────────────────┐  │
│  │   Orchestration API   │  File-Based Cache Layer  │  │
│  ├───────────────────────┴──────────────────────────┤  │
│  │               Security Guardrails                │  │
│  └───────────────────────┬──────────────────────────┘  │
└──────────────────────────┼─────────────────────────────┘
                           ▼
 ┌─────────────────────────┼──────────────────────────┐
 │                         │                          │
 ▼                         ▼                          ▼
GenAI Providers       Audio Engines          Local Assembly
(Kling/Hailuo/Veo)     (ElevenLabs)         (FFmpeg Compilers)
```

1. **Intelligent Orchestrator**: The `create_reel_from_brief` pipeline parses narration scripts, estimates scene durations, generates narration, triggers parallel scene generations, compiles sequences, and overlays background music.
2. **State & Caching Layer**: Serializes generative API outputs into JSON schema keys paired with local media targets. Resolves scene/narration parameter updates before executing expensive model calls.
3. **Local Compilers**: Integrates FFmpeg processes directly to concatenate files, format layouts dynamically (pad or crop to target aspect ratios), normalise loudness to **-14 LUFS**, and burn subtitles natively.

---

## 🛠️ Tool Registry & API Reference

### 1. Orchestration Tools
* `create_reel_from_brief`
  * Description: Generates a complete captioned vertical video from a narration script.
  * Parameters:
    * `script` (string, required): Narration dialogues split by paragraph breaks.
    * `style` (string, optional, default: `"pixar"`): Pixar illustration or cinematic look.
    * `platform` (string, optional, default: `"instagram"`): Target reels resolution standard.
    * `provider` (string, optional, default: `"kling"`): Primary generative video provider.
    * `voice_id` (string, optional, default: `"adam"`): ElevenLabs voice identifier.
    * `character_name` (string, optional): Profile name to load facial consistency locks.
    * `output_path` (string, optional): Export filename.

### 2. Video & Audio Synthesis Tools
* `generate_video_from_image`
  * Parameters: `image_path`, `motion_prompt`, `duration` (1-60s), `aspect_ratio`, `provider`, `model`.
* `generate_video_from_text`
  * Parameters: `prompt`, `duration`, `aspect_ratio`, `style`, `provider`.
* `generate_voiceover`
  * Parameters: `script`, `voice_id`, `speed`, `output_path`.

### 3. Timeline & Assembly Tools
* `assemble_reel`
  * Parameters: `clips` (JSON Clip list), `voiceover_path`, `bgm_path`, `bgm_volume`, `output_path`, `aspect_ratio`, `add_captions`.
* `add_subtitles`
  * Parameters: `video_path`, `srt_path`, `style` (bold_white, etc.), `output_path`.
* `normalize_audio`
  * Parameters: `input_path`, `target_lufs` (default: `-14.0`), `output_path`.
* `resize_to_platform`
  * Parameters: `input_path`, `platform` (reels, tiktok, shorts, landscape), `output_path`.

---

## ⚡ Caching, Checkpointing, and Resilience

Video MCP incorporates state recovery mechanisms to protect API consumption credits.

### Payload Hashing Checkpoints
Every generation query checks the cache before invoking paid API requests:
* **Audio Caching**: Narratives are hashed (`voice_id` + `speed` + `script`) to load `vo_{hash}.mp3` from local storage instantly.
* **Video Caching**: Input image pixels are hashed along with style parameters and prompts. Re-runs of identical scene descriptors resolve to cached `.mp4` references.

```
Request scene 3 -> hash(img_bytes + motion_prompt + duration)
   ├── File exists in cache dir?
   │     ├── YES -> Copy local cached file to workspace (0ms latency, 0 credits)
   │     └── NO  -> Call kling provider, download result, save to cache
```

### Script-to-Reel Resume Capability
If a vertical reel compile fails at Scene 7 (e.g., due to temporary network failure or API timeouts):
1. Resolve the network block.
2. Trigger `create_reel_from_brief` using the exact same script.
3. The server immediately matches caches for the voiceover and Scenes 1–6.
4. Active execution starts directly at Scene 7, preventing loss of previously generated assets.

---

## 🖥️ CLI & Troubleshooting

The server is packaged with a Command Line Interface for direct system debugging.

```bash
# Diagnose configuration issues, writable path, and FFmpeg capability
video-mcp doctor

# Generate a single clip from the console
video-mcp generate --image ./character.png --prompt "zoom in, pixar" --output ./scene1.mp4

# Verify configure providers and api keys validation status
video-mcp providers
```

### Common Resolutions

* **UnicodeEncodeError / Emoji Crash**: If your local Windows PowerShell console crashes printing emojis, run your console in UTF-8 mode (`[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`) or upgrade to the latest `video-mcp` CLI which handles ASCII fallback blocks automatically.
* **FFmpeg Dependency Missing**: Ensure `ffmpeg` and `ffprobe` are visible on your user `PATH`. Run `video-mcp doctor` to inspect the detected location.

---

## 🤝 Contributing & Community

We welcome community extensions and provider adapters!
* Check out the [Contributing Guide](CONTRIBUTING.md) to set up your local development workspace using `uv`.
* For security disclosures and policies, please review [SECURITY.md](SECURITY.md).
* Keep track of changes and milestones in our [CHANGELOG.md](CHANGELOG.md).

Licensed under the [Apache-2.0 License](LICENSE).
