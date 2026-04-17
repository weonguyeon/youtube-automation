# Sprint 3 체크리스트

## Step 1: TTS 엔진
- [x] pipeline/audio/tts_engine.py 생성 (ElevenLabs API)
- [x] audio_mixer.py에서 tts_engine 호출 연결
- [x] API 키 미설정 시 graceful skip 확인

## Step 2: Whisper 자막
- [x] audio_mixer.py에 Whisper 기반 SRT 생성 추가
- [x] Whisper 미설치 시 스크립트 기반 SRT 폴백

## Step 3: 이미지 생성
- [x] text_shorts.py에 Flux API 연동
- [x] 로컬 폴백 카드 품질 개선 (engine_ai_pipeline 로직 통합)

## Step 4: 통합 테스트
- [x] Pattern B × S15 E2E 테스트 (output/32de2709)
- [x] Pattern B × S8 E2E 테스트 (output/eb1ed32f)
- [x] API 키 없을 때 폴백 동작 확인 (BGM only + 로컬 카드)
