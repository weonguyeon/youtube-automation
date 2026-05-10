"""CLI 진입점

사용법:
  python -m pipeline.main --topic "주제" --pattern A --format S8
  python -m pipeline.main --topic "주제" --pattern B --format S15 --color ocean_blue
"""

from __future__ import annotations

import argparse
import logging
import sys

from pipeline.orchestrator import VideoPipeline
from pipeline.schema import ColorPreset, Pattern, RenderEngine, VideoFormat


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def cli():
    parser = argparse.ArgumentParser(
        description="YouTube Faceless Automation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 8초 차트 레이스 (Pattern A)
  yt-auto --topic "세계 GDP 순위" --pattern A --format S8

  # 15초 텍스트 숏폼 (Pattern B, 오션 블루)
  yt-auto --topic "커피의 효과" --pattern B --format S15 --color ocean_blue

  # CSV 기반 차트 레이스
  yt-auto --topic "K-Pop 조회수" --pattern A --format S8 --csv data/kpop.csv

  # 렌더링 엔진 지정 (manim/remotion/ai_pipeline)
  yt-auto --topic "AI 트렌드" --format S15 --engine manim
        """,
    )

    parser.add_argument("--topic", default=None, help="영상 주제 (미지정 시 트렌드에서 자동 선택)")
    parser.add_argument(
        "--category",
        choices=["data_comparison", "science_health", "ai_tech", "motivation", "history_whatif"],
        default=None,
        help="트렌드 카테고리 (--topic 미지정 시 사용)",
    )
    parser.add_argument(
        "--pattern",
        choices=["A", "B", "C", "D", "E", "F"],
        default="A",
        help="영상 패턴 (A:데이터, B:텍스트, C:무음, D:벡터, E:화이트보드, F:3D)",
    )
    parser.add_argument(
        "--format",
        choices=["S8", "S15", "L3", "L5", "L10"],
        default="S8",
        help="영상 포맷 (S8:8초, S15:15초, L3:3분, L5:5분, L10:10분)",
    )
    parser.add_argument(
        "--color",
        choices=[p.value for p in ColorPreset],
        default=None,
        help="컬러 프리셋 (미지정 시 .env BRAND_COLOR_PRESET 사용)",
    )
    parser.add_argument(
        "--engine",
        choices=[e.value for e in RenderEngine],
        default=None,
        help="렌더링 엔진 (manim/remotion/ai_pipeline, 미지정 시 Pattern 기반)",
    )
    parser.add_argument("--csv", help="CSV 데이터 파일 경로 (Pattern A용)")
    parser.add_argument("--upload", action="store_true", help="YouTube 자동 업로드")
    parser.add_argument(
        "--platforms",
        default=None,
        help="멀티플랫폼 익스포트 (콤마구분). e.g. youtube_shorts,tiktok,instagram_reels",
    )
    parser.add_argument(
        "--batch",
        default=None,
        help="배치 작업 파일 경로 (.yaml/.yml/.json). 지정 시 배치 모드로 실행",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="상세 로그")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # 배치 모드
    if args.batch:
        from pipeline.batch import run_batch
        summary = run_batch(args.batch)
        print(f"\n[Batch] 완료 — 성공 {summary.success_count}/{summary.total}")
        if summary.fail_count:
            sys.exit(1)
        return

    # 주제 자동 선택
    topic = args.topic
    if not topic:
        from pipeline.ideation.trend_collector import TrendCollector
        collector = TrendCollector()
        topics = collector.get_topics(category=args.category, count=1)
        topic = topics[0]
        print(f"[Auto] 트렌드 주제 선택: {topic}")

    platforms = [p.strip() for p in args.platforms.split(",")] if args.platforms else None

    pipeline = VideoPipeline()
    result = pipeline.run(
        topic=topic,
        pattern=Pattern(args.pattern),
        fmt=VideoFormat(args.format),
        color_preset=ColorPreset(args.color) if args.color else None,
        render_engine=RenderEngine(args.engine) if args.engine else None,
        upload=args.upload,
        csv_path=args.csv,
        platforms=platforms,
    )

    if result.success:
        print(f"\n[OK] 영상 생성 완료: {result.video_path}")
        if result.upload_url:
            print(f"[YouTube] {result.upload_url}")
        if result.platform_exports:
            print(f"[Multiplatform] {len(result.platform_exports)}개 플랫폼 익스포트:")
            for ex in result.platform_exports:
                print(f"   - {ex['platform']}: {ex['path']}")
    else:
        print("\n[ERROR] 에러 발생:")
        for err in result.errors:
            safe_err = err.encode("ascii", errors="replace").decode("ascii")
            print(f"   - {safe_err}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
