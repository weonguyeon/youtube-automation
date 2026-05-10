"""잡 매니저 — ProcessPoolExecutor 기반 비동기 파이프라인 실행"""

from __future__ import annotations

import logging
import uuid
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import datetime
from threading import Lock

from web.backend.models import JobResponse, JobStatus, StageInfo

logger = logging.getLogger(__name__)

MAX_WORKERS = 2


def _run_pipeline(
    topic: str,
    pattern: str,
    fmt: str,
    color_preset: str | None,
    render_engine: str | None,
    upload: bool,
    csv_path: str | None,
    platforms: list[str] | None = None,
) -> dict:
    """별도 프로세스에서 파이프라인 실행 (pickle 가능한 인자만 사용)"""
    from pipeline.orchestrator import VideoPipeline
    from pipeline.schema import ColorPreset as CP
    from pipeline.schema import Pattern, VideoFormat
    from pipeline.schema import RenderEngine as RE

    pipeline = VideoPipeline()
    result = pipeline.run(
        topic=topic,
        pattern=Pattern(pattern),
        fmt=VideoFormat(fmt),
        color_preset=CP(color_preset) if color_preset else None,
        render_engine=RE(render_engine) if render_engine else None,
        upload=upload,
        csv_path=csv_path,
        platforms=platforms,
    )
    return {
        "video_id": result.video_id,
        "video_path": str(result.video_path) if result.video_path else None,
        "upload_url": result.upload_url,
        "errors": result.errors,
        "success": result.success,
        "platform_exports": result.platform_exports,
    }


class JobRecord:
    def __init__(
        self,
        job_id: str,
        topic: str,
        pattern: str,
        fmt: str,
        color_preset: str | None,
        render_engine: str | None,
        platforms: list[str] | None = None,
        batch_id: str | None = None,
    ):
        self.job_id = job_id
        self.topic = topic
        self.pattern = pattern
        self.format = fmt
        self.color_preset = color_preset
        self.render_engine = render_engine
        self.platforms = platforms or []
        self.batch_id = batch_id
        self.status = JobStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.completed_at: str | None = None
        self.video_id: str | None = None
        self.video_path: str | None = None
        self.errors: list[str] = []
        self.platform_exports: list[dict] = []
        self.future: Future | None = None

    @property
    def current_stage(self) -> str | None:
        # pipeline_report.json의 마지막 stage 이름을 반환 (SSE/응답용)
        stages = self._load_stages()
        if not stages:
            return None
        # 진행중일 때만 마지막 stage가 곧 current
        if self.status == JobStatus.RUNNING:
            return stages[-1].name
        return None

    def to_response(self) -> JobResponse:
        # pipeline_report.json에서 stage 정보 로드
        stages = []
        if self.video_id:
            stages = self._load_stages()

        return JobResponse(
            job_id=self.job_id,
            video_id=self.video_id,
            status=self.status,
            topic=self.topic,
            pattern=self.pattern,
            format=self.format,
            color_preset=self.color_preset,
            render_engine=self.render_engine,
            created_at=self.created_at,
            completed_at=self.completed_at,
            video_path=self.video_path,
            thumbnail_path=self._find_thumbnail(),
            errors=self.errors,
            stages=stages,
            current_stage=self.current_stage,
        )

    def _load_stages(self) -> list[StageInfo]:
        import json

        from pipeline.config import OUTPUT_DIR

        if not self.video_id:
            return []
        report_path = OUTPUT_DIR / self.video_id / "pipeline_report.json"
        if not report_path.exists():
            return []
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
            return [
                StageInfo(
                    name=s["name"],
                    duration_sec=s.get("duration_sec", 0),
                    success=s.get("success", False),
                    error=s.get("error"),
                )
                for s in data.get("stages", [])
            ]
        except Exception:
            return []

    def _find_thumbnail(self) -> str | None:
        if not self.video_id:
            return None
        from pipeline.config import OUTPUT_DIR

        thumb = OUTPUT_DIR / self.video_id / "thumbnail.png"
        return str(thumb) if thumb.exists() else None


class JobManager:
    _instance: JobManager | None = None

    def __init__(self):
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()
        self._executor = ProcessPoolExecutor(max_workers=MAX_WORKERS)

    @classmethod
    def get_instance(cls) -> JobManager:
        if cls._instance is None:
            cls._instance = JobManager()
        return cls._instance

    def create_job(
        self,
        topic: str,
        pattern: str,
        fmt: str,
        color_preset: str | None = None,
        render_engine: str | None = None,
        upload: bool = False,
        csv_path: str | None = None,
        platforms: list[str] | None = None,
        batch_id: str | None = None,
    ) -> JobResponse:
        job_id = str(uuid.uuid4())[:8]

        with self._lock:
            record = JobRecord(
                job_id=job_id,
                topic=topic,
                pattern=pattern,
                fmt=fmt,
                color_preset=color_preset,
                render_engine=render_engine,
                platforms=platforms,
                batch_id=batch_id,
            )
            record.status = JobStatus.RUNNING
            self._jobs[job_id] = record

        future = self._executor.submit(
            _run_pipeline,
            topic=topic,
            pattern=pattern,
            fmt=fmt,
            color_preset=color_preset,
            render_engine=render_engine,
            upload=upload,
            csv_path=csv_path,
            platforms=platforms,
        )
        record.future = future
        future.add_done_callback(lambda f: self._on_complete(job_id, f))

        return record.to_response()

    def create_batch(
        self,
        defaults: dict | None,
        jobs: list[dict],
    ) -> tuple[str, list[str]]:
        """배치 잡 생성 — defaults 와 각 job 을 머지해 큐에 등록"""
        batch_id = str(uuid.uuid4())[:8]
        defaults = defaults or {}
        job_ids: list[str] = []

        for raw in jobs:
            merged = {**defaults, **{k: v for k, v in raw.items() if v is not None}}
            response = self.create_job(
                topic=merged["topic"],
                pattern=str(merged.get("pattern", "B")),
                fmt=str(merged.get("format", "S15")),
                color_preset=merged.get("color_preset"),
                render_engine=merged.get("render_engine"),
                upload=bool(merged.get("upload", False)),
                csv_path=merged.get("csv_path"),
                platforms=merged.get("platforms"),
                batch_id=batch_id,
            )
            job_ids.append(response.job_id)

        return batch_id, job_ids

    def list_batches(self) -> list[dict]:
        """배치별 잡 그루핑 — UI 배치 뷰용"""
        with self._lock:
            grouped: dict[str, list[JobRecord]] = {}
            for record in self._jobs.values():
                if record.batch_id:
                    grouped.setdefault(record.batch_id, []).append(record)

        result = []
        for batch_id, records in grouped.items():
            records.sort(key=lambda r: r.created_at)
            statuses = [r.status for r in records]
            done = sum(1 for s in statuses if s in (JobStatus.COMPLETED, JobStatus.FAILED))
            success = sum(1 for s in statuses if s == JobStatus.COMPLETED)
            result.append({
                "batch_id": batch_id,
                "total": len(records),
                "done": done,
                "success": success,
                "failed": done - success,
                "created_at": records[0].created_at,
                "job_ids": [r.job_id for r in records],
            })
        result.sort(key=lambda b: b["created_at"], reverse=True)
        return result

    def _on_complete(self, job_id: str, future: Future):
        with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                return

            record.completed_at = datetime.now().isoformat()

            try:
                result = future.result()
                record.video_id = result["video_id"]
                record.video_path = result["video_path"]
                record.errors = result["errors"]
                record.platform_exports = result.get("platform_exports") or []
                record.status = (
                    JobStatus.COMPLETED if result["success"] else JobStatus.FAILED
                )
            except Exception as e:
                record.status = JobStatus.FAILED
                record.errors.append(str(e))
                logger.error("Job %s failed: %s", job_id, e)

    def get_job(self, job_id: str) -> JobResponse | None:
        with self._lock:
            record = self._jobs.get(job_id)
            return record.to_response() if record else None

    def list_jobs(self, status: JobStatus | None = None) -> list[JobResponse]:
        with self._lock:
            jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [j.to_response() for j in jobs]

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            record = self._jobs.pop(job_id, None)
            if record and record.future and not record.future.done():
                record.future.cancel()
            return record is not None

    def shutdown(self):
        self._executor.shutdown(wait=False)
