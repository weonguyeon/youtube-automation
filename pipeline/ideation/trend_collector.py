"""트렌드 키워드 수집 모듈

Google Trends + Pytrends를 사용해 인기 주제를 수집.
키워드 풀을 생성하여 자동 대본 생성에 공급.
"""

from __future__ import annotations

import logging
import random

logger = logging.getLogger(__name__)

# 카테고리별 시드 키워드 (자동 확장용)
SEED_TOPICS = {
    "data_comparison": [
        "GDP 순위 변화",
        "세계 인구 순위",
        "프로그래밍 언어 인기도",
        "세계 군사력 순위",
        "K-Pop 그룹 유튜브 조회수",
        "세계 도시 인구 변화",
        "스마트폰 브랜드 점유율",
        "올림픽 메달 순위 변화",
        "세계 대학 순위",
        "넷플릭스 시청률 순위",
    ],
    "science_health": [
        "커피가 뇌에 미치는 효과",
        "수면 부족이 몸에 미치는 영향",
        "운동이 뇌에 미치는 5가지 변화",
        "설탕이 몸에 미치는 진짜 영향",
        "명상의 과학적 효과",
        "장내 미생물이 건강에 미치는 영향",
        "비타민D 결핍 증상",
        "단백질이 부족할 때 나타나는 신호",
    ],
    "ai_tech": [
        "AI가 대체할 직업 TOP 10",
        "2026년 주목할 AI 트렌드",
        "GPT vs Claude vs Gemini 비교",
        "AI로 월 500만원 버는 방법",
        "코딩 없이 AI 앱 만들기",
        "AI 이미지 생성 도구 비교",
        "자동화로 시간 절약하는 방법",
    ],
    "motivation": [
        "성공한 사람들의 아침 루틴",
        "부자들의 습관 vs 가난한 사람의 습관",
        "1만 시간의 법칙은 거짓인가",
        "포기하고 싶을 때 기억할 말",
        "실패에서 배우는 5가지 교훈",
    ],
    "history_whatif": [
        "만약 인터넷이 없었다면",
        "고대 로마가 멸망하지 않았다면",
        "한국전쟁이 일어나지 않았다면",
        "스마트폰이 발명되지 않았다면",
        "공룡이 멸종하지 않았다면",
    ],
}


class TrendCollector:
    """트렌드 키워드 수집 + 주제 추천"""

    def get_topics(
        self,
        category: str | None = None,
        count: int = 5,
    ) -> list[str]:
        """카테고리별 주제 추천 (시드 기반 + Google Trends 확장)"""

        # Google Trends 시도
        trending = self._fetch_google_trends()
        if trending:
            logger.info("Google Trends에서 %d개 트렌드 수집", len(trending))

        # 시드 토픽에서 선택
        if category and category in SEED_TOPICS:
            pool = list(SEED_TOPICS[category])
        else:
            pool = [t for topics in SEED_TOPICS.values() for t in topics]

        # 트렌드 키워드를 pool 앞에 추가 (우선순위)
        pool = trending + pool

        random.shuffle(pool)
        return pool[:count]

    def get_categories(self) -> list[str]:
        return list(SEED_TOPICS.keys())

    def _fetch_google_trends(self) -> list[str]:
        """Google Trends 실시간 인기 검색어 수집"""
        try:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl="ko-KR", tz=540)
            trending = pytrends.trending_searches(pn="south_korea")
            results = trending[0].tolist()[:10]
            return [str(r) for r in results]
        except ImportError:
            logger.debug("pytrends 미설치 — 시드 토픽만 사용")
            return []
        except Exception as e:
            logger.debug("Google Trends 수집 실패: %s", e)
            return []
