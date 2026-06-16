
from pydantic import BaseModel


class GenerationRequest(BaseModel):
    image_path: str
    motion_prompt: str
    duration: int = 5
    aspect_ratio: str = "9:16"
    provider: str = "kling"
    model: str = "auto"
    audio_prompt: str | None = None

class TextToVideoRequest(BaseModel):
    prompt: str
    duration: int = 5
    aspect_ratio: str = "9:16"
    style: str = "cinematic"
    provider: str = "kling"

class VoiceoverRequest(BaseModel):
    script: str
    voice_id: str = "adam"
    speed: float = 0.95
    output_path: str | None = None

class SceneRequest(BaseModel):
    scene_number: int
    image_path: str
    motion_prompt: str
    duration: int = 5
    audio_prompt: str | None = None

class BatchGenerationRequest(BaseModel):
    scenes: list[SceneRequest]
    provider: str = "kling"
    max_concurrent: int = 4

class ClipSequence(BaseModel):
    clip_path: str
    start_time: float
    duration: float
    transition: str = "dissolve"

class AssembleReelRequest(BaseModel):
    clips: list[ClipSequence]
    voiceover_path: str
    bgm_path: str | None = None
    bgm_volume: float = 0.12
    output_path: str | None = None
    aspect_ratio: str = "9:16"
    add_captions: bool = True

class CharacterLockRequest(BaseModel):
    reference_images: list[str]
    character_name: str
    style: str = "pixar"

class ReelBriefRequest(BaseModel):
    script: str
    style: str = "pixar"
    platform: str = "instagram"
    provider: str = "kling"
    voice_id: str = "adam"
    character_name: str | None = None
