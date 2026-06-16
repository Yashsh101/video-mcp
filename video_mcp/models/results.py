
from pydantic import BaseModel


class VideoResult(BaseModel):
    output_path: str
    duration_seconds: float
    width: int
    height: int
    fps: int
    file_size_mb: float
    provider_used: str
    cost_credits: float | None = None

class AudioResult(BaseModel):
    output_path: str
    duration_seconds: float
    voice_id: str
    character_count: int
    cost_credits: float | None = None

class BatchResult(BaseModel):
    results: list[VideoResult]
    total_cost_credits: float
    failed_scenes: list[int]
    total_duration_seconds: float

class ReelResult(BaseModel):
    output_path: str
    total_duration: float
    scene_count: int
    cost_breakdown: dict[str, float]
    storyboard_path: str | None = None

class CharacterProfile(BaseModel):
    profile_id: str
    character_name: str
    style: str
    reference_count: int
    prompt_descriptor: str

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending/running/complete/failed
    progress_pct: float
    output_path: str | None = None
    error: str | None = None

class AnalysisResult(BaseModel):
    scenes: list[dict]
    thumbnails: list[str]
    quality_score: float
    issues: list[str]
