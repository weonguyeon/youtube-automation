"""ElevenLabs TTS 엔진

씬별 narration → MP3 음성 파일 생성.
API 키 미설정 시 None 반환 (BGM only 폴백).
"""

from __future__ import annotations

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

# 한국어 기본 음성 (ElevenLabs multilingual)
DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam (multilingual_v2)


class TTSEngine:
    """ElevenLabs TTS 음성 생성"""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from elevenlabs.client import ElevenLabs
                self._client = ElevenLabs(api_key=settings.elevenlabs_api_key)
            except ImportError:
                raise ImportError("elevenlabs 패키지 필요: pip install elevenlabs")
        return self._client

    def generate_scene_audio(
        self,
        scene: Scene,
        voice_style: VoiceStyle,
        output_path: Path,
    ) -> Path | None:
        """단일 씬의 narration을 TTS로 변환"""
        if not scene.narration:
            return None

        if not settings.elevenlabs_api_key:
            logger.warning("ELEVENLABS_API_KEY 미설정 — TTS 건너뜀")
            return None

        voice_id = settings.elevenlabs_voice_id or DEFAULT_VOICE_ID
        params = VOICE_STYLE_PARAMS.get(voice_style, VOICE_STYLE_PARAMS[VoiceStyle.NARRATIVE])

        try:
            client = self._get_client()
            audio = client.text_to_speech.convert(
                voice_id=voice_id,
                text=scene.narration,
                model_id="eleven_multilingual_v2",
                voice_settings={
                    "stability": params["stability"],
                    "similarity_boost": params["similarity_boost"],
                    "style": params["style"],
                    "use_speaker_boost": True,
                },
                output_format="mp3_44100_128",
            )

            # 스트리밍 응답을 파일로 저장
            with open(output_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            logger.info("TTS 생성: scene_%d (%d자) → %s", scene.scene_id, len(scene.narration), output_path.name)
            return output_path

        except Exception as e:
            logger.error("TTS 생성 실패 (scene_%d): %s", scene.scene_id, e)
            return None

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

        if not settings.elevenlabs_api_key:
            logger.warning("ELEVENLABS_API_KEY 미설정 — TTS 건너뜀")
            return None

        voice_id = settings.elevenlabs_voice_id or DEFAULT_VOICE_ID
        params = VOICE_STYLE_PARAMS.get(voice_style, VOICE_STYLE_PARAMS[VoiceStyle.NARRATIVE])

        try:
            client = self._get_client()
            audio = client.text_to_speech.convert(
                voice_id=voice_id,
                text=full_text,
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

            logger.info("전체 TTS 생성: %d자 → %s", len(full_text), output_path.name)
            return output_path

        except Exception as e:
            logger.error("전체 TTS 생성 실패: %s", e)
            return None
