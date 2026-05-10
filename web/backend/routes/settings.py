"""설정 API 라우트 — .env 파일 읽기/쓰기"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from pipeline.config import CONFIG_DIR, settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

ENV_PATH = CONFIG_DIR / ".env"


class SettingsResponse(BaseModel):
    deploy_mode: str
    has_anthropic_key: bool
    has_elevenlabs_key: bool
    has_youtube_credentials: bool
    has_flux_key: bool
    has_pexels_key: bool
    ffmpeg_path: str
    brand_color_preset: str
    default_language: str
    default_font: str


class SettingsUpdateRequest(BaseModel):
    deploy_mode: str | None = None
    anthropic_api_key: str | None = None
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    youtube_client_id: str | None = None
    youtube_client_secret: str | None = None
    flux_api_key: str | None = None
    pexels_api_key: str | None = None
    ffmpeg_path: str | None = None
    brand_color_preset: str | None = None


def _read_env() -> dict[str, str]:
    """Parse .env file into dict"""
    env: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _write_env(env: dict[str, str]) -> None:
    """Write dict back to .env file"""
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'{k}="{v}"' for k, v in sorted(env.items())]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


@router.get("", response_model=SettingsResponse)
def get_settings():
    return SettingsResponse(
        deploy_mode=settings.deploy_mode,
        has_anthropic_key=bool(settings.anthropic_api_key),
        has_elevenlabs_key=bool(settings.elevenlabs_api_key),
        has_youtube_credentials=bool(settings.youtube_client_id and settings.youtube_client_secret),
        has_flux_key=bool(settings.flux_api_key),
        has_pexels_key=bool(settings.pexels_api_key),
        ffmpeg_path=settings.ffmpeg_path,
        brand_color_preset=settings.brand_color_preset,
        default_language=settings.default_language,
        default_font=settings.default_font,
    )


@router.put("", response_model=SettingsResponse)
def update_settings(req: SettingsUpdateRequest):
    env = _read_env()

    field_map = {
        "deploy_mode": "DEPLOY_MODE",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "elevenlabs_api_key": "ELEVENLABS_API_KEY",
        "elevenlabs_voice_id": "ELEVENLABS_VOICE_ID",
        "youtube_client_id": "YOUTUBE_CLIENT_ID",
        "youtube_client_secret": "YOUTUBE_CLIENT_SECRET",
        "flux_api_key": "FLUX_API_KEY",
        "pexels_api_key": "PEXELS_API_KEY",
        "ffmpeg_path": "FFMPEG_PATH",
        "brand_color_preset": "BRAND_COLOR_PRESET",
    }

    for field_name, env_key in field_map.items():
        value = getattr(req, field_name, None)
        if value is not None:
            env[env_key] = value
            # 런타임 설정도 업데이트
            if hasattr(settings, field_name):
                setattr(settings, field_name, value)

    _write_env(env)
    return get_settings()
