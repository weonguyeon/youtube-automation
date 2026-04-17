"""공통 데이터 스키마 - Pydantic 모델 정의

모든 패턴/포맷이 공유하는 JSON 구조.
Claude CLI가 생성한 대본 JSON을 검증하고, 파이프라인 전체에서 사용.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── 열거형 ──────────────────────────────────────────────


class VideoFormat(str, Enum):
    S8 = "S8"
    S15 = "S15"
    L3 = "L3"
    L5 = "L5"
    L10 = "L10"


class Pattern(str, Enum):
    A_DATA_VIZ = "A"
    B_TEXT_SHORTS = "B"
    C_SILENT_INFOGRAPHIC = "C"
    D_VECTOR_INFOGRAPHIC = "D"
    E_WHITEBOARD = "E"
    F_3D_BODY = "F"


class AspectRatio(str, Enum):
    PORTRAIT = "9:16"
    LANDSCAPE = "16:9"


class Transition(str, Enum):
    CUT = "cut"
    FADE = "fade"
    ZOOM_IN = "zoom_in"
    SLIDE_UP = "slide_up"
    SLIDE_LEFT = "slide_left"


class SceneType(str, Enum):
    HOOK = "hook"
    CONTENT = "content"
    WRAPUP = "wrapup"
    CTA = "cta"


class VoiceStyle(str, Enum):
    ENERGETIC = "energetic"
    CALM = "calm"
    DRAMATIC = "dramatic"
    CURIOUS = "curious"
    NARRATIVE = "narrative"


class BgmMood(str, Enum):
    EPIC = "epic"
    LOFI = "lofi"
    TENSE = "tense"
    UPBEAT = "upbeat"
    CALM = "calm"
    AMBIENT = "ambient"


class RenderEngine(str, Enum):
    """렌더링 엔진 선택 (웹사이트에서 사용자가 선택)"""
    MANIM = "manim"          # Python 코드 기반 애니메이션 (차트, 도형, 텍스트 모션)
    REMOTION = "remotion"    # React 컴포넌트 기반 인포그래픽 템플릿
    AI_PIPELINE = "ai_pipeline"  # AI 이미지 + TTS + 자동 조립 (MoneyPrinter 스타일)


class AssetType(str, Enum):
    GENERATED = "generated"
    STOCK = "stock"
    TEMPLATE = "template"
    CHART = "chart"


class ChartType(str, Enum):
    BAR_RACE = "bar_race"
    PIE = "pie"
    GAUGE = "gauge"
    LINE = "line"


class ColorPreset(str, Enum):
    MIDNIGHT_NAVY = "midnight_navy"
    OCEAN_BLUE = "ocean_blue"
    SUNSET_ORANGE = "sunset_orange"
    FOREST_GREEN = "forest_green"
    ROYAL_PURPLE = "royal_purple"
    CORAL_PINK = "coral_pink"
    GOLD_PREMIUM = "gold_premium"
    MONO_GRAY = "mono_gray"


# ── 포맷 규격 ────────────────────────────────────────────


FORMAT_SPECS: dict[VideoFormat, dict] = {
    VideoFormat.S8: {
        "duration_sec": 8,
        "aspect_ratio": AspectRatio.PORTRAIT,
        "resolution": (1080, 1920),
        "max_scenes": 3,
        "subtitle_font_size": 40,
        "subtitle_max_chars": 8,
        "subtitle_max_lines": 1,
        "subtitle_y_pct": 0.50,
        "transition_speed_ms": 0,
        "bgm_volume_with_voice": 0.3,
        "bgm_volume_no_voice": 0.7,
    },
    VideoFormat.S15: {
        "duration_sec": 15,
        "aspect_ratio": AspectRatio.PORTRAIT,
        "resolution": (1080, 1920),
        "max_scenes": 6,
        "subtitle_font_size": 32,
        "subtitle_max_chars": 12,
        "subtitle_max_lines": 2,
        "subtitle_y_pct": 0.60,
        "transition_speed_ms": 200,
        "bgm_volume_with_voice": 0.15,
        "bgm_volume_no_voice": 0.6,
    },
    VideoFormat.L3: {
        "duration_sec": 180,
        "aspect_ratio": AspectRatio.LANDSCAPE,
        "resolution": (1920, 1080),
        "max_scenes": 15,
        "subtitle_font_size": 42,
        "subtitle_max_chars": 20,
        "subtitle_max_lines": 2,
        "subtitle_y_pct": 0.85,
        "transition_speed_ms": 400,
        "bgm_volume_with_voice": 0.1,
        "bgm_volume_no_voice": 0.5,
    },
    VideoFormat.L5: {
        "duration_sec": 300,
        "aspect_ratio": AspectRatio.LANDSCAPE,
        "resolution": (1920, 1080),
        "max_scenes": 25,
        "subtitle_font_size": 42,
        "subtitle_max_chars": 20,
        "subtitle_max_lines": 2,
        "subtitle_y_pct": 0.85,
        "transition_speed_ms": 400,
        "bgm_volume_with_voice": 0.1,
        "bgm_volume_no_voice": 0.5,
    },
    VideoFormat.L10: {
        "duration_sec": 600,
        "aspect_ratio": AspectRatio.LANDSCAPE,
        "resolution": (1920, 1080),
        "max_scenes": 45,
        "subtitle_font_size": 42,
        "subtitle_max_chars": 20,
        "subtitle_max_lines": 2,
        "subtitle_y_pct": 0.85,
        "transition_speed_ms": 500,
        "bgm_volume_with_voice": 0.1,
        "bgm_volume_no_voice": 0.5,
    },
}


# ── 씬 모델 ──────────────────────────────────────────────


class StyleParams(BaseModel):
    color_preset: ColorPreset = ColorPreset.MIDNIGHT_NAVY
    font: str = "Pretendard Bold"
    layout: str = "center_text"


class Scene(BaseModel):
    scene_id: int
    scene_type: SceneType = SceneType.CONTENT
    duration_sec: float
    narration: Optional[str] = None
    subtitle: Optional[str] = None
    visual_prompt: Optional[str] = None
    transition: Transition = Transition.CUT
    asset_type: AssetType = AssetType.GENERATED
    style_params: Optional[StyleParams] = None
    visual_note: Optional[str] = None


# ── 오디오 설정 ────────────────────────────────────────────


class AudioConfig(BaseModel):
    voice_id: Optional[str] = None
    voice_style: VoiceStyle = VoiceStyle.NARRATIVE
    bgm_mood: BgmMood = BgmMood.UPBEAT
    bgm_volume: float = 0.15
    has_narration: bool = True


# ── 차트 데이터 (Pattern A 전용) ────────────────────────────


class ChartDataItem(BaseModel):
    label: str
    values: dict[str, float]


class ChartConfig(BaseModel):
    chart_type: ChartType = ChartType.BAR_RACE
    data_source: Optional[str] = None
    data: list[ChartDataItem] = Field(default_factory=list)


# ── 메타데이터 ──────────────────────────────────────────────


class VideoMetadata(BaseModel):
    title: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    scheduled_at: Optional[str] = None
    thumbnail_text: Optional[str] = None


# ── 최상위 스크립트 모델 ─────────────────────────────────────


class VideoScript(BaseModel):
    """Claude CLI가 생성하는 대본 JSON의 최상위 모델"""

    video_id: Optional[str] = None
    pattern: Pattern
    format: VideoFormat
    language: str = "ko"
    color_preset: ColorPreset = ColorPreset.MIDNIGHT_NAVY

    metadata: VideoMetadata
    scenes: list[Scene] = Field(default_factory=list)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    chart: Optional[ChartConfig] = None

    @property
    def aspect_ratio(self) -> AspectRatio:
        return FORMAT_SPECS[self.format]["aspect_ratio"]

    @property
    def resolution(self) -> tuple[int, int]:
        return FORMAT_SPECS[self.format]["resolution"]

    @property
    def target_duration(self) -> int:
        return FORMAT_SPECS[self.format]["duration_sec"]

    @property
    def total_scene_duration(self) -> float:
        return sum(s.duration_sec for s in self.scenes)
