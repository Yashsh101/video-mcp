# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] — 2026-06-25

### Fixed
- Dockerfile rewritten: replaced missing `requirements.txt` reference with `uv`-based multi-stage build
- `server.py`: switched `mcp.run()` to `streamable-http` transport on `0.0.0.0:$PORT`
- `server.py`: added `/health` GET endpoint for Render health checks
- `server.py`: fixed invalid URI schemes in `@mcp.resource()` decorators (`video_mcp://` → `video-mcp://`) — FastMCP 3.4.2 enforces RFC 3986 (no underscores in scheme)
- Added `render.yaml` for one-click Render.com free tier deployment

### Deployment
- Live at: https://video-mcp-9c74.onrender.com
- Health: https://video-mcp-9c74.onrender.com/health

## [0.1.0] - 2026-06-16

This is the initial release of the Video MCP Server, introducing a fully integrated suite of tools for short-form video generation, audio synthesis, and clip composition.

### Added
- **Core Server**: FastMCP implementation with multi-tool architecture.
- **Video Providers**: Integration wrappers for Kling (image-to-video), Hailuo, and Google Veo.
- **Audio Providers**: ElevenLabs text-to-speech integration.
- **Video Editing**: Trim, scale/resize, normalize audio (-14 LUFS), and burn-in subtitle captions.
- **Facial Lock Consistency**: Character profiling features using reference images.
- **CLI Utility**: `video-mcp` command-line tools (`doctor`, `generate`, `voiceover`, `reel`, `info`, `providers`).
- **DevOps**: GitHub Actions workflows for linting, type-checking, matrix testing (Ubuntu/macOS, Python 3.11/3.12), and release publishing.
