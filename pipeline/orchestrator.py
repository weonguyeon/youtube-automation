"""VideoPipeline - 순수 Python 기반 영상 제작 오케스트레이터

n8n 없이 Python 코드로 전체 파이프라인을 실행.
각 Stage를 순차 실행하고, 에러 핸들링/로깅 담당.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import OUTPUT_DIR, settings
from pipeline.schema import ColorPreset, Pattern, RenderEngine, VideoFormat, VideoScript

logger = logging.getLogger(__name__)


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

        # 채널 브랜드 컬러 (미지정 시 설정에서 가져옴)
        if color_preset is None:
            color_preset = ColorPreset(settings.brand_color_preset)

        video_id = str(uuid.uuid4())[:8]
        result = PipelineResult(video_id=video_id)
        output_dir = OUTPUT_DIR / video_id
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Stage 1: 대본 생성
            logger.info("[Stage 1] 대본 생성: %s", topic)
            script_gen = self._get_script_generator()
            script = script_gen.generate(
                topic=topic,
                pattern=pattern,
                fmt=fmt,
                color_preset=color_preset,
                csv_path=csv_path,
            )
            # 대본 JSON 저장
            import json
            script_path = output_dir / "script.json"
            script_path.write_text(
                json.dumps(script.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # Stage 2: 오디오 생성
            logger.info("[Stage 2] 오디오 생성")
            audio_gen = self._get_audio_generator()
            audio_result = audio_gen.generate(script, output_dir)

            # Stage 3: 시각 에셋 생성
            if render_engine:
                logger.info("[Stage 3] 시각 에셋 생성 (Engine: %s)", render_engine.value)
            else:
                logger.info("[Stage 3] 시각 에셋 생성 (Pattern %s)", pattern.value)
            visual_gen = self._get_visual_generator(pattern, render_engine)
            visual_result = visual_gen.render(script, output_dir)

            # Stage 4: 조립 & 렌더링
            logger.info("[Stage 4] 영상 조립")
            assembler = self._get_assembler()
            video_path = assembler.assemble(
                script=script,
                audio=audio_result,
                visuals=visual_result,
                output_dir=output_dir,
            )
            result.video_path = video_path

            # Stage 5: 업로드 (선택)
            if upload:
                logger.info("[Stage 5] YouTube 업로드")
                publisher = self._get_publisher()
                url = publisher.upload(video_path, script.metadata)
                result.upload_url = url

            result.success = True
            logger.info("파이프라인 완료: %s", video_path)

        except Exception as e:
            logger.error("파이프라인 에러: %s", e)
            result.errors.append(str(e))

        return result
