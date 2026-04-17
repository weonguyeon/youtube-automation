"""TTS 엔진 — ElevenLabs (유료) → edge-tts (무료) 자동 폴백

우선순위:
1. ElevenLabs API (API 키 설정 시)
2. edge-tts (무료, Microsoft Edge 음성, 한국어 지원)
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from pipeline.config import settings
from pipeline.schema import Scene, VoiceStyle

logger = logging.getLogger(__name__)

# voice_style → ElevenLabs 파라미터 매핑
VOICE_STYLE_PARAMS: dict[VoiceStyle, dict] = {
    VoiceStyle.ENERGETIC: {"stability": 0.3, "similarity_boost": 0.8, "style": 0.7},
    VoiceStyle.CALM: {"stability": 0.7, "similarity_boost": 0.6, "style": 0.3},
    VoiceStyle.DRAMATIC: {"stability": 0.4, "similarity_boost": 0.9, "style": 0.8},
    VoiceStyle.CURIOUS: {"stability": 0.5, "similarity_boost": 0.7, "style": 0.5},
    VoiceStyle.NARRATIVE: {"stability": 0.6, "similarity_boost": 0.7, "style": 0.4},
}

# voice_style → edge-tts 음성 매핑 (한국어)
EDGE_VOICE_MAP: dict[VoiceStyle, str] = {
    VoiceStyle.ENERGETIC: "ko-KR-InJoonNeural",    # 남성, 활기찬
    VoiceStyle.CALM: "ko-KR-SunHiNeural",          # 여성, 차분한
    VoiceStyle.DRAMATIC: "ko-KR-InJoonNeural",     # 남성, 극적
    VoiceStyle.CURIOUS: "ko-KR-SunHiNeural",       # 여성, 호기심
    VoiceStyle.NARRATIVE: "ko-KR-InJoonNeural",    # 남성, 내레이션
}

DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # ElevenLabs Adam


class TTSEngine:
    """TTS 음성 생성 (ElevenLabs → edge-tts 자동 폴백)"""

    def __init__(self):
        self._eleven_client = None

    def generate_full_narration(
        self,
        scenes: list[Scene],
        voice_style: VoiceStyle,
        output_dir: Path,
    ) -> Path | None:
        """전체 씬의 narration을 하나의 음성 파일로 생성"""
        narration_parts = [s.narration for s in scenes if s.narration]
        if not narration_parts:
            return None

        full_text = " ".join(narration_parts)
        output_path = output_dir / "voice.mp3"

        # 1순위: ElevenLabs
        if settings.elevenlabs_api_key:
            result = self._generate_elevenlabs(full_text, voice_style, output_path)
            if result:
                return result

        # 2순위: edge-tts (무료)
        result = self._generate_edge_tts(full_text, voice_style, output_path)
        if result:
            return result

        logger.warning("TTS 생성 실패 — BGM만 사용")
        return None

    def generate_scene_audio(
        self,
        scene: Scene,
        voice_style: VoiceStyle,
        output_path: Path,
    ) -> Path | None:
        """단일 씬의 narration을 TTS로 변환"""
        if not scene.narration:
            return None

        # 1순위: ElevenLabs
        if settings.elevenlabs_api_key:
            result = self._generate_elevenlabs(scene.narration, voice_style, output_path)
            if result:
                return result

        # 2순위: edge-tts
        return self._generate_edge_tts(scene.narration, voice_style, output_path)

    # ── ElevenLabs ──────────────────────────────────────

    def _get_eleven_client(self):
        if self._eleven_client is None:
            try:
                from elevenlabs.client import ElevenLabs
                self._eleven_client = ElevenLabs(api_key=settings.elevenlabs_api_key)
            except ImportError:
                logger.warning("elevenlabs 패키지 미설치 — edge-tts로 폴백")
                return None
        return self._eleven_client

    def _generate_elevenlabs(
        self, text: str, voice_style: VoiceStyle, output_path: Path
    ) -> Path | None:
        try:
            client = self._get_eleven_client()
            if client is None:
                return None

            voice_id = settings.elevenlabs_voice_id or DEFAULT_VOICE_ID
            params = VOICE_STYLE_PARAMS.get(voice_style, VOICE_STYLE_PARAMS[VoiceStyle.NARRATIVE])

            audio = client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings={
                    "stability": params["stability"],
                    "similarity_boost": params["similarity_boost"],
                    "style": params["style"],
                    "use_speaker_boost": True,
                },
                output_format="mp3_44100_128",
            )

            with open(output_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            logger.info("[ElevenLabs] TTS 생성: %d자 → %s", len(text), output_path.name)
            return output_path

        except Exception as e:
            logger.warning("[ElevenLabs] TTS 실패: %s — edge-tts로 폴백", e)
            return None

    # ── edge-tts (무료) ─────────────────────────────────

    def _generate_edge_tts(
        self, text: str, voice_style: VoiceStyle, output_path: Path
    ) -> Path | None:
        try:
            import edge_tts

            voice = EDGE_VOICE_MAP.get(voice_style, "ko-KR-InJoonNeural")

            async def _run():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(str(output_path))

            asyncio.run(_run())

            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info("[edge-tts] TTS 생성: %d자, 음성=%s → %s", len(text), voice, output_path.name)
                return output_path

            return None

        except ImportError:
            logger.warning("edge-tts 미설치: pip install edge-tts")
            return None
        except Exception as e:
            logger.error("[edge-tts] TTS 실패: %s", e)
            return None
