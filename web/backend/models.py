"""API 요청/응답 Pydantic 모델"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from pipeline.schema import ColorPreset, Pattern, RenderEngine, VideoFormat


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CreateJobRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    pattern: Pattern = Pattern.B_TEXT_SHORTS
    format: VideoFormat = VideoFormat.S15
    color_preset: ColorPreset | None = None
    render_engine: RenderEngine | None = None
    upload: bool = False
    csv_path: str | None = None
    platforms: list[str] | None = None


class BatchJobItem(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    pattern: Pattern | None = None
    format: VideoFormat | None = None
    color_preset: ColorPreset | None = None
    render_engine: RenderEngine | None = None
    upload: bool | None = None
    csv_path: str | None = None
    platforms: list[str] | None = None


class CreateBatchRequest(BaseModel):
    defaults: BatchJobItem | None = None
    jobs: list[BatchJobItem] = Field(..., min_length=1)


class BatchJobResponse(BaseModel):
    batch_id: str
    total: int
    job_ids: list[str]
    created_at: str


class StageInfo(BaseModel):
    name: str
    duration_sec: float = 0.0
    success: bool = False
    error: str | None = None


class JobResponse(BaseModel):
    job_id: str
    video_id: str | None = None
    status: JobStatus
    topic: str
    pattern: str
    format: str
    color_preset: str | None = None
    render_engine: str | None = None
    created_at: str
    completed_at: str | None = None
    video_path: str | None = None
    thumbnail_path: str | None = None
    errors: list[str] = Field(default_factory=list)
    stages: list[StageInfo] = Field(default_factory=list)
    current_stage: str | None = None


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int


class VideoInfo(BaseModel):
    video_id: str
    topic: str | None = None
    pattern: str | None = None
    format: str | None = None
    created_at: str | None = None
    video_path: str
    thumbnail_path: str | None = None
    duration_sec: float | None = None
    success: bool = True
    stages: list[StageInfo] = Field(default_factory=list)


class VideoListResponse(BaseModel):
    videos: list[VideoInfo]
    total: int
