"""Remotion 렌더링 엔진

React 컴포넌트 기반 인포그래픽 영상 대량 렌더링.
JSON 데이터를 Remotion 프로젝트에 전달하여 영상 생성.

웹사이트 배포 시 가장 자연스럽게 통합되는 엔진.
디자인 자유도가 가장 높음.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from pipeline.colors import get_theme
from pipeline.config import PROJECT_ROOT
from pipeline.schema import FORMAT_SPECS, VideoScript
from pipeline.visual.base_renderer import BaseRenderer, VisualResult

logger = logging.getLogger(__name__)

REMOTION_PROJECT_DIR = PROJECT_ROOT / "remotion"


class RemotionRenderer(BaseRenderer):
    """Remotion (React) 기반 인포그래픽 렌더러"""

    def render(self, script: VideoScript, output_dir: Path) -> VisualResult:
        result = VisualResult()
        theme = get_theme(script.color_preset)
        spec = FORMAT_SPECS[script.format]

        # 대본 JSON을 Remotion input props로 변환
        props = self._build_remotion_props(script, theme, spec)
        props_path = output_dir / "remotion_props.json"
        props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")

        # Remotion 프로젝트가 있으면 렌더링, 없으면 폴백
        if self._is_remotion_ready():
            video_path = self._render_remotion(props_path, output_dir, spec)
        else:
            logger.warning("Remotion 프로젝트 미설정 — MoviePy 폴백 렌더링")
            video_path = self._fallback_render(script, theme, spec, output_dir)

        result.video_clip_path = video_path
        logger.info("Remotion 렌더링 완료: %s", video_path)
        return result

    def _build_remotion_props(self, script: VideoScript, theme, spec: dict) -> dict:
        """Remotion 컴포넌트에 전달할 props JSON"""
        w, h = spec["resolution"]
        fps = 30

        return {
            "width": w,
            "height": h,
            "fps": fps,
            "durationInFrames": script.target_duration * fps,
            "theme": {
                "primary": theme.primary,
                "secondary": theme.secondary,
                "accent": theme.accent,
                "background": theme.background,
                "text": theme.text,
                "textHighlight": theme.text_highlight,
            },
            "scenes": [
                {
                    "id": s.scene_id,
                    "type": s.scene_type.value,
                    "durationInFrames": int(s.duration_sec * fps),
                    "subtitle": (s.subtitle or "").replace("**", ""),
                    "narration": s.narration or "",
                    "visualPrompt": s.visual_prompt or "",
                    "transition": s.transition.value,
                }
                for s in script.scenes
            ],
            "metadata": {
                "title": script.metadata.title,
                "description": script.metadata.description,
            },
        }

    def _is_remotion_ready(self) -> bool:
        """Remotion 프로젝트가 설치되어 있는지 확인"""
        package_json = REMOTION_PROJECT_DIR / "package.json"
        return package_json.exists()

    def _render_remotion(self, props_path: Path, output_dir: Path, spec: dict) -> Path:
        """Remotion CLI로 영상 렌더링"""
        output_path = output_dir / "remotion_output.mp4"

        cmd = [
            "npx", "remotion", "render",
            "src/index.ts",
            "InfographicVideo",
            str(output_path),
            "--props", str(props_path),
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            cwd=str(REMOTION_PROJECT_DIR),
        )

        if result.returncode != 0:
            raise RuntimeError(f"Remotion 렌더링 실패: {result.stderr[:500]}")

        return output_path

    def _fallback_render(self, script: VideoScript, theme, spec: dict, output_dir: Path) -> Path:
        """Remotion 미설치 시 MoviePy로 유사한 인포그래픽 영상 생성"""
        from PIL import Image, ImageDraw, ImageFont

        output_path = output_dir / "remotion_fallback.mp4"
        w, h = spec["resolution"]
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)

        frame_paths = []
        for scene in script.scenes:
            frame_path = frames_dir / f"scene_{scene.scene_id:03d}.png"
            self._render_infographic_frame(scene, theme, w, h, frame_path)
            frame_paths.append((frame_path, scene.duration_sec))

        # FFmpeg concat으로 영상 조립
        self._concat_frames(frame_paths, output_path, w, h, theme.background)

        return output_path

    def _render_infographic_frame(self, scene, theme, w: int, h: int, output_path: Path):
        """단일 인포그래픽 프레임 렌더링 (PIL)"""
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (w, h), theme.background)
        draw = ImageDraw.Draw(img)

        subtitle = (scene.subtitle or "").replace("**", "")

        # 상단 액센트 바
        draw.rectangle([0, 0, w, 6], fill=theme.accent)

        # 중앙 컨텐츠 영역
        if scene.scene_type.value == "hook":
            # Hook: 큰 텍스트 + 원형 강조
            cx, cy = w // 2, h // 2
            r = min(w, h) // 4
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=theme.accent, width=4)
        elif scene.scene_type.value == "content":
            # Content: 카드 스타일
            margin = 60
            card_y = h // 3
            draw.rounded_rectangle(
                [margin, card_y, w - margin, card_y + h // 3],
                radius=20, fill=theme.secondary, outline=theme.accent, width=2,
            )
        elif scene.scene_type.value == "wrapup":
            # Wrapup: 하단 강조
            draw.rectangle([0, h - 200, w, h], fill=theme.primary)

        # 하단 액센트 바
        draw.rectangle([0, h - 6, w, h], fill=theme.accent)

        img.save(output_path, "PNG")

    def _concat_frames(self, frame_paths: list, output_path: Path, w: int, h: int, bg: str):
        """프레임 시퀀스를 영상으로 합치기"""
        import ffmpeg

        concat_file = output_path.parent / "concat.txt"
        lines = []
        for path, duration in frame_paths:
            lines.append(f"file '{path}'")
            lines.append(f"duration {duration}")
        lines.append(f"file '{frame_paths[-1][0]}'")
        concat_file.write_text("\n".join(lines), encoding="utf-8")

        (
            ffmpeg
            .input(str(concat_file), f="concat", safe=0)
            .filter("scale", w, h)
            .output(
                str(output_path),
                vcodec="libx264", pix_fmt="yuv420p",
                preset="fast",
            )
            .overwrite_output()
            .run(quiet=True)
        )
