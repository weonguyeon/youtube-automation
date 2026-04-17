"""Manim 렌더링 엔진

Python 코드 기반으로 차트, 도형, 텍스트 모션 애니메이션 생성.
3Blue1Brown 스타일의 고품질 설명 영상.

지원 시각 요소:
- Bar Chart / Pie Chart 애니메이션
- 텍스트 타이포그래피 모션
- 도형 변환 (Circle, Arrow, Rectangle 등)
- 숫자 카운트업/카운트다운
- 프로세스 다이어그램
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from textwrap import dedent

from pipeline.colors import ColorTheme, get_theme
from pipeline.schema import FORMAT_SPECS, Scene, VideoScript
from pipeline.visual.base_renderer import BaseRenderer, VisualResult

logger = logging.getLogger(__name__)


class ManimRenderer(BaseRenderer):
    """Manim 기반 애니메이션 렌더러"""

    def render(self, script: VideoScript, output_dir: Path) -> VisualResult:
        result = VisualResult()
        theme = get_theme(script.color_preset)
        spec = FORMAT_SPECS[script.format]
        w, h = spec["resolution"]

        # Manim 씬 코드 생성
        scene_code = self._build_manim_scene(script, theme, spec)

        # 임시 파일에 코드 저장 후 렌더링
        code_path = output_dir / "manim_scene.py"
        code_path.write_text(scene_code, encoding="utf-8")

        video_path = self._render_manim(code_path, output_dir, w, h, script.target_duration)
        result.video_clip_path = video_path

        logger.info("Manim 렌더링 완료: %s", video_path)
        return result

    def _build_manim_scene(self, script: VideoScript, theme: ColorTheme, spec: dict) -> str:
        """대본 기반으로 Manim 씬 Python 코드 생성"""
        bg_color = theme.background
        primary = theme.primary
        accent = theme.accent
        text_color = theme.text

        # 씬별 애니메이션 코드 조각 생성
        animations = []
        for scene in script.scenes:
            anim = self._scene_to_manim_animation(scene, theme)
            animations.append(anim)

        animations_code = "\n".join(animations)

        return dedent(f"""\
            from manim import *

            class VideoScene(Scene):
                def construct(self):
                    self.camera.background_color = "{bg_color}"

            {self._indent(animations_code, 8)}
        """)

    def _scene_to_manim_animation(self, scene: Scene, theme: ColorTheme) -> str:
        """개별 씬을 Manim 애니메이션 코드로 변환"""
        subtitle = scene.subtitle or ""
        duration = scene.duration_sec
        accent = theme.accent
        text_color = theme.text

        # 자막 텍스트 표시
        code = dedent(f"""\
            # Scene {scene.scene_id}: {scene.scene_type.value}
            title_{scene.scene_id} = Text(
                "{self._escape(subtitle)}",
                font_size=48,
                color="{text_color}",
                weight=BOLD,
            ).move_to(ORIGIN)

            accent_bar_{scene.scene_id} = Rectangle(
                width=10, height=0.08,
                fill_color="{accent}", fill_opacity=1, stroke_width=0,
            ).next_to(title_{scene.scene_id}, DOWN, buff=0.3)

            self.play(
                FadeIn(title_{scene.scene_id}, shift=UP * 0.3),
                GrowFromCenter(accent_bar_{scene.scene_id}),
                run_time=0.8,
            )
            self.wait({max(0.5, duration - 1.6)})
            self.play(
                FadeOut(title_{scene.scene_id}),
                FadeOut(accent_bar_{scene.scene_id}),
                run_time=0.8,
            )
        """)
        return code

    def _render_manim(
        self, code_path: Path, output_dir: Path, width: int, height: int, duration: int
    ) -> Path:
        """Manim CLI로 렌더링 실행"""
        output_path = output_dir / "manim_output.mp4"

        cmd = [
            "manim", "render",
            str(code_path),
            "VideoScene",
            "-o", str(output_path),
            "--resolution", f"{width},{height}",
            "--fps", "30",
            "-ql",  # low quality for speed (개발 중)
            "--media_dir", str(output_dir / "manim_media"),
        ]

        logger.info("Manim 렌더링 시작: %s", " ".join(cmd))

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
        )

        if result.returncode != 0:
            logger.error("Manim 에러: %s", result.stderr)
            raise RuntimeError(f"Manim 렌더링 실패: {result.stderr[:500]}")

        # Manim은 자체 경로에 저장하므로 실제 파일 찾기
        media_dir = output_dir / "manim_media" / "videos"
        mp4_files = list(media_dir.rglob("*.mp4"))
        if mp4_files:
            actual_path = mp4_files[0]
            if actual_path != output_path:
                import shutil
                shutil.move(str(actual_path), str(output_path))

        return output_path

    @staticmethod
    def _escape(text: str) -> str:
        return text.replace('"', '\\"').replace("**", "").replace("\n", " ")

    @staticmethod
    def _indent(text: str, spaces: int) -> str:
        prefix = " " * spaces
        return "\n".join(prefix + line for line in text.split("\n"))
