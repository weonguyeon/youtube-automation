"""멀티플랫폼 익스포트 — 최종 mp4를 플랫폼별 규격으로 재인코딩

각 플랫폼이 요구하는 비율/최대 길이/해상도에 맞춰
원본 final.mp4를 변환하여 output/{video_id}/exports/{platform}.mp4 에 저장한다.

업로드 자동화는 포함하지 않는다 (수동 업로드/예약 업로드용 산출물 생성만).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import ffmpeg

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    YOUTUBE_SHORTS = "youtube_shorts"
    YOUTUBE_LONG = "youtube_long"
    TIKTOK = "tiktok"
    INSTAGRAM_REELS = "instagram_reels"
    INSTAGRAM_FEED = "instagram_feed"
    X_TWITTER = "x_twitter"


@dataclass(frozen=True)
class PlatformSpec:
    label: str
    width: int
    height: int
    max_duration_sec: int | None  # None = 제한 없음
    description: str


PLATFORM_SPECS: dict[Platform, PlatformSpec] = {
    Platform.YOUTUBE_SHORTS: PlatformSpec(
        label="YouTube Shorts", width=1080, height=1920,
        max_duration_sec=60,
        description="9:16 세로, 최대 60초",
    ),
    Platform.YOUTUBE_LONG: PlatformSpec(
        label="YouTube (Long)", width=1920, height=1080,
        max_duration_sec=None,
        description="16:9 가로, 길이 제한 없음",
    ),
    Platform.TIKTOK: PlatformSpec(
        label="TikTok", width=1080, height=1920,
        max_duration_sec=180,
        description="9:16 세로, 최대 3분",
    ),
    Platform.INSTAGRAM_REELS: PlatformSpec(
        label="Instagram Reels", width=1080, height=1920,
        max_duration_sec=90,
        description="9:16 세로, 최대 90초",
    ),
    Platform.INSTAGRAM_FEED: PlatformSpec(
        label="Instagram Feed", width=1080, height=1080,
        max_duration_sec=60,
        description="1:1 정사각, 최대 60초",
    ),
    Platform.X_TWITTER: PlatformSpec(
        label="X (Twitter)", width=1280, height=720,
        max_duration_sec=140,
        description="16:9 가로, 최대 2분 20초",
    ),
}


@dataclass
class ExportResult:
    platform: Platform
    output_path: Path
    width: int
    height: int
    duration_sec: float | None = None


class MultiPlatformExporter:
    """final.mp4 → 플랫폼별 mp4 변환기"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def export(
        self,
        source_video: Path,
        platforms: list[Platform],
        output_dir: Path,
    ) -> list[ExportResult]:
        """주어진 플랫폼들로 일괄 변환. 실패한 플랫폼은 스킵하고 나머지 진행."""
        if not source_video.exists():
            raise FileNotFoundError(f"원본 영상이 없습니다: {source_video}")

        export_dir = output_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        # 원본 길이 추출 (트림 결정용)
        try:
            probe = ffmpeg.probe(str(source_video))
            src_duration = float(probe["format"]["duration"])
        except Exception:
            src_duration = None

        results: list[ExportResult] = []
        for platform in platforms:
            spec = PLATFORM_SPECS.get(platform)
            if spec is None:
                logger.warning("알 수 없는 플랫폼: %s — 스킵", platform)
                continue

            out_path = export_dir / f"{platform.value}.mp4"
            try:
                duration = self._render(source_video, out_path, spec, src_duration)
                results.append(ExportResult(
                    platform=platform,
                    output_path=out_path,
                    width=spec.width,
                    height=spec.height,
                    duration_sec=duration,
                ))
                logger.info(
                    "[Export] %s → %s (%dx%d, %.1fs)",
                    spec.label, out_path.name, spec.width, spec.height, duration or 0,
                )
            except Exception as e:
                logger.error("[Export] %s 실패: %s", platform.value, e)

        return results

    def _render(
        self,
        source: Path,
        output: Path,
        spec: PlatformSpec,
        src_duration: float | None,
    ) -> float:
        """단일 플랫폼 렌더링 — 비율 맞춤 (pad+crop) + 길이 제한"""
        target_duration = src_duration or 0
        if spec.max_duration_sec and target_duration > spec.max_duration_sec:
            target_duration = float(spec.max_duration_sec)

        stream = ffmpeg.input(str(source))

        # scale=W:H:force_original_aspect_ratio=decrease 후 pad 로 비율 맞춤
        # (원본 비율을 유지하면서 검은 배경으로 채움 — 콘텐츠 손실 방지)
        video = stream.video.filter(
            "scale", spec.width, spec.height,
            force_original_aspect_ratio="decrease",
        ).filter(
            "pad",
            spec.width,
            spec.height,
            "(ow-iw)/2",
            "(oh-ih)/2",
            color="black",
        ).filter("setsar", 1)

        out_kwargs = {
            "vcodec": "libx264",
            "pix_fmt": "yuv420p",
            "preset": "fast",
            "crf": 23,
            "movflags": "+faststart",
        }
        if target_duration > 0:
            out_kwargs["t"] = target_duration

        # 오디오는 있으면 그대로 카피 시도, 코덱 호환 안되면 aac 재인코딩
        try:
            audio = stream.audio
            output_stream = ffmpeg.output(
                video, audio, str(output),
                acodec="aac",
                audio_bitrate="128k",
                **out_kwargs,
            )
        except Exception:
            output_stream = ffmpeg.output(video, str(output), **out_kwargs)

        output_stream.run(quiet=True, overwrite_output=True, cmd=self.ffmpeg_path)
        return target_duration


def list_platforms() -> list[dict]:
    """API용 플랫폼 목록 직렬화"""
    return [
        {
            "id": p.value,
            "label": spec.label,
            "width": spec.width,
            "height": spec.height,
            "max_duration_sec": spec.max_duration_sec,
            "description": spec.description,
        }
        for p, spec in PLATFORM_SPECS.items()
    ]
