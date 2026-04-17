"""FFmpeg 기반 최종 영상 조립

시각 에셋(이미지/클립) + 오디오 + 자막 → 최종 MP4
"""

from __future__ import annotations

import logging
from pathlib import Path

import ffmpeg

from pipeline.colors import get_theme
from pipeline.schema import FORMAT_SPECS, VideoScript
from pipeline.audio.audio_mixer import AudioResult
from pipeline.visual.base_renderer import VisualResult

logger = logging.getLogger(__name__)


class FFmpegRenderer:
    """FFmpeg로 최종 영상 조립"""

    def assemble(
        self,
        script: VideoScript,
        audio: AudioResult,
        visuals: VisualResult,
        output_dir: Path,
    ) -> Path:
        output_path = output_dir / "final.mp4"
        spec = FORMAT_SPECS[script.format]
        w, h = spec["resolution"]

        if visuals.video_clip_path:
            # Pattern A: 이미 영상 클립이 있는 경우 (차트 레이스)
            self._assemble_from_video(
                video_path=visuals.video_clip_path,
                audio_path=audio.merged_path,
                srt_path=audio.subtitle_srt_path,
                output_path=output_path,
                width=w,
                height=h,
                duration=script.target_duration,
            )
        else:
            # Pattern B/C: 이미지 시퀀스를 영상으로 조립
            self._assemble_from_images(
                image_paths=visuals.asset_paths,
                audio_path=audio.merged_path,
                srt_path=audio.subtitle_srt_path,
                script=script,
                output_path=output_path,
                width=w,
                height=h,
            )

        logger.info("최종 영상 렌더링 완료: %s (%dx%d)", output_path, w, h)
        return output_path

    def _assemble_from_video(
        self,
        video_path: Path,
        audio_path: Path | None,
        srt_path: Path | None,
        output_path: Path,
        width: int,
        height: int,
        duration: int,
    ):
        """영상 클립 + 오디오 합성"""
        video = ffmpeg.input(str(video_path))

        # 리사이즈 (세로/가로 규격 맞춤)
        video = video.filter("scale", width, height)
        video = video.filter("setsar", 1)

        if audio_path and audio_path.exists():
            audio = ffmpeg.input(str(audio_path))
            # 오디오 길이를 영상에 맞춤
            audio = audio.filter("atrim", duration=duration)
            output = ffmpeg.output(
                video, audio, str(output_path),
                vcodec="libx264",
                acodec="aac",
                preset="fast",
                t=duration,
                y=None,
            )
        else:
            output = ffmpeg.output(
                video, str(output_path),
                vcodec="libx264",
                preset="fast",
                t=duration,
                y=None,
            )

        output.run(quiet=True, overwrite_output=True)

    def _assemble_from_images(
        self,
        image_paths: list[Path],
        audio_path: Path | None,
        srt_path: Path | None,
        script: VideoScript,
        output_path: Path,
        width: int,
        height: int,
    ):
        """이미지 시퀀스 → 영상 조립 (씬별 duration 적용)"""
        if not image_paths:
            raise ValueError("시각 에셋이 없습니다")

        # 씬별 duration에 맞는 concat 파일 생성
        concat_path = output_path.parent / "concat.txt"
        lines = []
        for i, (img, scene) in enumerate(zip(image_paths, script.scenes)):
            abs_path = img.resolve().as_posix()
            lines.append(f"file '{abs_path}'")
            lines.append(f"duration {scene.duration_sec}")

        # 마지막 이미지 반복 (ffmpeg concat 요구사항)
        abs_last = image_paths[-1].resolve().as_posix()
        lines.append(f"file '{abs_last}'")
        concat_path.write_text("\n".join(lines), encoding="utf-8")

        # FFmpeg 조립
        total_duration = sum(s.duration_sec for s in script.scenes)
        video = ffmpeg.input(str(concat_path), f="concat", safe=0)
        video = video.filter("scale", width, height)
        video = video.filter("fps", fps=30)

        streams = [video]
        out_kwargs = {
            "vcodec": "libx264",
            "pix_fmt": "yuv420p",
            "preset": "fast",
            "t": total_duration,
        }

        if audio_path and audio_path.exists():
            # BGM을 영상 길이만큼 루프
            audio = ffmpeg.input(str(audio_path), stream_loop=-1)
            audio = audio.filter("atrim", duration=total_duration)
            streams.append(audio)
            out_kwargs["acodec"] = "aac"

        # 자막 오버레이 (filter chain에 통합)
        if srt_path and srt_path.exists():
            theme = get_theme(script.color_preset)
            spec = FORMAT_SPECS[script.format]
            font_size = spec["subtitle_font_size"]
            # Windows 경로 이스케이프 문제 회피: 상대경로 사용
            try:
                srt_rel = srt_path.relative_to(Path.cwd()).as_posix()
            except ValueError:
                srt_rel = srt_path.as_posix()
            force_style = f"FontSize={font_size},PrimaryColour=&H00{theme.text[1:]}&,Bold=1"
            streams[0] = streams[0].filter(
                "subtitles", srt_rel, force_style=force_style,
            )

        output = ffmpeg.output(
            *streams, str(output_path), **out_kwargs, y=None,
        )
        output.run(quiet=True, overwrite_output=True)
