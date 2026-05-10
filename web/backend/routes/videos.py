"""영상 갤러리 API 라우트"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from pipeline.config import OUTPUT_DIR
from web.backend.models import StageInfo, VideoInfo, VideoListResponse

router = APIRouter(prefix="/api/videos", tags=["videos"])


def _scan_videos() -> list[VideoInfo]:
    """output/ 디렉토리를 스캔하여 완성된 영상 목록 반환 (생성 시간 desc)"""
    videos = []

    if not OUTPUT_DIR.exists():
        return videos

    for video_dir in OUTPUT_DIR.iterdir():
        # 배치 리포트 등 시스템 디렉토리 제외
        if not video_dir.is_dir() or video_dir.name.startswith("_"):
            continue

        final_mp4 = video_dir / "final.mp4"
        if not final_mp4.exists():
            continue

        # script.json에서 메타데이터 추출
        topic = None
        pattern = None
        fmt = None
        script_path = video_dir / "script.json"
        if script_path.exists():
            try:
                script = json.loads(script_path.read_text(encoding="utf-8"))
                metadata = script.get("metadata", {})
                topic = metadata.get("title", script.get("topic"))
                pattern = script.get("pattern")
                fmt = script.get("format")
            except Exception:
                pass

        # pipeline_report.json에서 실행 정보 추출
        created_at = None
        duration_sec = None
        success = True
        stages = []
        report_path = video_dir / "pipeline_report.json"
        if report_path.exists():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
                created_at = report.get("started_at")
                duration_sec = report.get("total_duration_sec")
                success = report.get("success", True)
                stages = [
                    StageInfo(
                        name=s["name"],
                        duration_sec=s.get("duration_sec", 0),
                        success=s.get("success", False),
                        error=s.get("error"),
                    )
                    for s in report.get("stages", [])
                ]
            except Exception:
                pass

        # 썸네일 확인
        thumb = video_dir / "thumbnail.png"
        thumb_path = str(thumb) if thumb.exists() else None

        # created_at 폴백 — 리포트가 없으면 final.mp4 mtime
        if not created_at:
            try:
                from datetime import datetime
                created_at = datetime.fromtimestamp(final_mp4.stat().st_mtime).isoformat()
            except OSError:
                created_at = None

        videos.append(
            VideoInfo(
                video_id=video_dir.name,
                topic=topic,
                pattern=pattern,
                format=fmt,
                created_at=created_at,
                video_path=str(final_mp4),
                thumbnail_path=thumb_path,
                duration_sec=duration_sec,
                success=success,
                stages=stages,
            )
        )

    # 최신순 정렬 (created_at desc, 없으면 가장 뒤로)
    videos.sort(key=lambda v: v.created_at or "", reverse=True)
    return videos


@router.get("", response_model=VideoListResponse)
def list_videos():
    videos = _scan_videos()
    return VideoListResponse(videos=videos, total=len(videos))


@router.get("/{video_id}")
def get_video(video_id: str):
    video_dir = OUTPUT_DIR / video_id
    if not video_dir.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    final_mp4 = video_dir / "final.mp4"
    if not final_mp4.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # 전체 정보 반환
    videos = _scan_videos()
    for v in videos:
        if v.video_id == video_id:
            return v
    raise HTTPException(status_code=404, detail="Video not found")


@router.get("/{video_id}/stream")
def stream_video(video_id: str):
    video_dir = OUTPUT_DIR / video_id
    final_mp4 = video_dir / "final.mp4"
    if not final_mp4.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(str(final_mp4), media_type="video/mp4")


@router.get("/{video_id}/thumbnail")
def get_thumbnail(video_id: str):
    video_dir = OUTPUT_DIR / video_id
    thumb = video_dir / "thumbnail.png"
    if not thumb.exists():
        # AI 이미지 첫 번째 씬을 폴백으로 사용
        for img in sorted(video_dir.glob("ai_scene_*.png")):
            return FileResponse(str(img), media_type="image/png")
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(str(thumb), media_type="image/png")
