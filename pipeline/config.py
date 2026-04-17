"""환경변수 및 설정 관리"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
CONFIG_DIR = PROJECT_ROOT / "config"

# .env 로드
load_dotenv(CONFIG_DIR / ".env")


class Settings:
    """전역 설정"""

    # Claude CLI (개발) vs API (배포)
    deploy_mode: str = os.getenv("DEPLOY_MODE", "cli")  # "cli" or "api"
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # ElevenLabs TTS
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "")

    # YouTube
    youtube_client_id: str = os.getenv("YOUTUBE_CLIENT_ID", "")
    youtube_client_secret: str = os.getenv("YOUTUBE_CLIENT_SECRET", "")

    # 이미지 생성
    flux_api_key: str = os.getenv("FLUX_API_KEY", "")
    pexels_api_key: str = os.getenv("PEXELS_API_KEY", "")

    # FFmpeg
    ffmpeg_path: str = os.getenv("FFMPEG_PATH", "ffmpeg")

    # 채널 브랜딩 (한 번 설정하면 모든 영상에 일관 적용)
    brand_color_preset: str = os.getenv("BRAND_COLOR_PRESET", "midnight_navy")

    # 기본값
    default_language: str = "ko"
    default_font: str = "Pretendard Bold"
    font_path: str = str(ASSETS_DIR / "fonts" / "Pretendard-Bold.otf")


settings = Settings()
