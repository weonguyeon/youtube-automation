"""8색 컬러 프리셋 시스템

웹사이트에서 사용자가 선택 가능한 8가지 컬러 테마.
선택된 컬러가 인포그래픽 전체(차트, 자막, 배경, 이미지 프롬프트)에 적용됨.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.schema import ColorPreset


@dataclass(frozen=True)
class ColorTheme:
    name: str
    label_ko: str
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    text_highlight: str
    chart_colors: list[str]
    mood: str

    @property
    def subtitle_bg(self) -> str:
        return f"{self.background}99"

    @property
    def visual_prompt_suffix(self) -> str:
        return (
            f", color scheme: {self.primary} and {self.accent} "
            f"on {self.background} background, flat 2d vector style"
        )


COLOR_THEMES: dict[ColorPreset, ColorTheme] = {
    ColorPreset.MIDNIGHT_NAVY: ColorTheme(
        name="midnight_navy",
        label_ko="미드나잇 네이비",
        primary="#1a1a2e",
        secondary="#16213e",
        accent="#e94560",
        background="#0f0f23",
        text="#ffffff",
        text_highlight="#e94560",
        chart_colors=["#e94560", "#16213e", "#533483", "#0f3460", "#2b9348", "#ff6b35", "#00b4d8"],
        mood="프로페셔널, 테크",
    ),
    ColorPreset.OCEAN_BLUE: ColorTheme(
        name="ocean_blue",
        label_ko="오션 블루",
        primary="#0077b6",
        secondary="#00b4d8",
        accent="#90e0ef",
        background="#03045e",
        text="#ffffff",
        text_highlight="#90e0ef",
        chart_colors=["#0077b6", "#00b4d8", "#90e0ef", "#48cae4", "#023e8a", "#caf0f8", "#ade8f4"],
        mood="신뢰감, 기업용",
    ),
    ColorPreset.SUNSET_ORANGE: ColorTheme(
        name="sunset_orange",
        label_ko="선셋 오렌지",
        primary="#ff6b35",
        secondary="#f7c59f",
        accent="#efefd0",
        background="#1a1a2e",
        text="#ffffff",
        text_highlight="#ff6b35",
        chart_colors=["#ff6b35", "#f7c59f", "#004e89", "#1a659e", "#ff9f1c", "#e71d36", "#2ec4b6"],
        mood="에너지, 활력",
    ),
    ColorPreset.FOREST_GREEN: ColorTheme(
        name="forest_green",
        label_ko="포레스트 그린",
        primary="#2d6a4f",
        secondary="#40916c",
        accent="#95d5b2",
        background="#1b2a1f",
        text="#ffffff",
        text_highlight="#95d5b2",
        chart_colors=["#2d6a4f", "#40916c", "#52b788", "#74c69d", "#95d5b2", "#b7e4c7", "#d8f3dc"],
        mood="자연, 건강",
    ),
    ColorPreset.ROYAL_PURPLE: ColorTheme(
        name="royal_purple",
        label_ko="로얄 퍼플",
        primary="#7b2cbf",
        secondary="#9d4edd",
        accent="#c77dff",
        background="#10002b",
        text="#ffffff",
        text_highlight="#c77dff",
        chart_colors=["#7b2cbf", "#9d4edd", "#c77dff", "#e0aaff", "#5a189a", "#3c096c", "#240046"],
        mood="크리에이티브, 혁신",
    ),
    ColorPreset.CORAL_PINK: ColorTheme(
        name="coral_pink",
        label_ko="코랄 핑크",
        primary="#ff6b6b",
        secondary="#ffa07a",
        accent="#ffd1dc",
        background="#2d2d2d",
        text="#ffffff",
        text_highlight="#ff6b6b",
        chart_colors=["#ff6b6b", "#ffa07a", "#ee6c4d", "#f4845f", "#f3722c", "#f94144", "#f8961e"],
        mood="트렌디, 소셜",
    ),
    ColorPreset.GOLD_PREMIUM: ColorTheme(
        name="gold_premium",
        label_ko="골드 프리미엄",
        primary="#d4a373",
        secondary="#e6b980",
        accent="#fefae0",
        background="#1a1a1a",
        text="#ffffff",
        text_highlight="#d4a373",
        chart_colors=["#d4a373", "#e6b980", "#ccd5ae", "#faedcd", "#d4a373", "#a98467", "#6c584c"],
        mood="럭셔리, 금융",
    ),
    ColorPreset.MONO_GRAY: ColorTheme(
        name="mono_gray",
        label_ko="모노 그레이",
        primary="#adb5bd",
        secondary="#6c757d",
        accent="#e9ecef",
        background="#212529",
        text="#ffffff",
        text_highlight="#e9ecef",
        chart_colors=["#adb5bd", "#6c757d", "#495057", "#343a40", "#dee2e6", "#ced4da", "#868e96"],
        mood="미니멀, 클린",
    ),
}


def get_theme(preset: ColorPreset) -> ColorTheme:
    return COLOR_THEMES[preset]


def list_presets() -> list[dict]:
    """프리셋 목록을 UI 표시용 dict 리스트로 반환"""
    return [
        {
            "id": preset.value,
            "name": theme.label_ko,
            "primary": theme.primary,
            "accent": theme.accent,
            "background": theme.background,
            "mood": theme.mood,
        }
        for preset, theme in COLOR_THEMES.items()
    ]
