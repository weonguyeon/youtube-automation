"""Pattern E: 화이트보드 스타일 렌더러

흰 배경에 손글씨/스케치 느낌의 인포그래픽.
마커 펜 느낌의 텍스트, 러프한 도형, 화살표.
교육/설명 콘텐츠에 적합.
"""

from __future__ import annotations

import logging
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pipeline.colors import ColorTheme, get_theme
from pipeline.schema import FORMAT_SPECS, Scene, SceneType, VideoScript
from pipeline.visual.base_renderer import BaseRenderer, VisualResult

logger = logging.getLogger(__name__)

# 화이트보드 컬러 (브랜드 컬러 대신 마커 펜 색상)
MARKER_COLORS = {
    "black": "#2d2d2d",
    "red": "#e63946",
    "blue": "#1d3557",
    "green": "#2d6a4f",
    "orange": "#e76f51",
    "purple": "#6a4c93",
}


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


def _draw_rough_line(draw: ImageDraw.Draw, x1, y1, x2, y2, color, width=3):
    """러프한 선 (약간 흔들림 효과)"""
    points = [(x1, y1)]
    steps = max(5, int(math.dist((x1, y1), (x2, y2)) / 20))
    for i in range(1, steps):
        t = i / steps
        x = x1 + (x2 - x1) * t + random.uniform(-2, 2)
        y = y1 + (y2 - y1) * t + random.uniform(-2, 2)
        points.append((x, y))
    points.append((x2, y2))
    draw.line(points, fill=color, width=width)


def _draw_rough_rect(draw: ImageDraw.Draw, x1, y1, x2, y2, color, width=3):
    """러프한 사각형"""
    _draw_rough_line(draw, x1, y1, x2, y1, color, width)
    _draw_rough_line(draw, x2, y1, x2, y2, color, width)
    _draw_rough_line(draw, x2, y2, x1, y2, color, width)
    _draw_rough_line(draw, x1, y2, x1, y1, color, width)


def _draw_rough_circle(draw: ImageDraw.Draw, cx, cy, r, color, width=3):
    """러프한 원"""
    points = []
    for deg in range(0, 365, 5):
        rad = math.radians(deg)
        jitter_r = r + random.uniform(-3, 3)
        x = cx + jitter_r * math.cos(rad)
        y = cy + jitter_r * math.sin(rad)
        points.append((x, y))
    draw.line(points, fill=color, width=width)


def _draw_arrow(draw: ImageDraw.Draw, x1, y1, x2, y2, color, width=3):
    """화살표"""
    _draw_rough_line(draw, x1, y1, x2, y2, color, width)
    angle = math.atan2(y2 - y1, x2 - x1)
    head_len = 20
    for da in [math.pi * 0.8, -math.pi * 0.8]:
        hx = x2 - head_len * math.cos(angle + da)
        hy = y2 - head_len * math.sin(angle + da)
        _draw_rough_line(draw, x2, y2, hx, hy, color, width)


def _draw_centered(draw: ImageDraw.Draw, text: str, font, color, cx: int, cy: int, max_width: int):
    if not text:
        return
    lines, current = [], ""
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
    y = cy - len(lines) * line_h // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, y), line, fill=color, font=font)
        y += line_h


class WhiteboardRenderer(BaseRenderer):
    """화이트보드 스타일 렌더러"""

    def render(self, script: VideoScript, output_dir: Path) -> VisualResult:
        result = VisualResult()
        spec = FORMAT_SPECS[script.format]
        w, h = spec["resolution"]
        theme = get_theme(script.color_preset)

        total = len(script.scenes)
        for i, scene in enumerate(script.scenes):
            img_path = output_dir / f"wb_{scene.scene_id:03d}.png"
            self._render_scene(scene, theme, w, h, img_path, i, total)
            result.asset_paths.append(img_path)

        logger.info("화이트보드 %d개 씬 생성", len(result.asset_paths))
        return result

    def _render_scene(
        self, scene: Scene, theme: ColorTheme, w: int, h: int,
        output_path: Path, index: int, total: int,
    ):
        # 화이트보드 배경 (약간 크림색)
        img = Image.new("RGB", (w, h), "#faf8f5")
        draw = ImageDraw.Draw(img)

        # 격자 배경 (노트 느낌)
        grid_color = "#e8e4df"
        for gy in range(0, h, 40):
            draw.line([(0, gy), (w, gy)], fill=grid_color, width=1)

        subtitle = (scene.subtitle or "").replace("**", "")
        marker = MARKER_COLORS["black"]
        accent = MARKER_COLORS["red"]
        blue = MARKER_COLORS["blue"]

        if scene.scene_type == SceneType.HOOK:
            self._draw_hook(draw, subtitle, w, h, accent)
        elif scene.scene_type == SceneType.WRAPUP:
            self._draw_wrapup(draw, subtitle, w, h, marker, accent)
        elif scene.scene_type == SceneType.CTA:
            self._draw_cta(draw, subtitle, w, h, accent)
        else:
            layout = index % 3
            if layout == 0:
                self._draw_mindmap(draw, subtitle, w, h, marker, accent, blue, index)
            elif layout == 1:
                self._draw_list(draw, subtitle, w, h, marker, accent, index)
            else:
                self._draw_diagram(draw, subtitle, w, h, marker, accent, blue, index)

        # 페이지 번호
        font_small = _load_font(20)
        page_text = f"{index + 1}/{total}"
        draw.text((w - 80, h - 40), page_text, fill="#999999", font=font_small)

        img.save(output_path, "PNG", quality=95)

    def _draw_hook(self, draw, subtitle, w, h, accent):
        """Hook: 큰 밑줄 텍스트"""
        font_big = _load_font(72)
        font_small = _load_font(28)
        cx, cy = w // 2, h // 2 - 40

        _draw_centered(draw, subtitle, font_big, MARKER_COLORS["black"], cx, cy, w - 160)

        # 밑줄 강조
        bbox = draw.textbbox((0, 0), subtitle[:10], font=font_big)
        tw = min(bbox[2] - bbox[0], w - 200)
        _draw_rough_line(draw, cx - tw // 2, cy + 50, cx + tw // 2, cy + 50, accent, 4)
        _draw_rough_line(draw, cx - tw // 2, cy + 58, cx + tw // 2, cy + 58, accent, 2)

        # 상단 별표 장식
        for i in range(3):
            sx = cx - 40 + i * 40
            draw.text((sx, 180), "*", fill=accent, font=font_small)

    def _draw_mindmap(self, draw, subtitle, w, h, marker, accent, blue, index):
        """마인드맵 레이아웃"""
        font_title = _load_font(44)
        font_node = _load_font(24)
        cx, cy = w // 2, h // 2

        # 중앙 원
        _draw_rough_circle(draw, cx, cy, 80, accent, 4)
        _draw_centered(draw, subtitle[:12], font_title, marker, cx, cy, 140)

        # 주변 노드 (6개)
        nodes = 6
        node_r = min(w, h) // 4
        for i in range(nodes):
            angle = math.radians(-90 + i * (360 / nodes))
            nx = cx + int(node_r * math.cos(angle))
            ny = cy + int(node_r * math.sin(angle))

            # 연결선
            _draw_rough_line(draw, cx, cy, nx, ny, "#cccccc", 2)

            # 노드 원
            color = accent if i % 2 == 0 else blue
            _draw_rough_circle(draw, nx, ny, 40, color, 3)
            draw.text((nx - 12, ny - 10), f"#{i + 1}", fill=marker, font=font_node)

    def _draw_list(self, draw, subtitle, w, h, marker, accent, index):
        """체크리스트 레이아웃"""
        font_title = _load_font(44)
        font_item = _load_font(32)
        margin = 100

        # 제목
        draw.text((margin, 160), subtitle, fill=marker, font=font_title)
        _draw_rough_line(draw, margin, 220, w - margin, 220, accent, 3)

        # 체크리스트 항목
        items = 5
        for i in range(items):
            y = 280 + i * 90
            checked = i <= index % items

            # 체크박스
            _draw_rough_rect(draw, margin, y, margin + 36, y + 36, marker, 2)
            if checked:
                _draw_rough_line(draw, margin + 6, y + 18, margin + 14, y + 30, accent, 3)
                _draw_rough_line(draw, margin + 14, y + 30, margin + 30, y + 6, accent, 3)

            # 텍스트
            item_color = marker if checked else "#999999"
            draw.text((margin + 56, y + 2), f"Item {i + 1}", fill=item_color, font=font_item)

            # 취소선 (완료 항목)
            if checked:
                bbox = draw.textbbox((margin + 56, y + 2), f"Item {i + 1}", font=font_item)
                _draw_rough_line(draw, margin + 56, y + 20, bbox[2], y + 20, accent, 2)

    def _draw_diagram(self, draw, subtitle, w, h, marker, accent, blue, index):
        """플로우 다이어그램"""
        font_title = _load_font(40)
        font_node = _load_font(24)
        margin = 80
        cx = w // 2

        # 제목
        _draw_centered(draw, subtitle, font_title, marker, cx, 180, w - margin * 2)

        # 3단계 플로우 (상→하)
        steps = ["Input", "Process", "Output"]
        box_w, box_h = 240, 80
        start_y = 320
        gap = 120

        for i, step in enumerate(steps):
            y = start_y + i * (box_h + gap)
            bx = cx - box_w // 2
            color = accent if i == index % 3 else blue

            _draw_rough_rect(draw, bx, y, bx + box_w, y + box_h, color, 3)
            _draw_centered(draw, step, font_node, marker, cx, y + box_h // 2, box_w - 20)

            # 화살표
            if i < len(steps) - 1:
                _draw_arrow(draw, cx, y + box_h + 5, cx, y + box_h + gap - 5, marker, 2)

    def _draw_wrapup(self, draw, subtitle, w, h, marker, accent):
        """요약"""
        font_title = _load_font(52)
        cx = w // 2

        # 큰 프레임
        _draw_rough_rect(draw, 80, h // 3 - 20, w - 80, h // 3 + 280, accent, 4)
        _draw_centered(draw, subtitle, font_title, marker, cx, h // 3 + 130, w - 200)

        # 별 강조
        font_star = _load_font(36)
        draw.text((100, h // 3 - 10), "*", fill=accent, font=font_star)
        draw.text((w - 130, h // 3 - 10), "*", fill=accent, font=font_star)

    def _draw_cta(self, draw, subtitle, w, h, accent):
        """CTA"""
        font_big = _load_font(56)
        font_btn = _load_font(32)
        cx = w // 2

        _draw_centered(draw, subtitle, font_big, MARKER_COLORS["black"], cx, h // 2 - 60, w - 160)

        # 손글씨 화살표 (구독 유도)
        _draw_arrow(draw, cx - 80, h // 2 + 80, cx + 80, h // 2 + 80, accent, 3)
        draw.text((cx - 60, h // 2 + 100), "Subscribe!", fill=accent, font=font_btn)
