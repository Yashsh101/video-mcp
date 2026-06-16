import hashlib
import json
import shutil
from pathlib import Path

import structlog

import video_mcp.config
from video_mcp.models.results import AudioResult, VideoResult

logger = structlog.get_logger()

def get_cache_dir() -> Path:
    """Returns the resolved cache directory, ensuring it exists."""
    settings = video_mcp.config.get_settings()
    if settings.cache_dir:
        path = settings.cache_dir.resolve()
    else:
        path = (settings.work_dir / ".mcp_cache").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

def hash_file(file_path: Path) -> str:
    """Calculates the SHA-256 hash of a file's content."""
    if not file_path.exists():
        return ""
    hasher = hashlib.sha256()
    # Read in chunks of 64kb
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_cached_voiceover(
    script: str, voice_id: str, speed: float
) -> tuple[AudioResult | None, Path | None]:
    """
    Checks the cache for a previously generated voiceover.
    Returns (AudioResult, cached_file_path) if hit, else (None, None).
    """
    settings = video_mcp.config.get_settings()
    if not settings.enable_cache:
        return None, None

    # Deterministic hashing of parameters
    input_str = f"voiceover:{voice_id}:{speed:.4f}:{script}"
    hash_val = hashlib.sha256(input_str.encode("utf-8")).hexdigest()
    
    cache_dir = get_cache_dir()
    json_path = cache_dir / f"vo_{hash_val}.json"
    audio_path = cache_dir / f"vo_{hash_val}.mp3"

    if json_path.exists() and audio_path.exists():
        try:
            with json_path.open(encoding="utf-8") as f:
                data = json.load(f)
            # Validate model
            res = AudioResult.model_validate(data)
            logger.info("cache_hit", type="voiceover", hash=hash_val, script_snippet=script[:30])
            return res, audio_path
        except Exception as e:
            logger.warn("cache_read_error", type="voiceover", hash=hash_val, error=str(e))
            # Remove malformed cache files
            json_path.unlink(missing_ok=True)
            audio_path.unlink(missing_ok=True)

    logger.debug("cache_miss", type="voiceover", script_snippet=script[:30])
    return None, None

def cache_voiceover(script: str, voice_id: str, speed: float, result: AudioResult) -> AudioResult:
    """Stores a generated voiceover result into the cache directory."""
    settings = video_mcp.config.get_settings()
    if not settings.enable_cache or not result.output_path:
        return result

    src_audio = Path(result.output_path)
    if not src_audio.exists():
        return result

    input_str = f"voiceover:{voice_id}:{speed:.4f}:{script}"
    hash_val = hashlib.sha256(input_str.encode("utf-8")).hexdigest()
    
    cache_dir = get_cache_dir()
    json_path = cache_dir / f"vo_{hash_val}.json"
    audio_path = cache_dir / f"vo_{hash_val}.mp3"

    try:
        # Copy audio file to cache
        shutil.copy(src_audio, audio_path)
        # Write metadata
        cache_res = result.model_copy()
        cache_res.output_path = str(audio_path)
        with json_path.open("w", encoding="utf-8") as f:
            f.write(cache_res.model_dump_json())
        logger.info("cache_saved", type="voiceover", hash=hash_val)
    except Exception as e:
        logger.warn("cache_write_failed", type="voiceover", error=str(e))
        json_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)

    return result

def get_cached_video(
    image_path: str | None,
    motion_prompt: str,
    duration: int,
    aspect_ratio: str,
    provider: str,
    model: str,
    audio_prompt: str | None,
) -> tuple[VideoResult | None, Path | None]:
    """
    Checks the cache for a previously generated video clip.
    Returns (VideoResult, cached_file_path) if hit, else (None, None).
    """
    settings = video_mcp.config.get_settings()
    if not settings.enable_cache:
        return None, None

    # Get image file content hash
    img_hash = ""
    if image_path:
        img_path = Path(image_path)
        if img_path.exists():
            img_hash = hash_file(img_path)

    # Hash parameters
    input_str = (
        f"video:{img_hash}:{motion_prompt}:{duration}:"
        f"{aspect_ratio}:{provider}:{model}:{audio_prompt or ''}"
    )
    hash_val = hashlib.sha256(input_str.encode("utf-8")).hexdigest()

    cache_dir = get_cache_dir()
    json_path = cache_dir / f"video_{hash_val}.json"
    video_path = cache_dir / f"video_{hash_val}.mp4"

    if json_path.exists() and video_path.exists():
        try:
            with json_path.open(encoding="utf-8") as f:
                data = json.load(f)
            res = VideoResult.model_validate(data)
            logger.info("cache_hit", type="video", hash=hash_val, prompt_snippet=motion_prompt[:30])
            return res, video_path
        except Exception as e:
            logger.warn("cache_read_error", type="video", hash=hash_val, error=str(e))
            json_path.unlink(missing_ok=True)
            video_path.unlink(missing_ok=True)

    logger.debug("cache_miss", type="video", prompt_snippet=motion_prompt[:30])
    return None, None

def cache_video(
    image_path: str | None,
    motion_prompt: str,
    duration: int,
    aspect_ratio: str,
    provider: str,
    model: str,
    audio_prompt: str | None,
    result: VideoResult,
) -> VideoResult:
    """Stores a generated video result into the cache directory."""
    settings = video_mcp.config.get_settings()
    if not settings.enable_cache or not result.output_path:
        return result

    src_video = Path(result.output_path)
    if not src_video.exists():
        return result

    # Get image file content hash
    img_hash = ""
    if image_path:
        img_path = Path(image_path)
        if img_path.exists():
            img_hash = hash_file(img_path)

    # Hash parameters
    input_str = (
        f"video:{img_hash}:{motion_prompt}:{duration}:"
        f"{aspect_ratio}:{provider}:{model}:{audio_prompt or ''}"
    )
    hash_val = hashlib.sha256(input_str.encode("utf-8")).hexdigest()

    cache_dir = get_cache_dir()
    json_path = cache_dir / f"video_{hash_val}.json"
    video_path = cache_dir / f"video_{hash_val}.mp4"

    try:
        shutil.copy(src_video, video_path)
        cache_res = result.model_copy()
        cache_res.output_path = str(video_path)
        with json_path.open("w", encoding="utf-8") as f:
            f.write(cache_res.model_dump_json())
        logger.info("cache_saved", type="video", hash=hash_val)
    except Exception as e:
        logger.warn("cache_write_failed", type="video", error=str(e))
        json_path.unlink(missing_ok=True)
        video_path.unlink(missing_ok=True)

    return result
