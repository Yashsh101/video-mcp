import json
from pathlib import Path

import structlog

from video_mcp.config import get_settings
from video_mcp.errors import ErrorCode, MCPVideoError
from video_mcp.guardrails import validate_input_path
from video_mcp.models.results import CharacterProfile, VideoResult
from video_mcp.tools.generate import generate_video_from_image

logger = structlog.get_logger()

def _get_profile_path(character_name: str) -> Path:
    settings = get_settings()
    char_dir = settings.work_dir / "characters"
    char_dir.mkdir(parents=True, exist_ok=True)
    # Sanitize character name
    safe_name = "".join(c for c in character_name if c.isalnum() or c in ("-", "_")).strip()
    if not safe_name:
        raise MCPVideoError(f"Invalid character name: '{character_name}'", ErrorCode.INVALID_INPUT)
    return char_dir / f"{safe_name}.json"

async def create_character_profile(
    reference_images: list[str],
    character_name: str,
    style: str = "pixar",
) -> CharacterProfile:
    """
    Create and store a reusable character consistency profile with facial features.

    Inputs:
        reference_images: List of local paths to Bob or character image files.
        character_name: Alphanumeric name to identify the profile.
        style: Visual style (pixar, cinematic, hyperrealistic).

    Returns:
        CharacterProfile detailing the stored metadata.
    """
    logger.info("tool_call", tool_name="create_character_profile", character_name=character_name)

    if not reference_images:
        raise MCPVideoError("Must provide at least one reference image path.", ErrorCode.INVALID_INPUT)

    # Validate all reference images
    validated_paths = []
    for img in reference_images:
        validated_paths.append(str(validate_input_path(img)))

    # Construct structured prompt fragment describing visual cues
    # Bob defaults as senior entrepreneur
    if "bob" in character_name.lower():
        prompt_descriptor = (
            "an elderly man, around 70 years old, with short silver-grey hair, "
            "wearing thin rectangular glasses, styled in Pixar Up movie aesthetic, "
            "highly detailed animated rendering"
        )
    else:
        prompt_descriptor = (
            f"a character named {character_name}, in high quality {style} style, "
            "with consistent facial structure and distinctive clothing"
        )

    profile = CharacterProfile(
        profile_id=character_name.lower().replace(" ", "_"),
        character_name=character_name,
        style=style,
        reference_count=len(validated_paths),
        prompt_descriptor=prompt_descriptor,
    )

    # Save to disk
    profile_path = _get_profile_path(character_name)
    try:
        data = profile.model_dump()
        data["reference_images"] = validated_paths  # Store paths alongside metadata
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise MCPVideoError(
            f"Failed to save character profile to disk: {e}",
            ErrorCode.INVALID_INPUT,
        )

    return profile

async def load_character_profile(character_name: str) -> CharacterProfile:
    """
    Load an existing character profile from disk.

    Inputs:
        character_name: Name of character to retrieve.

    Returns:
        CharacterProfile metadata.
    """
    profile_path = _get_profile_path(character_name)
    if not profile_path.exists():
        raise MCPVideoError(
            f"Character profile '{character_name}' not found.",
            ErrorCode.FILE_NOT_FOUND,
            hint="Create it first via create_character_profile.",
        )

    try:
        with open(profile_path, encoding="utf-8") as f:
            data = json.load(f)
        return CharacterProfile(
            profile_id=data["profile_id"],
            character_name=data["character_name"],
            style=data["style"],
            reference_count=data["reference_count"],
            prompt_descriptor=data["prompt_descriptor"],
        )
    except Exception as e:
        raise MCPVideoError(
            f"Failed to load character profile: {e}",
            ErrorCode.INVALID_INPUT,
        )

async def generate_scene_with_character(
    character_name: str,
    scene_description: str,
    camera: str = "medium close-up",
    expression: str = "neutral",
    provider: str = "kling",
    duration: int = 5,
    aspect_ratio: str = "9:16",
) -> VideoResult:
    """
    Generate a video scene featuring a consistent character from a profile.

    Inputs:
        character_name: Target character name.
        scene_description: Visual actions happening in the scene.
        camera: Shot specification (e.g., medium close-up, wide shot).
        expression: Facial emotion (neutral, smiling, angry).
        provider: AI generator engine.
        duration: Clip length in seconds.
        aspect_ratio: Destination screen size.

    Returns:
        VideoResult containing clip file information.
    """
    logger.info("tool_call", tool_name="generate_scene_with_character", character=character_name)
    
    # Load profile data
    profile_path = _get_profile_path(character_name)
    if not profile_path.exists():
        raise MCPVideoError(
            f"Character profile '{character_name}' not found.",
            ErrorCode.FILE_NOT_FOUND,
            hint="Run create_character_profile first.",
        )

    with open(profile_path, encoding="utf-8") as f:
        data = json.load(f)

    reference_images = data.get("reference_images", [])
    if not reference_images:
        raise MCPVideoError(
            f"Character profile '{character_name}' has no reference images.",
            ErrorCode.INVALID_INPUT,
        )

    descriptor = data["prompt_descriptor"]
    first_image = reference_images[0]

    # Inject descriptor to anchor visual styling
    augmented_prompt = (
        f"{descriptor}, camera: {camera}, expression: {expression}, {scene_description}"
    )

    # Call image generation
    return await generate_video_from_image(
        image_path=first_image,
        motion_prompt=augmented_prompt,
        duration=duration,
        aspect_ratio=aspect_ratio,
        provider=provider,
    )
