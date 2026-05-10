"""썸네일 자동 생성

YouTube 업로드용 1280x720 썸네일을 자동 생성.
영상 첫 씬 이미지를 기반으로 텍스트 오버레이 추가.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pipeline.colors import ColorTheme, get_theme
from pipeline.schema import VideoScript

logger = logging.getLogger(__name__)

THUMB_W = 1280
THUMB_H = 720


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    font_candidates = [
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/NanumGothicBold.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fp in font_candidates:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


class ThumbnailGenerator:
    """YouTube 썸네일 자동 생성"""

    def generate(
        self,
        script: VideoScript,
        scene_images: list[Path],
        output_dir: Path,
    ) -> Path:
        output_path = output_dir / "thumbnail.png"
        theme = get_theme(script.color_preset)
        text = script.metadata.thumbnail_text or script.metadata.title

        # 베이스 이미지: 첫 씬 이미지 사용
        if scene_images and scene_images[0].exists():
            base = Image.open(scene_images[0])
            base = base.resize((THUMB_W, THUMB_H), Image.LANCZOS)
        else:
            base = Image.new("RGB", (THUMB_W, THUMB_H), theme.background)

        draw = ImageDraw.Draw(base)

        # 하단 그라데이션 오버레이 (텍스트 가독성)
        bg_rgb = _hex_to_rgb(theme.background)
        for y in range(THUMB_H // 2, THUMB_H):
            alpha = int(220 * ((y - THUMB_H // 2) / (THUMB_H // 2)))
            draw.line(
                [(0, y), (THUMB_W, y)],
                fill=(bg_rgb[0], bg_rgb[1], bg_rgb[2], alpha),
            )

        # 메인 텍스트
        font_main = _load_font(72)
        self._draw_text_with_shadow(
            draw, text, font_main, theme, THUMB_W // 2, THUMB_H - 120, THUMB_W - 120
        )

        # 상단 액센트 바
        draw.rectangle([0, 0, THUMB_W, 8], fill=theme.accent)
        # 하단 액센트 바
        draw.rectangle([0, THUMB_H - 8, THUMB_W, THUMB_H], fill=theme.accent)

        base.save(output_path, "PNG", quality=95)
        logger.info("썸네일 생성: %s (%s)", output_path.name, text[:20])
        return output_path

    def _draw_text_with_shadow(
        self,
        draw: ImageDraw.Draw,
        text: str,
        font: ImageFont.FreeTypeFont,
        theme: ColorTheme,
        cx: int,
        cy: int,
        max_width: int,
    ):
        """그림자 + 중앙 정렬 텍스트"""
        lines = self._wrap_text(draw, text, font, max_width)
        line_height = draw.textbbox((0, 0), "가Ag", font=font)[3] + 10
        total_h = len(lines) * line_height
        y = cy - total_h // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = cx - tw // 2

            # 그림자
            draw.text((x + 3, y + 3), line, fill="#000000", font=font)
            # 메인 텍스트
            draw.text((x, y), line, fill=theme.text, font=font)
            y += line_height

    @staticmethod
    def _wrap_text(
        draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont, max_width: int
    ) -> list[str]:
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        return lines
