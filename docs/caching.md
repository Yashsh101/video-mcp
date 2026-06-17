# Caching and Resilience

Video MCP integrates a local, file-based caching layer designed to optimize costs, bypass rate limits, and provide robust state recovery during orchestrator execution.

---

## ⚙️ Configuration

Control the caching behavior using the following environment variables:

*   `VIDEO_MCP_ENABLE_CACHE`: Set to `true` (default) to enable caching; set to `false` to force requests directly to upstream APIs.
*   `VIDEO_MCP_CACHE_DIR`: Explicit path to store cache files. Defaults to `.mcp_cache/` inside your `VIDEO_MCP_WORK_DIR`.

---

## 🧠 Caching Subsystems

### 1. Voiceover (TTS) Caching
Before calling ElevenLabs API, the server hashes:
*   `voice_id`
*   `speed` (formatted to 4 decimal places)
*   `script` content

**Key**: `vo_{sha256}.json` and `vo_{sha256}.mp3`
If found, the server copies the cached audio track directly to the destination path, preserving character credits.

### 2. Video Scene Caching
Before submitting clip requests, the server hashes:
*   The reference image bytes (if an image is provided)
*   The clean motion prompt
*   Duration
*   Aspect ratio
*   Provider
*   Model/Style
*   Audio prompt (if any)

**Key**: `video_{sha256}.json` and `video_{sha256}.mp4`
If both files exist in the cache directory, the server copies the cached clip. This prevents duplicate generations for the same prompts or static character references.

---

## ⚡ Checkpoint & Resume Capability

The flagship orchestrator `create_reel_from_brief` leverages this caching mechanism to achieve script-level checkpointing:

1.  **Decomposition**: The script is split into paragraph segments representing distinct scenes.
2.  **Voiceover Checkpoint**: The voiceover file is generated first. If this exact script has been voiced, the voiceover is loaded instantly from the cache.
3.  **Scene Checkpoints**: In parallel, `batch_generate_scenes` checks the cache for each scene individually.
    *   Scenes that were generated successfully in a previous run immediately hit the cache and are copied in milliseconds.
    *   Only scenes that failed, timed out, or were edited are sent to the generative model.
4.  **Assembly**: All clips (cached and new) are stitched together using FFmpeg.

This ensures that network timeouts or quota exhaustion will never force a complete restart of the orchestration pipeline.
