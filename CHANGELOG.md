# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
