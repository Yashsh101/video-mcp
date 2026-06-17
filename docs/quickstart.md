# Quick Start Guide

This guide gets you up and running with the Video MCP Server as quickly as possible.

---

## 📋 System Prerequisites

Before starting, confirm that your machine satisfies the following hardware and software requirements:

*   **Operating System**: Windows 10/11, macOS 11+, or Linux (Ubuntu 20.04+).
*   **Python Runtime**: `3.11` or `3.12` installed and added to your environment `PATH`.
*   **Media Driver**: **FFmpeg** binaries.
    *   **macOS**: `brew install ffmpeg`
    *   **Linux**: `sudo apt-get update && sudo apt-get install -y ffmpeg`
    *   **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add the `bin` directory to your user `PATH`.

---

## ⚡ Setup in 3 Steps

### Step 1: Install uv and synchronization package
We recommend [uv](https://github.com/astral-sh/uv) for fast, isolated python virtual environments.

```bash
# Install uv globally
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize and install video-mcp globally
uv tool install video-mcp
```

### Step 2: Configure Environment Keys
Create a workspace directory and set up your active provider keys:

*   **Linux/macOS**:
    ```bash
    export KLING_API_KEY="your-kling-api-key"
    export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
    export VIDEO_MCP_WORK_DIR="/tmp/video-mcp"
    ```
*   **Windows (PowerShell)**:
    ```powershell
    $env:KLING_API_KEY="your-kling-api-key"
    $env:ELEVENLABS_API_KEY="your-elevenlabs-api-key"
    $env:VIDEO_MCP_WORK_DIR="C:\tmp\video-mcp"
    ```

### Step 3: Run Environment Diagnostics
Execute the built-in diagnostic utility to ensure your pathing, FFmpeg binaries, and write directories are correct:

```bash
video-mcp doctor
```

If the checks pass successfully, your system is ready to host the Video MCP Server!

---

## 🎬 Running Your First Video Compilation

You can compile your first vertical reel script directly from the Command Line Interface (CLI):

```bash
video-mcp reel \
  --script "Bob started wash dishes. [SCENE] Bob wash dishes at sink. [SCENE] Bob eating steak." \
  --style "pixar" \
  --platform "instagram" \
  --output "./first_reel.mp4"
```

This command parses the scenes, generates the ElevenLabs voiceover, creates matching Pixar-style video clips, stitches them together, burns in captions, and exports the final file.
