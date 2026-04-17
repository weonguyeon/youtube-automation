"""Pattern C: 무음 인포그래픽 슬라이드 렌더러

내레이션 없이 텍스트/숫자/차트만으로 정보 전달.
글로벌 타겟 가능하도록 숫자/기호 중심 디자인.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pipeline.colors import ColorTheme, get_theme
from pipeline.schema import FORMAT_SPECS, Scene, SceneType, VideoScript
from pipeline.visual.base_renderer import BaseRenderer, VisualResult

logger = logging.getLogger(__name__)


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for fp in [
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/NanumGothicBold.ttf",
    ]:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class SilentInfographicRenderer(BaseRenderer):
    """무음 인포그래픽 슬라이드 렌더러"""

    def render(self, script: VideoScript, output_dir: Path) -> VisualResult:
        result = VisualResult()
        theme = get_theme(script.color_preset)
        spec = FORMAT_SPECS[script.format]
        w, h = spec["resolution"]

        for scene in script.scenes:
            slide_path = output_dir / f"slide_{scene.scene_id:03d}.png"
            self._render_slide(scene, theme, w, h, slide_path)
            result.asset_paths.append(slide_path)

        logger.info("무음 인포그래픽 슬라이드 %d장 생성", len(result.asset_paths))
        return result

    def _render_slide(self, scene: Scene, theme: ColorTheme, w: int, h: int, output_path: Path):
        """씬 타입별 슬라이드 렌더링"""
        img = Image.new("RGB", (w, h), theme.background)
        draw = ImageDraw.Draw(img)

        # 배경 그라데이션
        bg_rgb = _hex_to_rgb(theme.background)
        sec_rgb = _hex_to_rgb(theme.secondary)
        for y in range(h):
            ratio = y / h
            r = int(bg_rgb[0] + (sec_rgb[0] - bg_rgb[0]) * ratio * 0.25)
            g = int(bg_rgb[1] + (sec_rgb[1] - bg_rgb[1]) * ratio * 0.25)
            b = int(bg_rgb[2] + (sec_rgb[2] - bg_rgb[2]) * ratio * 0.25)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        subtitle = (scene.subtitle or "").replace("**", "")
        visual_note = scene.visual_note or ""
        chart_type = self._parse_chart_type(visual_note)

        if scene.scene_type == SceneType.HOOK:
            self._draw_hook(draw, subtitle, theme, w, h)
        elif scene.scene_type == SceneType.WRAPUP:
            self._draw_wrapup(draw, subtitle, theme, w, h)
        else:
            if chart_type == "bar":
                self._draw_bar_chart(draw, subtitle, theme, w, h)
            elif chart_type == "pie":
                self._draw_pie_chart(draw, subtitle, theme, w, h)
            elif chart_type == "number":
                self._draw_number_highlight(draw, subtitle, theme, w, h)
            else:
                self._draw_info_card(draw, subtitle, theme, w, h, scene.scene_id)

        # 상단/하단 액센트
        draw.rectangle([0, 0, w, 5], fill=theme.accent)
        draw.rectangle([0, h - 5, w, h], fill=theme.accent)

        img.save(output_path, "PNG", quality=95)

    def _parse_chart_type(self, visual_note: str) -> str:
        note_lower = visual_note.lower()
        if "bar" in note_lower:
            return "bar"
        if "pie" in note_lower:
            return "pie"
        if "number" in note_lower or "gauge" in note_lower:
            return "number"
        return "card"

    def _draw_hook(self, draw: ImageDraw.Draw, subtitle: str, theme: ColorTheme, w: int, h: int):
        """Hook: 큰 숫자/텍스트 중심"""
        font_big = _load_font(96)
        font_small = _load_font(28)
        cx = w // 2
        cy = h // 2 - 40

        # 중앙 큰 원
        r = 220
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=theme.accent, width=6)
        draw.ellipse([cx - r + 15, cy - r + 15, cx + r - 15, cy + r - 15], outline=theme.primary, width=2)
        self._draw_centered(draw, subtitle, font_big, theme.text, cx, cy, r * 2 - 60)

        # 상단 뱃지
        draw.rounded_rectangle([cx - 80, 180, cx + 80, 216], radius=18, fill=theme.accent)
        bbox = draw.textbbox((0, 0), "INFO", font=font_small)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, 184), "INFO", fill=theme.background, font=font_small)

    def _draw_info_card(self, draw: ImageDraw.Draw, subtitle: str, theme: ColorTheme, w: int, h: int, scene_id: int):
        """Content: 정보 카드"""
        font_title = _load_font(52)
        font_small = _load_font(24)
        margin = 60
        cx = w // 2

        # 씬 번호
        draw.rounded_rectangle([margin, 120, margin + 90, 164], radius=12, fill=theme.accent)
        draw.text((margin + 14, 126), f"#{scene_id:02d}", fill=theme.background, font=font_small)

        # 구분선
        draw.rectangle([margin, 184, w - margin, 188], fill=theme.accent)

        # 메인 카드
        card_top = 230
        card_bottom = h - 280
        draw.rounded_rectangle(
            [margin, card_top, w - margin, card_bottom],
            radius=24, fill=theme.secondary, outline=theme.accent, width=2,
        )

        # 카드 내부 텍스트
        self._draw_centered(draw, subtitle, font_title, theme.text, cx, (card_top + card_bottom) // 2, w - margin * 2 - 60)

        # 장식: 하단 점선
        dot_y = card_bottom - 40
        for x in range(margin + 30, w - margin - 30, 20):
            draw.ellipse([x, dot_y, x + 6, dot_y + 6], fill=theme.accent)

    def _draw_bar_chart(self, draw: ImageDraw.Draw, subtitle: str, theme: ColorTheme, w: int, h: int):
        """가로 바 차트"""
        font_title = _load_font(44)
        font_label = _load_font(28)
        font_value = _load_font(24)
        margin = 80
        cx = w // 2

        # 제목
        self._draw_centered(draw, subtitle, font_title, theme.text, cx, 260, w - margin * 2)

        # 구분선
        draw.rectangle([margin, 320, w - margin, 324], fill=theme.accent)

        # 바 차트 (5개 항목)
        labels = ["Category A", "Category B", "Category C", "Category D", "Category E"]
        values = [92, 78, 65, 51, 38]
        bar_start_y = 380
        bar_h = 50
        bar_gap = 30
        max_bar_w = w - margin * 2 - 160

        chart_colors = _hex_to_rgb(theme.accent), _hex_to_rgb(theme.primary)
        for i, (label, val) in enumerate(zip(labels, values)):
            y = bar_start_y + i * (bar_h + bar_gap)
            draw.text((margin, y + 10), label, fill=theme.text, font=font_label)
            # 바 배경
            bar_x = margin + 160
            draw.rounded_rectangle([bar_x, y + 6, bar_x + max_bar_w, y + bar_h - 6], radius=8, fill=theme.background)
            # 바 값
            bw = int(max_bar_w * val / 100)
            color = theme.accent if i % 2 == 0 else theme.primary
            draw.rounded_rectangle([bar_x, y + 6, bar_x + bw, y + bar_h - 6], radius=8, fill=color)
            draw.text((bar_x + bw + 10, y + 10), f"{val}%", fill=theme.text, font=font_value)

    def _draw_pie_chart(self, draw: ImageDraw.Draw, subtitle: str, theme: ColorTheme, w: int, h: int):
        """파이 차트 (근사치)"""
        font_title = _load_font(44)
        font_label = _load_font(28)
        cx = w // 2

        # 제목
        self._draw_centered(draw, subtitle, font_title, theme.text, cx, 260, w - 160)

        # 파이 차트
        pie_cx, pie_cy = cx, h // 2 + 40
        pie_r = 200
        slices = [
            (35, theme.accent),
            (25, theme.primary),
            (20, theme.secondary),
            (15, theme.text_highlight),
            (5, theme.background),
        ]

        start_angle = -90
        for pct, color in slices:
            sweep = pct / 100 * 360
            draw.pieslice(
                [pie_cx - pie_r, pie_cy - pie_r, pie_cx + pie_r, pie_cy + pie_r],
                start=start_angle, end=start_angle + sweep,
                fill=color, outline=theme.background, width=2,
            )
            start_angle += sweep

        # 중앙 원 (도넛 효과)
        inner_r = 80
        draw.ellipse(
            [pie_cx - inner_r, pie_cy - inner_r, pie_cx + inner_r, pie_cy + inner_r],
            fill=theme.background,
        )
        self._draw_centered(draw, "100%", _load_font(36), theme.text, pie_cx, pie_cy, inner_r * 2 - 20)

        # 범례
        legend_y = pie_cy + pie_r + 60
        legend_labels = ["35%", "25%", "20%", "15%", "5%"]
        for i, ((pct, color), lbl) in enumerate(zip(slices[:4], legend_labels)):
            x = cx - 180 + (i % 2) * 200
            y = legend_y + (i // 2) * 50
            draw.rectangle([x, y, x + 24, y + 24], fill=color)
            draw.text((x + 34, y - 2), lbl, fill=theme.text, font=font_label)

    def _draw_number_highlight(self, draw: ImageDraw.Draw, subtitle: str, theme: ColorTheme, w: int, h: int):
        """큰 숫자 강조"""
        font_number = _load_font(140)
        font_label = _load_font(36)
        cx = w // 2
        cy = h // 2 - 60

        # 배경 사각형
        draw.rounded_rectangle([80, cy - 180, w - 80, cy + 180], radius=30, fill=theme.secondary, outline=theme.accent, width=3)

        # 숫자 추출 (자막에서)
        import re
        numbers = re.findall(r"[\d,.]+[%]?", subtitle)
        number_text = numbers[0] if numbers else subtitle[:6]
        rest_text = subtitle.replace(number_text, "").strip() if numbers else ""

        # 큰 숫자
        self._draw_centered(draw, number_text, font_number, theme.accent, cx, cy - 30, w - 200)
        # 설명 텍스트
        if rest_text:
            self._draw_centered(draw, rest_text, font_label, theme.text, cx, cy + 100, w - 200)

    def _draw_wrapup(self, draw: ImageDraw.Draw, subtitle: str, theme: ColorTheme, w: int, h: int):
        """Wrapup: 요약"""
        font_title = _load_font(52)
        font_small = _load_font(28)
        cx = w // 2

        # 상단 액센트 바
        draw.rectangle([0, 240, w, 248], fill=theme.accent)

        # 요약 카드
        card_top = h // 3
        draw.rounded_rectangle(
            [80, card_top, w - 80, card_top + 320],
            radius=30, fill=theme.secondary, outline=theme.accent, width=3,
        )
        self._draw_centered(draw, subtitle, font_title, theme.text, cx, card_top + 160, w - 200)

        # 하단 CTA
        draw.rectangle([0, h - 200, w, h], fill=theme.primary)
        draw.rectangle([0, h - 206, w, h - 200], fill=theme.accent)
        btn_w = 360
        draw.rounded_rectangle([cx - btn_w // 2, h - 150, cx + btn_w // 2, h - 88], radius=32, fill=theme.accent)
        bbox = draw.textbbox((0, 0), "SUBSCRIBE", font=font_small)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, h - 144), "SUBSCRIBE", fill=theme.background, font=font_small)

    def _draw_centered(self, draw: ImageDraw.Draw, text: str, font, color: str, cx: int, cy: int, max_width: int):
        if not text:
            return
        lines = []
        current = ""
        for char in text:
            test = current + char
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width and current:
                lines.append(current)
                current = char
            else:
                current = test
        if current:
            lines.append(current)

        line_h = draw.textbbox((0, 0), "가Ag", font=font)[3] + 8
        total_h = len(lines) * line_h
        y = cy - total_h // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((cx - tw // 2, y), line, fill=color, font=font)
            y += line_h
