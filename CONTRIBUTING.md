# Contributing to Video MCP

First off, thank you for taking the time to contribute! Contributions from the community help make Video MCP a production-grade, highly performant, and reliable Model Context Protocol server.

The following guidelines outline the standards and processes for contributing to the repository.

---

## 🚀 Getting Started

### Prerequisites
* **Python 3.11** or higher
* [uv](https://github.com/astral-sh/uv) (strongly recommended python packaging tool)
* **FFmpeg** (essential for local video assembly and audio tools)
  * **macOS**: `brew install ffmpeg`
  * **Linux**: `sudo apt-get install ffmpeg`
  * **Windows**: Download binaries from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add them to your user `PATH`.

### Local Setup
1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/video-mcp.git
   cd video-mcp
   ```

2. Initialize a virtual environment and synchronize dependencies using `uv`:
   ```bash
   uv sync --all-extras
   ```
   This creates a `.venv` directory and installs all dependencies (core, development, and optional extras).

3. Activate the virtual environment:
   * **macOS/Linux**: `source .venv/bin/activate`
   * **Windows (PowerShell)**: `.venv\Scripts\Activate.ps1`

---

## 🛠 Development Workflow

### Code Quality and Style
We enforce strict style checks to maintain a clean codebase:
* **Linting & Formatting**: We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting. Run:
  ```bash
  uv run ruff check video_mcp/
  uv run ruff format video_mcp/
  ```
* **Static Type Checking**: We use [mypy](https://github.com/python/mypy) for strict type safety. Run:
  ```bash
  uv run mypy video_mcp/
  ```

### Writing and Running Tests
All logic must be accompanied by unit tests under the `tests/` directory.

To run the complete test suite with coverage and zero warnings:
```bash
uv run pytest tests/ -W error
```

> [!NOTE]
> If FFmpeg is missing from your system, tests requiring subprocess calls will automatically be skipped cleanly without throwing errors or causing build failures.

---

## 📄 Pull Request Guidelines
1. **Branch Naming**: Use clean, descriptive branch names (e.g., `feature/kling-provider`, `fix/cli-unicode`).
2. **Commit Messages**: Write meaningful commit messages adhering to Conventional Commits (e.g., `feat: add support for veo video model`).
3. **Documentation**: If adding tools or resources, update `README.md` and inline docstrings.
4. **Verifications**: Ensure Ruff linting, mypy types, and pytest checks all pass locally before opening a pull request.
