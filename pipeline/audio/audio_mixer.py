"""오디오 생성 모듈 - TTS + BGM 믹싱

Pattern A/C: BGM만 (내레이션 없음)
Pattern B/D/E/F: TTS 음성 + BGM
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import ffmpeg as ffmpeg_lib

from pipeline.config import ASSETS_DIR
from pipeline.schema import FORMAT_SPECS, BgmMood, VideoScript

logger = logging.getLogger(__name__)


@dataclass
class AudioResult:
    merged_path: Path | None = None
    voice_path: Path | None = None
    bgm_path: Path | None = None
    subtitle_srt_path: Path | None = None
    duration_sec: float = 0.0


class AudioMixer:
    """오디오 생성 + BGM 믹싱"""

    def __init__(self):
        self._tts_engine = None

    def _get_tts_engine(self):
        if self._tts_engine is None:
            from pipeline.audio.tts_engine import TTSEngine
            self._tts_engine = TTSEngine()
        return self._tts_engine

    def generate(self, script: VideoScript, output_dir: Path) -> AudioResult:
        result = AudioResult()
        spec = FORMAT_SPECS[script.format]
        duration = script.target_duration

        # BGM 선택
        result.bgm_path = self._select_bgm(script.audio.bgm_mood)

        if script.audio.has_narration:
            # TTS 생성 (ElevenLabs → edge-tts 자동 폴백)
            result.voice_path = self._generate_tts(script, output_dir)

            if result.voice_path and result.voice_path.exists():
                # Whisper로 정확한 타임스탬프 자막 생성
                whisper_srt = self._generate_whisper_srt(result.voice_path, output_dir)
                if whisper_srt:
                    result.subtitle_srt_path = whisper_srt
                else:
                    # 폴백: 스크립트 기반 SRT
                    result.subtitle_srt_path = self._generate_srt(script, output_dir)

                # 음성 길이에 맞춰 duration 조정
                voice_duration = self._get_audio_duration(result.voice_path)
                if voice_duration:
                    duration = max(duration, voice_duration + 0.5)

                bgm_vol = spec["bgm_volume_with_voice"]
                result.merged_path = self._mix_audio(
                    result.voice_path, result.bgm_path, bgm_vol, duration, output_dir
                )
            else:
                logger.warning("TTS 미생성 — BGM만 사용")
                result.subtitle_srt_path = self._generate_srt(script, output_dir)
                bgm_vol = spec["bgm_volume_no_voice"]
                result.merged_path = self._adjust_bgm(
                    result.bgm_path, bgm_vol, duration, output_dir
                )
        else:
            # BGM만 사용 (볼륨 조절 + 길이 맞춤)
            result.subtitle_srt_path = self._generate_srt(script, output_dir)
            bgm_vol = spec["bgm_volume_no_voice"]
            result.merged_path = self._adjust_bgm(
                result.bgm_path, bgm_vol, duration, output_dir
            )

        result.duration_sec = duration
        logger.info("오디오 생성 완료: %.1f초 (BGM: %s)", result.duration_sec, script.audio.bgm_mood.value)
        return result

    def _select_bgm(self, mood: BgmMood) -> Path:
        """BGM 무드에 맞는 파일 선택"""
        bgm_dir = ASSETS_DIR / "bgm"
        # 무드별 BGM 매칭 (mp3, wav 모두 지원)
        candidates = list(bgm_dir.glob(f"{mood.value}*.*"))
        if not candidates:
            candidates = list(bgm_dir.glob("*.mp3")) + list(bgm_dir.glob("*.wav"))
        if not candidates:
            raise FileNotFoundError(f"BGM 파일 없음: {bgm_dir}")
        return candidates[0]

    def _generate_tts(self, script: VideoScript, output_dir: Path) -> Path | None:
        """ElevenLabs TTS로 음성 생성"""
        tts = self._get_tts_engine()
        return tts.generate_full_narration(
            scenes=script.scenes,
            voice_style=script.audio.voice_style,
            output_dir=output_dir,
        )

    def _generate_whisper_srt(self, voice_path: Path, output_dir: Path) -> Path | None:
        """Whisper로 음성에서 타임스탬프 자막 추출"""
        srt_path = output_dir / "subtitles.srt"
        try:
            import whisper

            model = whisper.load_model("small")
            result = model.transcribe(
                str(voice_path),
                language="ko",
                word_timestamps=True,
            )

            lines = []
            for i, segment in enumerate(result["segments"], 1):
                start = self._format_srt_time(segment["start"])
                end = self._format_srt_time(segment["end"])
                text = segment["text"].strip()
                if text:
                    lines.append(f"{i}")
                    lines.append(f"{start} --> {end}")
                    lines.append(text)
                    lines.append("")

            srt_path.write_text("\n".join(lines), encoding="utf-8")
            logger.info("Whisper 자막 생성: %d개 세그먼트", len(result["segments"]))
            return srt_path

        except ImportError:
            logger.warning("whisper 미설치 — 스크립트 기반 SRT 사용")
            return None
        except Exception as e:
            logger.warning("Whisper 실패: %s — 스크립트 기반 SRT 폴백", e)
            return None

    def _generate_srt(self, script: VideoScript, output_dir: Path) -> Path:
        """대본 기반 자막 SRT 파일 생성"""
        srt_path = output_dir / "subtitles.srt"
        lines = []
        current_time = 0.0

        for i, scene in enumerate(script.scenes, 1):
            if not scene.subtitle:
                current_time += scene.duration_sec
                continue

            start = self._format_srt_time(current_time)
            end = self._format_srt_time(current_time + scene.duration_sec)
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(scene.subtitle.replace("**", ""))
            lines.append("")
            current_time += scene.duration_sec

        srt_path.write_text("\n".join(lines), encoding="utf-8")
        return srt_path

    def _get_audio_duration(self, audio_path: Path) -> float | None:
        """오디오 파일 길이 조회"""
        try:
            probe = ffmpeg_lib.probe(str(audio_path))
            return float(probe["format"]["duration"])
        except Exception:
            return None

    def _adjust_bgm(
        self, bgm: Path, volume: float, duration: float, output_dir: Path
    ) -> Path:
        """BGM 볼륨 조절 + 길이 맞춤 (루프)"""
        adjusted_path = output_dir / "bgm_adjusted.wav"
        (
            ffmpeg_lib
            .input(str(bgm), stream_loop=-1)
            .filter("volume", volume)
            .filter("atrim", duration=duration)
            .filter("afade", type="in", duration=1.0)
            .filter("afade", type="out", start_time=max(0, duration - 2.0), duration=2.0)
            .output(str(adjusted_path), acodec="pcm_s16le", y=None)
            .run(quiet=True, overwrite_output=True)
        )
        logger.info("BGM 볼륨 조절: %.0f%%, %.1f초", volume * 100, duration)
        return adjusted_path

    def _mix_audio(
        self, voice: Path, bgm: Path, bgm_volume: float, duration: float, output_dir: Path
    ) -> Path:
        """음성 + BGM 볼륨 조절하여 믹싱"""
        merged_path = output_dir / "merged_audio.wav"

        voice_input = ffmpeg_lib.input(str(voice))
        bgm_input = (
            ffmpeg_lib
            .input(str(bgm), stream_loop=-1)
            .filter("volume", bgm_volume)
            .filter("atrim", duration=duration)
        )

        (
            ffmpeg_lib
            .filter([voice_input, bgm_input], "amix", inputs=2, duration="first")
            .output(str(merged_path), acodec="pcm_s16le", y=None)
            .run(quiet=True, overwrite_output=True)
        )
        logger.info("오디오 믹싱 완료: 음성 + BGM(%.0f%%)", bgm_volume * 100)
        return merged_path

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
