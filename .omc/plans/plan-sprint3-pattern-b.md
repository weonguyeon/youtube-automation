# Sprint 3: Pattern B 텍스트 숏폼 개발 계획

## 목표
Pattern B (텍스트 인포그래픽 숏폼)의 E2E 파이프라인 완성

## 변경 범위

### 1. ElevenLabs TTS 연동 (`pipeline/audio/tts_engine.py` 신규)
- ElevenLabs API v1 연동
- 씬별 narration → MP3 음성 파일 생성
- voice_style에 따른 stability/similarity_boost 조절
- API 키 미설정 시 graceful skip (BGM only 폴백)

### 2. Whisper 자막 (`pipeline/audio/audio_mixer.py` 수정)
- TTS 생성된 음성에서 Whisper로 정확한 타임스탬프 추출
- 기존 스크립트 기반 SRT와 Whisper SRT 선택 로직

### 3. Flux 이미지 생성 (`pipeline/visual/text_shorts.py` 수정)
- BFL Flux API 연동 (flux-pro-1.1)
- API 실패 시 로컬 인포그래픽 카드 폴백 (engine_ai_pipeline의 로직 재사용)

### 4. audio_mixer.py 수정
- _generate_tts()에서 TTSEngine 호출
- TTS → Whisper → SRT 파이프라인 연결

## 기술 결정
- ElevenLabs: multilingual_v2 모델, 한국어 지원
- Whisper: openai-whisper 로컬 (small 모델) — API 비용 절감
- Flux: BFL API, 실패 시 PIL 로컬 카드 폴백
