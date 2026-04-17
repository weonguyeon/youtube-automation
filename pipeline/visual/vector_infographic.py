"""Pattern D: 벡터 인포그래픽 렌더러

캐릭터/아이콘/도형 조합으로 정보 구조를 시각화.
타임라인, 프로세스, 비교, 순위 등 구조화된 레이아웃.
Remotion 미사용 — PIL 기반 벡터 스타일 렌더링.
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


class VectorInfographicRenderer(BaseRenderer):
    """벡터 인포그래픽 렌더러 — 구조화된 정보 시각화"""

    def render(self, script: VideoScript, output_dir: Path) -> VisualResult:
        result = VisualResult()
        theme = get_theme(script.color_preset)
        spec = FORMAT_SPECS[script.format]
        w, h = spec["resolution"]

        total_scenes = len(script.scenes)
        for i, scene in enumerate(script.scenes):
            img_path = output_dir / f"vector_{scene.scene_id:03d}.png"
            self._render_scene(scene, theme, w, h, img_path, i, total_scenes)
            result.asset_paths.append(img_path)

        logger.info("벡터 인포그래픽 %d개 씬 생성", len(result.asset_paths))
        return result

    def _render_scene(
        self, scene: Scene, theme: ColorTheme, w: int, h: int,
        output_path: Path, index: int, total: int,
    ):
        img = Image.new("RGB", (w, h), theme.background)
        draw = ImageDraw.Draw(img)
        subtitle = (scene.subtitle or "").replace("**", "")

        # 배경 그라데이션
        bg_rgb = _hex_to_rgb(theme.background)
        sec_rgb = _hex_to_rgb(theme.secondary)
        for y in range(h):
            r = y / h
            cr = int(bg_rgb[0] + (sec_rgb[0] - bg_rgb[0]) * r * 0.2)
            cg = int(bg_rgb[1] + (sec_rgb[1] - bg_rgb[1]) * r * 0.2)
            cb = int(bg_rgb[2] + (sec_rgb[2] - bg_rgb[2]) * r * 0.2)
            draw.line([(0, y), (w, y)], fill=(cr, cg, cb))

        if scene.scene_type == SceneType.HOOK:
            self._draw_title_card(draw, subtitle, theme, w, h)
        elif scene.scene_type == SceneType.WRAPUP:
            self._draw_summary_card(draw, subtitle, theme, w, h)
        elif scene.scene_type == SceneType.CTA:
            self._draw_cta_card(draw, subtitle, theme, w, h)
        else:
            # content 씬은 인덱스에 따라 다른 레이아웃 순환
            layout = index % 4
            if layout == 0:
                self._draw_timeline_card(draw, subtitle, theme, w, h, index)
            elif layout == 1:
                self._draw_comparison_card(draw, subtitle, theme, w, h)
            elif layout == 2:
                self._draw_process_card(draw, subtitle, theme, w, h, index)
            else:
                self._draw_stats_card(draw, subtitle, theme, w, h, index)

        # 프로그레스 바 (하단)
        if total > 1:
            progress = (index + 1) / total
            bar_y = h - 12
            draw.rectangle([0, bar_y, w, h], fill=theme.secondary)
            draw.rectangle([0, bar_y, int(w * progress), h], fill=theme.accent)

        # 상단 액센트
        draw.rectangle([0, 0, w, 4], fill=theme.accent)

        img.save(output_path, "PNG", quality=95)

    def _draw_title_card(self, draw, subtitle, theme, w, h):
        """타이틀: 대형 헥사곤 + 텍스트"""
        font_big = _load_font(72)
        font_small = _load_font(28)
        cx, cy = w // 2, h // 2 - 40

        # 헥사곤 배경
        r = 200
        points = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(0, 360, 60)]
        draw.polygon(points, fill=theme.secondary, outline=theme.accent, width=4)

        _draw_centered(draw, subtitle, font_big, theme.text, cx, cy, r * 2 - 60)

        # 상단 레이블
        draw.rounded_rectangle([cx - 100, 160, cx + 100, 200], radius=20, fill=theme.accent)
        bbox = draw.textbbox((0, 0), "INFOGRAPHIC", font=font_small)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, 164), "INFOGRAPHIC", fill=theme.background, font=font_small)

        # 하단 장식 점들
        for i in range(7):
            x = cx - 90 + i * 30
            draw.ellipse([x, h - 180, x + 12, h - 168], fill=theme.accent if i == 3 else theme.primary)

    def _draw_timeline_card(self, draw, subtitle, theme, w, h, index):
        """타임라인 레이아웃"""
        font_title = _load_font(48)
        font_label = _load_font(24)
        margin = 80
        cx = w // 2

        # 제목
        _draw_centered(draw, subtitle, font_title, theme.text, cx, 200, w - margin * 2)

        # 타임라인 중앙선
        line_x = cx
        line_top = 320
        line_bottom = h - 200
        draw.rectangle([line_x - 3, line_top, line_x + 3, line_bottom], fill=theme.accent)

        # 타임라인 노드 (5개)
        nodes = 5
        for i in range(nodes):
            ny = line_top + (line_bottom - line_top) * i // (nodes - 1)
            # 원형 노드
            nr = 20
            draw.ellipse([line_x - nr, ny - nr, line_x + nr, ny + nr], fill=theme.accent)
            draw.ellipse([line_x - nr + 6, ny - nr + 6, line_x + nr - 6, ny + nr - 6], fill=theme.background)

            # 좌우 교차 카드
            if i % 2 == 0:
                card_x = margin
                card_w = cx - margin - 50
            else:
                card_x = cx + 50
                card_w = w - cx - margin - 50

            draw.rounded_rectangle(
                [card_x, ny - 30, card_x + card_w, ny + 30],
                radius=12, fill=theme.secondary, outline=theme.primary, width=1,
            )
            label = f"Step {i + 1}"
            draw.text((card_x + 16, ny - 12), label, fill=theme.text, font=font_label)

    def _draw_comparison_card(self, draw, subtitle, theme, w, h):
        """VS 비교 레이아웃"""
        font_title = _load_font(44)
        font_label = _load_font(32)
        font_small = _load_font(24)
        cx = w // 2
        margin = 60

        # 제목
        _draw_centered(draw, subtitle, font_title, theme.text, cx, 180, w - margin * 2)

        # 구분선
        draw.rectangle([margin, 250, w - margin, 254], fill=theme.accent)

        # 좌우 분할
        mid_y = h // 2 + 40
        left_cx = w // 4
        right_cx = w * 3 // 4

        # 왼쪽 카드
        draw.rounded_rectangle(
            [margin, 300, cx - 30, h - 200],
            radius=20, fill=theme.secondary, outline=theme.accent, width=2,
        )
        # 왼쪽 원형 아이콘
        draw.ellipse([left_cx - 50, 340, left_cx + 50, 440], fill=theme.accent)
        draw.text((left_cx - 8, 370), "A", fill=theme.background, font=font_label)

        # 오른쪽 카드
        draw.rounded_rectangle(
            [cx + 30, 300, w - margin, h - 200],
            radius=20, fill=theme.secondary, outline=theme.primary, width=2,
        )
        draw.ellipse([right_cx - 50, 340, right_cx + 50, 440], fill=theme.primary)
        draw.text((right_cx - 8, 370), "B", fill=theme.background, font=font_label)

        # 중앙 VS
        vs_y = mid_y - 20
        draw.ellipse([cx - 35, vs_y - 35, cx + 35, vs_y + 35], fill=theme.accent)
        bbox = draw.textbbox((0, 0), "VS", font=font_label)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, vs_y - 16), "VS", fill=theme.background, font=font_label)

    def _draw_process_card(self, draw, subtitle, theme, w, h, index):
        """프로세스 플로우 레이아웃"""
        font_title = _load_font(44)
        font_label = _load_font(24)
        font_num = _load_font(36)
        margin = 80
        cx = w // 2

        _draw_centered(draw, subtitle, font_title, theme.text, cx, 200, w - margin * 2)

        # 4단계 프로세스
        steps = 4
        step_w = (w - margin * 2 - 60 * (steps - 1)) // steps
        y_center = h // 2 + 20

        for i in range(steps):
            x = margin + i * (step_w + 60)
            # 원형 번호
            circle_cx = x + step_w // 2
            circle_cy = y_center - 60
            cr = 35
            draw.ellipse(
                [circle_cx - cr, circle_cy - cr, circle_cx + cr, circle_cy + cr],
                fill=theme.accent if i == index % steps else theme.primary,
            )
            bbox = draw.textbbox((0, 0), str(i + 1), font=font_num)
            tw = bbox[2] - bbox[0]
            draw.text((circle_cx - tw // 2, circle_cy - 18), str(i + 1), fill=theme.background, font=font_num)

            # 카드
            draw.rounded_rectangle(
                [x, y_center, x + step_w, y_center + 120],
                radius=12, fill=theme.secondary, outline=theme.accent, width=1,
            )
            draw.text((x + 12, y_center + 10), f"Phase {i + 1}", fill=theme.text, font=font_label)

            # 화살표 (마지막 제외)
            if i < steps - 1:
                arrow_x = x + step_w + 10
                arrow_y = circle_cy
                draw.polygon(
                    [(arrow_x, arrow_y - 10), (arrow_x + 30, arrow_y), (arrow_x, arrow_y + 10)],
                    fill=theme.accent,
                )

    def _draw_stats_card(self, draw, subtitle, theme, w, h, index):
        """통계 그리드 레이아웃"""
        font_title = _load_font(44)
        font_num = _load_font(64)
        font_label = _load_font(24)
        margin = 80
        cx = w // 2

        _draw_centered(draw, subtitle, font_title, theme.text, cx, 180, w - margin * 2)

        # 2x2 통계 그리드
        grid_top = 320
        card_w = (w - margin * 2 - 40) // 2
        card_h = (h - grid_top - 200) // 2 - 20
        stats = [("87%", "Success Rate"), ("3.2x", "Growth"), ("500+", "Projects"), ("24/7", "Support")]

        for i, (num, label) in enumerate(stats):
            col = i % 2
            row = i // 2
            x = margin + col * (card_w + 40)
            y = grid_top + row * (card_h + 20)

            color = theme.accent if (i + index) % 2 == 0 else theme.primary
            draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=20, fill=theme.secondary, outline=color, width=2)

            _draw_centered(draw, num, font_num, color, x + card_w // 2, y + card_h // 2 - 20, card_w - 40)
            _draw_centered(draw, label, font_label, theme.text, x + card_w // 2, y + card_h // 2 + 40, card_w - 40)

    def _draw_summary_card(self, draw, subtitle, theme, w, h):
        """요약 카드"""
        font_title = _load_font(52)
        font_small = _load_font(28)
        cx = w // 2

        draw.rectangle([0, 220, w, 228], fill=theme.accent)
        card_top = h // 3
        draw.rounded_rectangle(
            [80, card_top, w - 80, card_top + 320],
            radius=30, fill=theme.secondary, outline=theme.accent, width=3,
        )
        _draw_centered(draw, subtitle, font_title, theme.text, cx, card_top + 160, w - 200)

    def _draw_cta_card(self, draw, subtitle, theme, w, h):
        """CTA"""
        font_title = _load_font(56)
        font_btn = _load_font(28)
        cx = w // 2
        draw.rectangle([0, 0, w, h], fill=theme.primary)

        cy = h // 2 - 80
        _draw_centered(draw, subtitle, font_title, theme.text, cx, cy, w - 160)

        btn_w, btn_h = 360, 64
        draw.rounded_rectangle(
            [cx - btn_w // 2, h - 240, cx + btn_w // 2, h - 240 + btn_h],
            radius=32, fill=theme.accent,
        )
        bbox = draw.textbbox((0, 0), "SUBSCRIBE", font=font_btn)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, h - 234), "SUBSCRIBE", fill=theme.background, font=font_btn)
