"""파이프라인 모니터링 — 실행 시간 추적 + 에러 리포트

각 Stage 실행 시간을 기록하고, 실패 시 JSON 에러 리포트를 저장.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from pipeline.config import OUTPUT_DIR

logger = logging.getLogger(__name__)


@dataclass
class StageMetric:
    name: str
    start_time: float = 0.0
    end_time: float = 0.0
    success: bool = False
    error: str | None = None

    @property
    def duration_sec(self) -> float:
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0


@dataclass
class PipelineMetrics:
    video_id: str
    topic: str
    pattern: str
    format: str
    started_at: str = ""
    stages: list[StageMetric] = field(default_factory=list)
    total_duration_sec: float = 0.0
    success: bool = False

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "topic": self.topic,
            "pattern": self.pattern,
            "format": self.format,
            "started_at": self.started_at,
            "success": self.success,
            "total_duration_sec": round(self.total_duration_sec, 2),
            "stages": [
                {
                    "name": s.name,
                    "duration_sec": round(s.duration_sec, 2),
                    "success": s.success,
                    "error": s.error,
                }
                for s in self.stages
            ],
        }


class PipelineMonitor:
    """파이프라인 실행 모니터"""

    def __init__(self, video_id: str, topic: str, pattern: str, fmt: str):
        self.metrics = PipelineMetrics(
            video_id=video_id,
            topic=topic,
            pattern=pattern,
            format=fmt,
            started_at=datetime.now().isoformat(),
        )
        self._pipeline_start = time.time()
        self._current_stage: StageMetric | None = None

    def start_stage(self, name: str):
        """Stage 시작 기록"""
        self._current_stage = StageMetric(name=name, start_time=time.time())
        logger.info("[Monitor] Stage 시작: %s", name)

    def end_stage(self, success: bool = True, error: str | None = None):
        """Stage 종료 기록"""
        if self._current_stage is None:
            return

        self._current_stage.end_time = time.time()
        self._current_stage.success = success
        self._current_stage.error = error
        self.metrics.stages.append(self._current_stage)

        status = "OK" if success else "FAIL"
        logger.info(
            "[Monitor] Stage 완료: %s — %s (%.1fs)",
            self._current_stage.name, status, self._current_stage.duration_sec,
        )
        self._current_stage = None

    def finish(self, success: bool = True):
        """파이프라인 종료 & 리포트 저장"""
        self.metrics.success = success
        self.metrics.total_duration_sec = time.time() - self._pipeline_start
        self._save_report()

        # 실패 시 에러 요약 출력
        failed = [s for s in self.metrics.stages if not s.success]
        if failed:
            logger.error("[Monitor] 실패 Stage: %s", ", ".join(s.name for s in failed))

        logger.info(
            "[Monitor] 파이프라인 %s — 총 %.1fs (%d stages)",
            "성공" if success else "실패",
            self.metrics.total_duration_sec,
            len(self.metrics.stages),
        )

    def _save_report(self):
        """JSON 리포트 저장"""
        report_dir = OUTPUT_DIR / self.metrics.video_id
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "pipeline_report.json"

        report_path.write_text(
            json.dumps(self.metrics.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
