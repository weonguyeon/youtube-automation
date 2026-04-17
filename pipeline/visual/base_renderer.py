"""시각 에셋 렌더러 베이스 클래스 + 팩토리

각 Pattern별 렌더러가 이 인터페이스를 구현.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.schema import Pattern, RenderEngine, VideoScript


@dataclass
class VisualResult:
    """시각 에셋 생성 결과"""
    asset_paths: list[Path] = field(default_factory=list)
    video_clip_path: Path | None = None  # 차트 등 이미 영상인 경우


class BaseRenderer(abc.ABC):
    """시각 에셋 렌더러 인터페이스"""

    @abc.abstractmethod
    def render(self, script: VideoScript, output_dir: Path) -> VisualResult:
        ...


def get_renderer(pattern: Pattern) -> BaseRenderer:
    """패턴에 맞는 렌더러 반환 (Pattern 기반 — 기존 호환)"""
    if pattern == Pattern.A_DATA_VIZ:
        from pipeline.visual.data_viz import DataVizRenderer
        return DataVizRenderer()
    elif pattern == Pattern.B_TEXT_SHORTS:
        from pipeline.visual.text_shorts import TextShortsRenderer
        return TextShortsRenderer()
    elif pattern == Pattern.C_SILENT_INFOGRAPHIC:
        from pipeline.visual.silent_infographic import SilentInfographicRenderer
        return SilentInfographicRenderer()
    elif pattern == Pattern.D_VECTOR_INFOGRAPHIC:
        from pipeline.visual.vector_infographic import VectorInfographicRenderer
        return VectorInfographicRenderer()
    elif pattern == Pattern.E_WHITEBOARD:
        from pipeline.visual.whiteboard import WhiteboardRenderer
        return WhiteboardRenderer()
    else:
        raise NotImplementedError(f"Pattern {pattern.value} 렌더러 미구현")


def get_engine_renderer(engine: RenderEngine) -> BaseRenderer:
    """렌더링 엔진에 맞는 렌더러 반환 (Engine 기반)"""
    if engine == RenderEngine.MANIM:
        from pipeline.visual.engine_manim import ManimRenderer
        return ManimRenderer()
    elif engine == RenderEngine.REMOTION:
        from pipeline.visual.engine_remotion import RemotionRenderer
        return RemotionRenderer()
    elif engine == RenderEngine.AI_PIPELINE:
        from pipeline.visual.engine_ai_pipeline import AIPipelineRenderer
        return AIPipelineRenderer()
    else:
        raise NotImplementedError(f"Engine {engine.value} 렌더러 미구현")
