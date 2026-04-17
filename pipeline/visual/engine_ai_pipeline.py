"""AI Pipeline 렌더링 엔진 (MoneyPrinter 스타일)

AI 이미지 생성 + TTS 음성 + 자동 조립.
가장 빠르게 완성된 영상을 만들 수 있는 엔진.

흐름:
1. 씬별 visual_prompt → AI 이미지 생성 (Flux/Midjourney)
2. narration → TTS 음성 생성 (ElevenLabs)
3. 이미지 + 음성 + 자막 → FFmpeg로 자동 조립
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from pipeline.colors import ColorTheme, get_theme
from pipeline.schema import FORMAT_SPECS, Scene, VideoScript
from pipeline.visual.base_renderer import BaseRenderer, VisualResult

logger = logging.getLogger(__name__)


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """시스템 폰트 로드 (한글 지원)"""
    font_candidates = [
        "C:/Windows/Fonts/malgunbd.ttf",   # 맑은 고딕 Bold
        "C:/Windows/Fonts/malgun.ttf",      # 맑은 고딕
        "C:/Windows/Fonts/NanumGothicBold.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fp in font_candidates:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


class AIPipelineRenderer(BaseRenderer):
    """AI 이미지 + TTS + 자동 조립 렌더러"""

    def render(self, script: VideoScript, output_dir: Path) -> VisualResult:
        result = VisualResult()
        theme = get_theme(script.color_preset)
        spec = FORMAT_SPECS[script.format]
        w, h = spec["resolution"]

        # 씬별 AI 이미지 생성
        for scene in script.scenes:
            img_path = output_dir / f"ai_scene_{scene.scene_id:03d}.png"
            self._generate_scene_image(scene, theme, w, h, img_path)
            result.asset_paths.append(img_path)

        logger.info("AI Pipeline: %d개 씬 이미지 생성 완료", len(result.asset_paths))
        return result

    def _generate_scene_image(
        self, scene: Scene, theme: ColorTheme, w: int, h: int, output_path: Path
    ):
        """씬별 이미지 생성 (AI API 또는 로컬 폴백)"""
        prompt = scene.visual_prompt
        if prompt:
            # 브랜드 컬러 스타일 접미사 추가
            full_prompt = prompt + theme.visual_prompt_suffix
            try:
                self._generate_with_ai(full_prompt, w, h, output_path)
                return
            except Exception as e:
                logger.warning("AI 이미지 생성 실패, 로컬 폴백: %s", e)

        # 폴백: 브랜드 컬러 기반 로컬 인포그래픽 카드 생성
        self._generate_local_card(scene, theme, w, h, output_path)

    def _generate_with_ai(self, prompt: str, w: int, h: int, output_path: Path):
        """Flux/Leonardo AI API로 이미지 생성"""
        from pipeline.config import settings

        if not settings.flux_api_key:
            raise ValueError("FLUX_API_KEY 미설정")

        # TODO: Flux API 연동
        # import requests
        # response = requests.post(
        #     "https://api.bfl.ml/v1/flux-pro-1.1",
        #     headers={"X-Key": settings.flux_api_key},
        #     json={"prompt": prompt, "width": w, "height": h}
        # )
        raise NotImplementedError("Flux API 연동 대기 중")

    def _generate_local_card(
        self, scene: Scene, theme: ColorTheme, w: int, h: int, output_path: Path
    ):
        """브랜드 컬러 기반 로컬 인포그래픽 카드 생성"""
        img = Image.new("RGB", (w, h), theme.background)
        draw = ImageDraw.Draw(img)

        subtitle = (scene.subtitle or "").replace("**", "")
        scene_type = scene.scene_type.value

        # 폰트
        font_title = _load_font(64)
        font_body = _load_font(44)
        font_small = _load_font(28)
        font_number = _load_font(120)

        text_color = theme.text
        accent_rgb = self._hex_to_rgb(theme.accent)
        primary_rgb = self._hex_to_rgb(theme.primary)
        bg_rgb = self._hex_to_rgb(theme.background)
        secondary_rgb = self._hex_to_rgb(theme.secondary)

        # 배경 그라데이션 효과 (상단→하단)
        for y_pos in range(h):
            ratio = y_pos / h
            r = int(bg_rgb[0] + (secondary_rgb[0] - bg_rgb[0]) * ratio * 0.3)
            g = int(bg_rgb[1] + (secondary_rgb[1] - bg_rgb[1]) * ratio * 0.3)
            b = int(bg_rgb[2] + (secondary_rgb[2] - bg_rgb[2]) * ratio * 0.3)
            draw.line([(0, y_pos), (w, y_pos)], fill=(r, g, b))

        cx = w // 2

        if scene_type == "hook":
            # Hook: 대형 숫자/텍스트 중심
            # 상단 작은 레이블
            draw.rounded_rectangle(
                [cx - 100, 200, cx + 100, 240], radius=20, fill=theme.accent,
            )
            bbox = draw.textbbox((0, 0), "INFOGRAPHIC", font=font_small)
            tw = bbox[2] - bbox[0]
            draw.text((cx - tw // 2, 204), "INFOGRAPHIC", fill=theme.background, font=font_small)

            # 중앙 대형 원형 + 텍스트
            cy = h // 2 - 60
            r = min(w, h) // 4
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                outline=theme.accent, width=6,
            )
            r2 = r - 20
            draw.ellipse(
                [cx - r2, cy - r2, cx + r2, cy + r2],
                outline=theme.primary, width=2,
            )
            # 원 안에 자막 텍스트
            self._draw_centered_text(draw, subtitle, font_title, text_color, cx, cy, w - 200)

            # 하단 장식 바
            bar_y = h * 3 // 4
            draw.rounded_rectangle(
                [80, bar_y, w - 80, bar_y + 8], radius=4, fill=theme.accent,
            )

        elif scene_type == "content":
            # Content: 카드 + 텍스트 + 데이터 바
            margin = 60

            # 상단 씬 번호 뱃지
            badge_text = f"#{scene.scene_id:02d}"
            draw.rounded_rectangle([margin, 120, margin + 100, 170], radius=12, fill=theme.accent)
            draw.text((margin + 16, 126), badge_text, fill=theme.background, font=font_small)

            # 상단 헤더 라인
            draw.rectangle([margin, 190, w - margin, 194], fill=theme.accent)

            # 메인 카드
            card_top = 240
            card_bottom = h - 300
            draw.rounded_rectangle(
                [margin, card_top, w - margin, card_bottom],
                radius=24, fill=theme.secondary, outline=theme.accent, width=2,
            )

            # 카드 내부 자막 텍스트
            text_y = card_top + 60
            self._draw_centered_text(draw, subtitle, font_title, text_color, cx, text_y + 40, w - margin * 2 - 60)

            # 데이터 바 (시각적 데이터 표현)
            bar_y = card_top + 200
            bar_labels = ["Data A", "Data B", "Data C"]
            bar_ratios = [0.85, 0.65, 0.45]
            max_bar_w = w - margin * 2 - 80
            for i, (label, ratio) in enumerate(zip(bar_labels, bar_ratios)):
                y = bar_y + i * 80
                # 레이블
                draw.text((margin + 30, y), label, fill=text_color, font=font_small)
                # 바 배경
                draw.rounded_rectangle(
                    [margin + 30, y + 32, margin + 30 + max_bar_w, y + 62],
                    radius=8, fill=theme.background,
                )
                # 바 값
                bar_w = int(max_bar_w * ratio)
                fill_color = theme.accent if i == 0 else theme.primary
                draw.rounded_rectangle(
                    [margin + 30, y + 32, margin + 30 + bar_w, y + 62],
                    radius=8, fill=fill_color,
                )
                # 퍼센트 표시
                pct_text = f"{int(ratio * 100)}%"
                draw.text((margin + 40 + bar_w, y + 34), pct_text, fill=text_color, font=font_small)

            # 하단 출처 텍스트
            draw.text(
                (margin, card_bottom + 20), "Source: Global Data Report 2025",
                fill=text_color, font=font_small,
            )

        elif scene_type == "wrapup":
            # Wrapup: 요약 카드
            # 상단 액센트 바
            draw.rectangle([0, 250, w, 258], fill=theme.accent)

            # 중앙 요약 영역
            summary_top = h // 3
            draw.rounded_rectangle(
                [80, summary_top, w - 80, summary_top + 300],
                radius=30, fill=theme.secondary, outline=theme.accent, width=3,
            )
            # 요약 텍스트
            self._draw_centered_text(
                draw, subtitle, font_title, text_color, cx, summary_top + 130, w - 200,
            )

            # 하단 CTA 영역
            draw.rectangle([0, h - 280, w, h], fill=theme.primary)
            draw.rectangle([0, h - 286, w, h - 280], fill=theme.accent)
            # CTA 버튼
            btn_w, btn_h = 400, 70
            draw.rounded_rectangle(
                [cx - btn_w // 2, h - 200, cx + btn_w // 2, h - 200 + btn_h],
                radius=35, fill=theme.accent,
            )
            bbox = draw.textbbox((0, 0), "SUBSCRIBE", font=font_body)
            tw = bbox[2] - bbox[0]
            draw.text((cx - tw // 2, h - 194), "SUBSCRIBE", fill=theme.background, font=font_body)

        elif scene_type == "cta":
            # CTA: 풀스크린 강조
            draw.rectangle([0, 0, w, h], fill=theme.primary)

            # 큰 원형 배경
            cy = h // 2 - 50
            r = 200
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=theme.accent)

            # 중앙 텍스트
            self._draw_centered_text(draw, subtitle, font_title, theme.background, cx, cy, r * 2 - 40)

            # 하단 화살표 장식
            arrow_y = h * 3 // 4
            for i in range(3):
                ay = arrow_y + i * 40
                alpha = 1.0 - i * 0.3
                aw = 60 - i * 15
                draw.polygon(
                    [(cx - aw, ay), (cx + aw, ay), (cx, ay + 30)],
                    fill=theme.accent,
                )

        # 상단/하단 액센트 라인
        draw.rectangle([0, 0, w, 5], fill=theme.accent)
        draw.rectangle([0, h - 5, w, h], fill=theme.accent)

        img.save(output_path, "PNG", quality=95)

    def _draw_centered_text(
        self, draw: ImageDraw.Draw, text: str, font, color: str,
        cx: int, cy: int, max_width: int,
    ):
        """텍스트를 중앙 정렬로 그리기 (자동 줄바꿈)"""
        if not text:
            return
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

        line_height = draw.textbbox((0, 0), "Ag가", font=font)[3] + 8
        total_h = len(lines) * line_height
        y = cy - total_h // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((cx - tw // 2, y), line, fill=color, font=font)
            y += line_height

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
