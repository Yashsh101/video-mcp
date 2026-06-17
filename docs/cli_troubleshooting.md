# CLI and Troubleshooting Guide

Video MCP includes a Command Line Interface (CLI) for administration, configuration validation, and local asset generation.

---

## 🖥️ Command Line Reference

All subcommands are exposed via the `video-mcp` command:

### 1. `video-mcp doctor`
Runs local environmental diagnostics, checking for Python versions, write directories, API credentials status, and local media driver availability.
* **Usage**: `video-mcp doctor`

### 2. `video-mcp generate`
Generates a video clip from an input reference image.
* **Usage**:
  ```bash
  video-mcp generate --image ./character.png --prompt "orbit zoom" --provider kling --output ./clip.mp4
  ```

### 3. `video-mcp voiceover`
Converts script dialogues to spoken audio.
* **Usage**:
  ```bash
  video-mcp voiceover --script "Welcome to the future of AI." --voice adam --output ./voice.mp3
  ```

### 4. `video-mcp reel`
Compiles a vertical reel script to video.
* **Usage**:
  ```bash
  video-mcp reel --script "Scene 1 description." --style pixar --output ./reel.mp4
  ```

### 5. `video-mcp info`
Analyzes technical characteristics of a video file.
* **Usage**: `video-mcp info ./compiled.mp4`

---

## 🔍 Troubleshooting Scenarios

### ❌ Scenario A: UnicodeEncodeError on Windows Console
* **Symptom**: CLI crashes with error:
  `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'`
* **Cause**: The active PowerShell/cmd session is set to legacy default codepages (like CP1252) which do not support unicode emoji symbols.
* **Fix**:
  * Run PowerShell as Administrator and enable UTF-8 mode:
    ```powershell
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    ```
  * Note: The latest CLI has built-in `_safe_echo` overrides that fall back to ASCII text brackets (`[PASS]`, `[FAIL]`) automatically.

### ❌ Scenario B: FFmpeg Dependency Missing
* **Symptom**: Tests skip assemble fixtures, or CLI reports:
  `FileNotFoundError: [WinError 2] The system cannot find the file specified`
* **Cause**: FFmpeg executable binaries are not installed or not exposed on system PATH.
* **Fix**: Ensure `which ffmpeg` (macOS/Linux) or `where.exe ffmpeg` (Windows) returns a valid executable path. Add the `bin/` path to environment configurations.

### ❌ Scenario C: Kling API Timeout / Quota Limits
* **Symptom**: Logs report Kling request timeouts or status checks return `failed`.
* **Cause**: Kling limits parallel processing or upstream queues are saturated.
* **Fix**:
  * Set model to `fast` inside your execution requests.
  * Configure Hailuo credentials to enable auto-fallback loops.
