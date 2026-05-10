"""E2E 파이프라인 테스트 (Stage 2~5)

Stage 1(대본 생성)을 건너뛰고, 하드코딩된 대본으로
오디오 → 시각 → 조립 파이프라인을 검증.
"""

import json
import shutil
from pathlib import Path

from pipeline.audio.audio_mixer import AudioMixer
from pipeline.assembly.ffmpeg_renderer import FFmpegRenderer
from pipeline.config import OUTPUT_DIR
from pipeline.schema import VideoScript
from pipeline.assembly.thumbnail import ThumbnailGenerator
from pipeline.visual.base_renderer import get_engine_renderer
from pipeline.visual.engine_ai_pipeline import AIPipelineRenderer

TEST_SCRIPT = {
    "pattern": "B",
    "format": "S15",
    "color_preset": "midnight_navy",
    "metadata": {
        "title": "커피가 뇌에 미치는 5가지 효과",
        "description": "매일 마시는 커피, 우리 뇌에 어떤 영향을 줄까?",
        "tags": ["커피", "뇌과학", "건강", "카페인"],
        "thumbnail_text": "커피 vs 뇌",
    },
    "scenes": [
        {
            "scene_id": 1,
            "scene_type": "hook",
            "duration_sec": 3,
            "narration": "전 세계 인구의 80%가 매일 마시는 이것, 당신의 뇌를 바꾸고 있습니다.",
            "subtitle": "80%가 매일 마시는 이것",
            "visual_prompt": "flat 2d infographic brain with coffee cup, dark navy background, no text, no words, no letters",
            "transition": "fade",
            "asset_type": "generated",
        },
        {
            "scene_id": 2,
            "scene_type": "content",
            "duration_sec": 3,
            "narration": "첫 번째, 카페인은 도파민 분비를 촉진해 집중력을 높입니다.",
            "subtitle": "집중력 향상",
            "visual_prompt": "flat 2d infographic dopamine molecule and brain neurons firing, dark navy background, no text, no words, no letters",
            "transition": "slide_left",
            "asset_type": "generated",
        },
        {
            "scene_id": 3,
            "scene_type": "content",
            "duration_sec": 3,
            "narration": "두 번째, 단기 기억력을 최대 30% 향상시킵니다.",
            "subtitle": "기억력 +30%",
            "visual_prompt": "flat 2d infographic memory boost chart showing 30 percent increase, dark navy background, no text, no words, no letters",
            "transition": "cut",
            "asset_type": "generated",
        },
        {
            "scene_id": 4,
            "scene_type": "content",
            "duration_sec": 3,
            "narration": "세 번째, 알츠하이머 위험을 65%까지 낮출 수 있습니다.",
            "subtitle": "알츠하이머 -65%",
            "visual_prompt": "flat 2d infographic brain shield protection icon, dark navy background, no text, no words, no letters",
            "transition": "fade",
            "asset_type": "generated",
        },
        {
            "scene_id": 5,
            "scene_type": "wrapup",
            "duration_sec": 2,
            "narration": "하지만 하루 4잔 이상은 오히려 독이 됩니다.",
            "subtitle": "4잔 이상은 독",
            "visual_prompt": "flat 2d infographic warning sign with coffee cups, dark navy background, no text, no words, no letters",
            "transition": "zoom_in",
            "asset_type": "generated",
        },
        {
            "scene_id": 6,
            "scene_type": "cta",
            "duration_sec": 1,
            "narration": None,
            "subtitle": "구독과 좋아요!",
            "visual_prompt": "flat 2d subscribe button icon, dark navy background, no text, no words, no letters",
            "transition": "fade",
            "asset_type": "generated",
        },
    ],
    "audio": {
        "has_narration": True,
        "voice_style": "curious",
        "bgm_mood": "lofi",
        "bgm_volume": 0.15,
    },
}


def test_stages_2_to_4():
    """Stage 2(오디오) → Stage 3(시각) → Stage 4(조립) E2E 테스트"""
    script = VideoScript.model_validate(TEST_SCRIPT)
    output_dir = OUTPUT_DIR / "test_e2e"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # 대본 저장
    (output_dir / "script.json").write_text(
        json.dumps(TEST_SCRIPT, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Stage 2: 오디오
    print("\n[Stage 2] 오디오 생성...")
    audio_mixer = AudioMixer()
    audio_result = audio_mixer.generate(script, output_dir)
    print(f"  BGM: {audio_result.bgm_path}")
    print(f"  Merged: {audio_result.merged_path}")
    print(f"  SRT: {audio_result.subtitle_srt_path}")
    print(f"  Duration: {audio_result.duration_sec:.1f}s")

    # Stage 3: 시각 에셋
    print("\n[Stage 3] 시각 에셋 생성 (AI Pipeline - 로컬 카드)...")
    renderer = AIPipelineRenderer()
    visual_result = renderer.render(script, output_dir)
    print(f"  이미지 {len(visual_result.asset_paths)}개 생성")
    for p in visual_result.asset_paths:
        print(f"    - {p.name} ({p.stat().st_size // 1024}KB)")

    # Stage 4: 조립
    print("\n[Stage 4] FFmpeg 영상 조립...")
    assembler = FFmpegRenderer()
    video_path = assembler.assemble(
        script=script,
        audio=audio_result,
        visuals=visual_result,
        output_dir=output_dir,
    )

    if not video_path.exists():
        print("\n[FAIL] 영상 생성 실패")
        return False

    size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"\n[OK] 최종 영상: {video_path}")
    print(f"     크기: {size_mb:.1f}MB")

    # 썸네일 생성
    print("\n[Thumbnail] 썸네일 생성...")
    thumb_gen = ThumbnailGenerator()
    thumb_path = thumb_gen.generate(script, visual_result.asset_paths, output_dir)
    if thumb_path.exists():
        print(f"  [OK] {thumb_path.name} ({thumb_path.stat().st_size // 1024}KB)")
    else:
        print("  [FAIL] 썸네일 생성 실패")

    return True


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    success = test_stages_2_to_4()
    print(f"\n{'=' * 50}")
    print(f"E2E 테스트: {'PASS' if success else 'FAIL'}")
