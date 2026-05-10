"""프리셋 API 라우트 — 패턴/포맷/컬러/엔진 목록"""

from __future__ import annotations

from fastapi import APIRouter

from pipeline.colors import list_presets as get_color_presets
from pipeline.schema import FORMAT_SPECS, Pattern, RenderEngine

router = APIRouter(prefix="/api/presets", tags=["presets"])

PATTERN_DESCRIPTIONS = {
    "A": {
        "name": "데이터 비주얼라이제이션",
        "desc": "막대차트 레이스, 파이차트 변화",
        "difficulty": 1,
    },
    "B": {
        "name": "텍스트 인포그래픽 숏폼",
        "desc": "큰 자막 + 빠른 컷 + AI 이미지",
        "difficulty": 2,
    },
    "C": {"name": "무음 인포그래픽", "desc": "차트/그래프 + 텍스트만", "difficulty": 1},
    "D": {"name": "2D 벡터 인포그래픽", "desc": "캐릭터 + 배경 + 아이콘 조합", "difficulty": 3},
    "E": {"name": "화이트보드 애니메이션", "desc": "가상 손이 그리는 드로잉", "difficulty": 3},
    "F": {"name": "3D 인체/과학", "desc": "3D 모델 + 카메라 애니메이션", "difficulty": 4},
}

ENGINE_DESCRIPTIONS = {
    "manim": {"name": "Manim", "desc": "Python 코드 기반 차트/수학 애니메이션"},
    "remotion": {"name": "Remotion", "desc": "React 컴포넌트 기반 인포그래픽 템플릿"},
    "ai_pipeline": {"name": "AI Pipeline", "desc": "AI 이미지 + TTS + 자동 조립"},
}


@router.get("/patterns")
def get_patterns():
    return [
        {
            "id": p.value,
            "name": PATTERN_DESCRIPTIONS[p.value]["name"],
            "description": PATTERN_DESCRIPTIONS[p.value]["desc"],
            "difficulty": PATTERN_DESCRIPTIONS[p.value]["difficulty"],
        }
        for p in Pattern
    ]


@router.get("/formats")
def get_formats():
    return [
        {
            "id": f.value,
            "duration_sec": spec["duration_sec"],
            "aspect_ratio": spec["aspect_ratio"].value,
            "resolution": list(spec["resolution"]),
            "max_scenes": spec["max_scenes"],
        }
        for f, spec in FORMAT_SPECS.items()
    ]


@router.get("/colors")
def get_colors():
    return get_color_presets()


@router.get("/engines")
def get_engines():
    return [
        {
            "id": e.value,
            "name": ENGINE_DESCRIPTIONS[e.value]["name"],
            "description": ENGINE_DESCRIPTIONS[e.value]["desc"],
        }
        for e in RenderEngine
    ]


@router.get("/platforms")
def get_platforms():
    """멀티플랫폼 익스포트 대상 목록"""
    from pipeline.publish.multiplatform import list_platforms
    return list_platforms()
