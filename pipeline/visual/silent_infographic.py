"""Pattern C: 무음 인포그래픽 렌더러

인포그래픽 카드 슬라이드 → PNG 시퀀스 생성
내레이션 없이 텍스트/차트/아이콘만으로 정보 전달
"""

from __future__ import annotations

import logging
from pathlib import Path

from pipeline.colors import get_theme
from pipeline.schema import VideoScript
from pipeline.visual.base_renderer import BaseRenderer, VisualResult

logger = logging.getLogger(__name__)


class SilentInfographicRenderer(BaseRenderer):
    """무음 인포그래픽 슬라이드 렌더러"""

    def render(self, script: VideoScript, output_dir: Path) -> VisualResult:
        result = VisualResult()
        theme = get_theme(script.color_preset)

        for scene in script.scenes:
            slide_path = self._render_slide(scene, theme, output_dir)
            result.asset_paths.append(slide_path)

        logger.info("무음 인포그래픽 슬라이드 %d장 생성", len(result.asset_paths))
        return result

    def _render_slide(self, scene, theme, output_dir: Path) -> Path:
        """단일 슬라이드 렌더링"""
        from PIL import Image, ImageDraw

        output_path = output_dir / f"slide_{scene.scene_id:03d}.png"
        w, h = 1080, 1920

        img = Image.new("RGB", (w, h), theme.background)
        draw = ImageDraw.Draw(img)

        # 상단 제목 영역
        draw.rectangle([0, 0, w, 200], fill=theme.primary)

        # 중앙 데이터 영역
        draw.rectangle([80, 300, w - 80, h - 400], fill=theme.secondary, outline=theme.accent, width=2)

        # 하단 강조 바
        draw.rectangle([0, h - 120, w, h], fill=theme.accent)

        img.save(output_path, "PNG")
        return output_path
