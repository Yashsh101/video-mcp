import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict

# Load env files if they exist
load_dotenv()

class Settings(BaseModel):
    kling_api_key: str | None = Field(default_factory=lambda: os.getenv("KLING_API_KEY"))
    elevenlabs_api_key: str | None = Field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY"))
    hailuo_api_key: str | None = Field(default_factory=lambda: os.getenv("HAILUO_API_KEY"))
    veo_api_key: str | None = Field(default_factory=lambda: os.getenv("VEO_API_KEY"))
    work_dir: Path = Field(default_factory=lambda: Path(os.getenv("VIDEO_MCP_WORK_DIR", "/tmp/video-mcp")))
    max_file_size_mb: int = Field(default_factory=lambda: int(os.getenv("VIDEO_MCP_MAX_FILE_SIZE_MB", "500")))
    default_provider: str = Field(default_factory=lambda: os.getenv("VIDEO_MCP_DEFAULT_PROVIDER", "kling"))
    log_level: str = Field(default_factory=lambda: os.getenv("VIDEO_MCP_LOG_LEVEL", "INFO"))
    enable_cache: bool = Field(default_factory=lambda: os.getenv("VIDEO_MCP_ENABLE_CACHE", "true").lower() in ("true", "1", "yes"))
    cache_dir: Path | None = Field(default_factory=lambda: Path(os.getenv("VIDEO_MCP_CACHE_DIR")) if os.getenv("VIDEO_MCP_CACHE_DIR") else None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # Auto-create workspace dir
    settings.work_dir.mkdir(parents=True, exist_ok=True)
    return settings
