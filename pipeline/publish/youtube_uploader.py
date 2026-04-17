"""YouTube Data API v3 업로드 모듈"""

from __future__ import annotations

import logging
from pathlib import Path

from pipeline.schema import VideoMetadata

logger = logging.getLogger(__name__)


class YouTubeUploader:
    """YouTube 예약 업로드"""

    def upload(self, video_path: Path, metadata: VideoMetadata) -> str:
        """영상을 YouTube에 업로드하고 URL 반환"""
        # TODO: YouTube Data API v3 연동
        # google-api-python-client + google-auth-oauthlib
        logger.info("YouTube 업로드: %s → %s", video_path.name, metadata.title)
        logger.warning("YouTube API 미연동 — 스킵")
        return f"https://youtube.com/shorts/PLACEHOLDER"
