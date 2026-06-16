from pathlib import Path

from video_mcp.config import get_settings
from video_mcp.errors import ErrorCode, MCPVideoError


def validate_input_path(path_str: str) -> Path:
    """Validates that input path exists, is readable, and lies within the work directory (no traversal)."""
    if not path_str:
        raise MCPVideoError("Input path cannot be empty", ErrorCode.INVALID_INPUT)

    settings = get_settings()
    work_dir = settings.work_dir.resolve()
    
    # Try resolving path. Handle potential errors.
    try:
        path = Path(path_str).resolve()
    except Exception as e:
        raise MCPVideoError(f"Invalid path format: {e}", ErrorCode.INVALID_INPUT)

    # Check path traversal / boundary
    try:
        path.relative_to(work_dir)
    except ValueError:
        raise MCPVideoError(
            f"Path violation: {path} lies outside of allowed WORK_DIR {work_dir}",
            ErrorCode.PATH_VIOLATION,
        )

    if not path.exists():
        raise MCPVideoError(f"Input file not found: {path}", ErrorCode.FILE_NOT_FOUND)
    
    if not path.is_file():
        raise MCPVideoError(f"Input path is not a file: {path}", ErrorCode.INVALID_INPUT)

    # Test readability
    try:
        with open(path, "rb") as f:
            f.read(1)
    except Exception as e:
        raise MCPVideoError(f"Input file is not readable: {e}", ErrorCode.PATH_VIOLATION)

    return path

def validate_output_path(path_str: str | None, suffix: str) -> Path:
    """Ensures output path is inside work_dir, creates parent directories, and appends suffix if missing."""
    settings = get_settings()
    work_dir = settings.work_dir.resolve()

    if not path_str:
        # Generate a unique path inside work_dir
        import uuid
        path = work_dir / f"output_{uuid.uuid4().hex}{suffix}"
    else:
        try:
            path = Path(path_str).resolve()
        except Exception as e:
            raise MCPVideoError(f"Invalid path format: {e}", ErrorCode.INVALID_INPUT)

        # Check path traversal
        try:
            path.relative_to(work_dir)
        except ValueError:
            raise MCPVideoError(
                f"Path violation: Output path {path} must be inside WORK_DIR {work_dir}",
                ErrorCode.PATH_VIOLATION,
            )

    # Ensure parent directories exist
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise MCPVideoError(f"Failed to create output parent directory: {e}", ErrorCode.INVALID_INPUT)

    # Ensure it ends with suffix
    if suffix and not path.name.endswith(suffix):
        path = path.with_suffix(suffix)

    return path

def validate_file_size(path: Path) -> None:
    """Raises if file size exceeds configured limits."""
    settings = get_settings()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    try:
        size = path.stat().st_size
    except Exception as e:
        raise MCPVideoError(f"Failed to check file size: {e}", ErrorCode.INVALID_INPUT)

    if size > max_bytes:
        raise MCPVideoError(
            f"File size {size / (1024 * 1024):.1f}MB exceeds limit of {settings.max_file_size_mb}MB",
            ErrorCode.INVALID_INPUT,
        )

def validate_aspect_ratio(ratio: str) -> None:
    """Accepts only standard video aspect ratios."""
    allowed = {"9:16", "16:9", "1:1", "4:5"}
    if ratio not in allowed:
        raise MCPVideoError(
            f"Invalid aspect ratio '{ratio}'. Allowed ratios: {', '.join(allowed)}",
            ErrorCode.INVALID_INPUT,
        )

def validate_duration(seconds: int, provider: str = "kling") -> None:
    """Ensures generation durations fall within provider limits."""
    # Paid/premium providers generally support longer durations
    max_duration = 180 if provider in {"veo", "runway"} else 60
    if not (1 <= seconds <= max_duration):
        raise MCPVideoError(
            f"Invalid duration {seconds}s. Must be between 1 and {max_duration} seconds for {provider}.",
            ErrorCode.INVALID_INPUT,
        )

def sanitize_prompt(prompt: str) -> str:
    """Cleans up prompt strings to prevent injection or formatting breakages."""
    if not prompt:
        return ""
    # Strip control characters
    sanitized = "".join(ch for ch in prompt if ord(ch) >= 32 or ch in "\n\r\t")
    # Limit length
    return sanitized[:1000].strip()
