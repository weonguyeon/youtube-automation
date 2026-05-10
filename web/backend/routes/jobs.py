"""잡 관리 API 라우트"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from pipeline.config import OUTPUT_DIR
from web.backend.models import (
    BatchJobResponse,
    CreateBatchRequest,
    CreateJobRequest,
    JobListResponse,
    JobResponse,
    JobStatus,
)
from web.backend.services.job_manager import JobManager

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
def create_job(req: CreateJobRequest):
    manager = JobManager.get_instance()
    return manager.create_job(
        topic=req.topic,
        pattern=req.pattern.value,
        fmt=req.format.value,
        color_preset=req.color_preset.value if req.color_preset else None,
        render_engine=req.render_engine.value if req.render_engine else None,
        upload=req.upload,
        csv_path=req.csv_path,
        platforms=req.platforms,
    )


@router.post("/batch", response_model=BatchJobResponse, status_code=201)
def create_batch(req: CreateBatchRequest):
    """배치 잡 생성 — 여러 영상을 한 번에 큐잉"""
    from datetime import datetime

    manager = JobManager.get_instance()
    defaults_dict = req.defaults.model_dump(mode="json") if req.defaults else None
    jobs_dicts = [j.model_dump(mode="json") for j in req.jobs]
    batch_id, job_ids = manager.create_batch(defaults_dict, jobs_dicts)
    return BatchJobResponse(
        batch_id=batch_id,
        total=len(job_ids),
        job_ids=job_ids,
        created_at=datetime.now().isoformat(),
    )


@router.get("/batches")
def list_batches():
    """배치 목록"""
    manager = JobManager.get_instance()
    batches = manager.list_batches()
    return {"batches": batches, "total": len(batches)}


@router.get("", response_model=JobListResponse)
def list_jobs(status: JobStatus | None = None):
    manager = JobManager.get_instance()
    jobs = manager.list_jobs(status=status)
    return JobListResponse(jobs=jobs, total=len(jobs))


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    manager = JobManager.get_instance()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str):
    manager = JobManager.get_instance()
    if not manager.delete_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")


@router.get("/{job_id}/sse")
async def job_sse(job_id: str):
    """SSE 엔드포인트 — pipeline_report.json 파일 폴링으로 Stage 진행 스트리밍"""
    manager = JobManager.get_instance()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream():
        last_data = ""
        while True:
            # 잡 상태 확인
            current_job = manager.get_job(job_id)
            if not current_job:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
                break

            # pipeline_report.json 읽기
            report_path = OUTPUT_DIR / (current_job.video_id or job_id) / "pipeline_report.json"
            report_data = {}
            if report_path.exists():
                try:
                    report_data = json.loads(report_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pass

            event = {
                "type": "progress",
                "job_id": job_id,
                "status": current_job.status.value,
                "current_stage": current_job.current_stage,
                "stages": [
                    {
                        "name": s.get("name", ""),
                        "duration_sec": s.get("duration_sec", 0),
                        "success": s.get("success", False),
                        "error": s.get("error"),
                    }
                    for s in report_data.get("stages", [])
                ],
            }
            data = json.dumps(event, ensure_ascii=False)

            # 변경된 경우에만 전송
            if data != last_data:
                yield f"data: {data}\n\n"
                last_data = data

            # 완료/실패 시 종료 이벤트
            if current_job.status.value in ("completed", "failed"):
                final = {
                    "type": "done",
                    "job_id": job_id,
                    "status": current_job.status.value,
                    "stages": event["stages"],
                }
                yield f"data: {json.dumps(final, ensure_ascii=False)}\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
