"""VideoPipeline - 순수 Python 기반 영상 제작 오케스트레이터

n8n 없이 Python 코드로 전체 파이프라인을 실행.
각 Stage를 순차 실행하고, 모니터링/유사도 검사/에러 핸들링 담당.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import OUTPUT_DIR, settings
from pipeline.schema import ColorPreset, Pattern, RenderEngine, VideoFormat, VideoScript

logger = logging.getLogger(__name__)

MAX_SIMILARITY_RETRIES = 2  # 유사도 초과 시 최대 재생성 횟수


@dataclass
class PipelineResult:
    video_id: str
    video_path: Path | None = None
    upload_url: str | None = None
    errors: list[str] = field(default_factory=list)
    success: bool = False


class VideoPipeline:
    """전체 파이프라인 실행 엔진"""

    def __init__(self):
        self._script_gen = None
        self._audio_gen = None
        self._visual_gen = None
        self._assembler = None
        self._publisher = None

    def _get_script_generator(self):
        if self._script_gen is None:
            from pipeline.ideation.script_writer import ScriptWriter
            self._script_gen = ScriptWriter()
        return self._script_gen

    def _get_audio_generator(self):
        if self._audio_gen is None:
            from pipeline.audio.audio_mixer import AudioMixer
            self._audio_gen = AudioMixer()
        return self._audio_gen

    def _get_visual_generator(self, pattern: Pattern, engine: RenderEngine | None = None):
        if engine is not None:
            from pipeline.visual.base_renderer import get_engine_renderer
            return get_engine_renderer(engine)
        from pipeline.visual.base_renderer import get_renderer
        return get_renderer(pattern)

    def _get_assembler(self):
        if self._assembler is None:
            from pipeline.assembly.ffmpeg_renderer import FFmpegRenderer
            self._assembler = FFmpegRenderer()
        return self._assembler

    def _get_publisher(self):
        if self._publisher is None:
            from pipeline.publish.youtube_uploader import YouTubeUploader
            self._publisher = YouTubeUploader()
        return self._publisher

    def run(
        self,
        topic: str,
        pattern: Pattern = Pattern.A_DATA_VIZ,
        fmt: VideoFormat = VideoFormat.S8,
        color_preset: ColorPreset | None = None,
        render_engine: RenderEngine | None = None,
        upload: bool = False,
        csv_path: str | None = None,
    ) -> PipelineResult:
        """전체 파이프라인 실행"""

        if color_preset is None:
            color_preset = ColorPreset(settings.brand_color_preset)

        video_id = str(uuid.uuid4())[:8]
        result = PipelineResult(video_id=video_id)
        output_dir = OUTPUT_DIR / video_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # 모니터링 시작
        from pipeline.monitoring import PipelineMonitor
        monitor = PipelineMonitor(video_id, topic, pattern.value, fmt.value)

        try:
            # Stage 1: 대본 생성 + 유사도 검사
            monitor.start_stage("script_generation")
            script = self._generate_script_with_filter(
                topic, pattern, fmt, color_preset, csv_path
            )
            script_path = output_dir / "script.json"
            script_path.write_text(
                json.dumps(script.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            monitor.end_stage(success=True)

            # Stage 2: 오디오 생성
            monitor.start_stage("audio_generation")
            audio_gen = self._get_audio_generator()
            audio_result = audio_gen.generate(script, output_dir)
            monitor.end_stage(success=True)

            # Stage 3: 시각 에셋 생성
            engine_label = render_engine.value if render_engine else f"Pattern {pattern.value}"
            monitor.start_stage(f"visual_generation ({engine_label})")
            visual_gen = self._get_visual_generator(pattern, render_engine)
            visual_result = visual_gen.render(script, output_dir)
            monitor.end_stage(success=True)

            # Stage 4: 조립 & 렌더링
            monitor.start_stage("assembly")
            assembler = self._get_assembler()
            video_path = assembler.assemble(
                script=script,
                audio=audio_result,
                visuals=visual_result,
                output_dir=output_dir,
            )
            result.video_path = video_path
            monitor.end_stage(success=True)

            # Stage 5: 업로드 (선택)
            if upload:
                monitor.start_stage("upload")
                publisher = self._get_publisher()
                url = publisher.upload(video_path, script.metadata)
                result.upload_url = url
                monitor.end_stage(success=True)

            result.success = True
            monitor.finish(success=True)
            logger.info("파이프라인 완료: %s", video_path)

        except Exception as e:
            logger.error("파이프라인 에러: %s", e)
            result.errors.append(str(e))
            if monitor._current_stage:
                monitor.end_stage(success=False, error=str(e))
            monitor.finish(success=False)

        return result

    def _generate_script_with_filter(
        self,
        topic: str,
        pattern: Pattern,
        fmt: VideoFormat,
        color_preset: ColorPreset,
        csv_path: str | None,
    ) -> VideoScript:
        """대본 생성 + 유사도 검사 (초과 시 재생성)"""
        from pipeline.ideation.quality_filter import check_similarity

        script_gen = self._get_script_generator()

        for attempt in range(MAX_SIMILARITY_RETRIES + 1):
            logger.info("[Stage 1] 대본 생성: %s (시도 %d)", topic, attempt + 1)
            script = script_gen.generate(
                topic=topic,
                pattern=pattern,
                fmt=fmt,
                color_preset=color_preset,
                csv_path=csv_path,
            )

            # 유사도 검사
            script_dict = script.model_dump(mode="json")
            is_similar, similarity = check_similarity(script_dict)

            if not is_similar:
                return script

            if attempt < MAX_SIMILARITY_RETRIES:
                logger.warning("유사도 %.0f%% — 재생성 시도 (%d/%d)", similarity * 100, attempt + 1, MAX_SIMILARITY_RETRIES)
            else:
                logger.warning("유사도 %.0f%% — 최대 재시도 초과, 현재 대본 사용", similarity * 100)

        return script
