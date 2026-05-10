"""배치 모드 — 여러 영상을 하나의 YAML/JSON 파일로 정의해 순차 실행

사용 예시 (YAML):
    defaults:
      pattern: B
      format: S15
      color_preset: midnight_navy
      platforms: [youtube_shorts, tiktok]
    jobs:
      - topic: "커피의 5가지 효과"
      - topic: "AI 트렌드 2026"
        pattern: A
        format: L3
      - topic: "역사 What If — 알렉산더가 살았다면"
        platforms: [youtube_long]

CLI: yt-auto --batch jobs.yaml
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from pipeline.config import OUTPUT_DIR
from pipeline.orchestrator import PipelineResult, VideoPipeline
from pipeline.schema import ColorPreset, Pattern, RenderEngine, VideoFormat

logger = logging.getLogger(__name__)


@dataclass
class BatchJob:
    topic: str
    pattern: Pattern = Pattern.B_TEXT_SHORTS
    format: VideoFormat = VideoFormat.S15
    color_preset: ColorPreset | None = None
    render_engine: RenderEngine | None = None
    upload: bool = False
    csv_path: str | None = None
    platforms: list[str] | None = None


@dataclass
class BatchItemResult:
    topic: str
    success: bool
    video_id: str
    video_path: str | None = None
    errors: list[str] = field(default_factory=list)
    duration_sec: float = 0.0
    platform_exports: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "success": self.success,
            "video_id": self.video_id,
            "video_path": self.video_path,
            "errors": self.errors,
            "duration_sec": round(self.duration_sec, 2),
            "platform_exports": self.platform_exports,
        }


@dataclass
class BatchSummary:
    total: int
    success_count: int
    fail_count: int
    items: list[BatchItemResult] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    report_path: Path | None = None


def _coerce_pattern(v: Any) -> Pattern:
    if isinstance(v, Pattern):
        return v
    return Pattern(str(v))


def _coerce_format(v: Any) -> VideoFormat:
    if isinstance(v, VideoFormat):
        return v
    return VideoFormat(str(v))


def _coerce_color(v: Any) -> ColorPreset | None:
    if v is None or v == "":
        return None
    if isinstance(v, ColorPreset):
        return v
    return ColorPreset(str(v))


def _coerce_engine(v: Any) -> RenderEngine | None:
    if v is None or v == "":
        return None
    if isinstance(v, RenderEngine):
        return v
    return RenderEngine(str(v))


def parse_batch_file(path: str | Path) -> list[BatchJob]:
    """YAML/JSON 배치 파일을 BatchJob 리스트로 파싱"""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"배치 파일이 없습니다: {file_path}")

    text = file_path.read_text(encoding="utf-8")
    if file_path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)

    if not isinstance(data, dict):
        raise ValueError("배치 파일은 dict 루트여야 합니다 (defaults/jobs 키)")

    defaults = data.get("defaults") or {}
    raw_jobs = data.get("jobs") or []

    if not raw_jobs:
        raise ValueError("'jobs' 리스트가 비어있습니다")

    jobs: list[BatchJob] = []
    for i, raw in enumerate(raw_jobs):
        merged = {**defaults, **raw}
        if "topic" not in merged or not merged["topic"]:
            raise ValueError(f"jobs[{i}]: 'topic'이 필수입니다")

        jobs.append(BatchJob(
            topic=str(merged["topic"]),
            pattern=_coerce_pattern(merged.get("pattern", "B")),
            format=_coerce_format(merged.get("format", "S15")),
            color_preset=_coerce_color(merged.get("color_preset")),
            render_engine=_coerce_engine(merged.get("render_engine")),
            upload=bool(merged.get("upload", False)),
            csv_path=merged.get("csv_path"),
            platforms=list(merged["platforms"]) if merged.get("platforms") else None,
        ))

    return jobs


def run_batch(
    batch_file: str | Path,
    progress_callback=None,
) -> BatchSummary:
    """배치 파일을 읽어 순차 실행. 각 잡 결과를 누적해 BatchSummary 반환.

    progress_callback(index, total, item_result): 진행 후크 (옵션)
    """
    jobs = parse_batch_file(batch_file)
    return run_batch_jobs(jobs, progress_callback=progress_callback)


def run_batch_jobs(
    jobs: list[BatchJob],
    progress_callback=None,
) -> BatchSummary:
    """이미 파싱된 BatchJob 리스트를 순차 실행"""
    started = time.time()
    started_iso = _now_iso()
    pipeline = VideoPipeline()

    items: list[BatchItemResult] = []
    success_count = 0

    for i, job in enumerate(jobs):
        logger.info("[Batch %d/%d] 시작: %s", i + 1, len(jobs), job.topic)
        job_start = time.time()

        item: BatchItemResult
        try:
            result: PipelineResult = pipeline.run(
                topic=job.topic,
                pattern=job.pattern,
                fmt=job.format,
                color_preset=job.color_preset,
                render_engine=job.render_engine,
                upload=job.upload,
                csv_path=job.csv_path,
                platforms=job.platforms,
            )
            item = BatchItemResult(
                topic=job.topic,
                success=result.success,
                video_id=result.video_id,
                video_path=str(result.video_path) if result.video_path else None,
                errors=list(result.errors),
                duration_sec=time.time() - job_start,
                platform_exports=list(result.platform_exports),
            )
        except Exception as e:
            logger.exception("[Batch %d/%d] 실패: %s", i + 1, len(jobs), e)
            item = BatchItemResult(
                topic=job.topic,
                success=False,
                video_id="",
                errors=[str(e)],
                duration_sec=time.time() - job_start,
            )

        items.append(item)
        if item.success:
            success_count += 1

        if progress_callback is not None:
            try:
                progress_callback(i + 1, len(jobs), item)
            except Exception:
                logger.debug("progress_callback 예외 무시")

    finished_iso = _now_iso()
    summary = BatchSummary(
        total=len(jobs),
        success_count=success_count,
        fail_count=len(jobs) - success_count,
        items=items,
        started_at=started_iso,
        finished_at=finished_iso,
    )

    summary.report_path = _save_batch_report(summary, started)
    logger.info(
        "[Batch] 완료 — 성공 %d / 실패 %d (총 %.1fs)",
        success_count, summary.fail_count, time.time() - started,
    )
    return summary


def _save_batch_report(summary: BatchSummary, started: float) -> Path:
    batch_dir = OUTPUT_DIR / "_batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    name = time.strftime("batch-%Y%m%d-%H%M%S.json", time.localtime(started))
    report_path = batch_dir / name
    report_path.write_text(
        json.dumps(
            {
                "started_at": summary.started_at,
                "finished_at": summary.finished_at,
                "total": summary.total,
                "success_count": summary.success_count,
                "fail_count": summary.fail_count,
                "items": [it.to_dict() for it in summary.items],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return report_path


def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().isoformat(timespec="seconds")
