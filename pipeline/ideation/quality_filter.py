"""텍스트 유사도 검사 — 재사용 콘텐츠 패널티 회피

이전에 생성한 대본과 새 대본을 비교하여 유사도가 높으면 재생성 요청.
TF-IDF 코사인 유사도 사용 (외부 의존성 최소화).
"""

from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from pathlib import Path

from pipeline.config import OUTPUT_DIR

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 0.65  # 65% 이상 유사하면 재생성


def _tokenize(text: str) -> list[str]:
    """한국어/영어 혼합 토큰화"""
    text = text.lower()
    text = re.sub(r"[^\w가-힣a-z0-9\s]", " ", text)
    return [t for t in text.split() if len(t) > 1]


def _cosine_similarity(a: Counter, b: Counter) -> float:
    """두 Counter 간 코사인 유사도"""
    common = set(a.keys()) & set(b.keys())
    if not common:
        return 0.0

    dot = sum(a[k] * b[k] for k in common)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _extract_text_from_script(script_data: dict) -> str:
    """대본 JSON에서 텍스트 추출"""
    parts = []
    meta = script_data.get("metadata", {})
    parts.append(meta.get("title", ""))
    parts.append(meta.get("description", ""))

    for scene in script_data.get("scenes", []):
        if scene.get("narration"):
            parts.append(scene["narration"])
        if scene.get("subtitle"):
            parts.append(scene["subtitle"])

    return " ".join(parts)


def load_previous_scripts(limit: int = 50) -> list[str]:
    """이전 대본들의 텍스트를 로드"""
    texts = []
    if not OUTPUT_DIR.exists():
        return texts

    script_files = sorted(OUTPUT_DIR.glob("*/script.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    for sf in script_files[:limit]:
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
            text = _extract_text_from_script(data)
            if text.strip():
                texts.append(text)
        except Exception:
            continue

    return texts


def check_similarity(
    new_script: dict,
    threshold: float = DEFAULT_THRESHOLD,
) -> tuple[bool, float]:
    """새 대본이 기존 대본과 유사한지 검사

    Returns:
        (is_similar, max_similarity): 유사 여부, 최고 유사도
    """
    new_text = _extract_text_from_script(new_script)
    new_tokens = Counter(_tokenize(new_text))

    if not new_tokens:
        return False, 0.0

    previous_texts = load_previous_scripts()
    if not previous_texts:
        logger.info("이전 대본 없음 — 유사도 검사 건너뜀")
        return False, 0.0

    max_sim = 0.0
    for prev_text in previous_texts:
        prev_tokens = Counter(_tokenize(prev_text))
        sim = _cosine_similarity(new_tokens, prev_tokens)
        max_sim = max(max_sim, sim)

    is_similar = max_sim >= threshold
    if is_similar:
        logger.warning("유사도 %.1f%% (임계값 %.0f%%) — 재생성 권장", max_sim * 100, threshold * 100)
    else:
        logger.info("유사도 검사 통과: %.1f%% (임계값 %.0f%%)", max_sim * 100, threshold * 100)

    return is_similar, max_sim
