# 체크리스트: YouTube Automation 개발

## Phase 0: 기획
- [x] 벤치마크 리서치 정리
- [x] 영상 패턴 6종 분류
- [x] 기술 아키텍처 설계 (순수 Python, n8n 제거)
- [x] 개발 로드맵 수립
- [x] GitHub 오픈소스 도구 리서치 (15개 도구)
- [x] 프롬프트 설계 (패턴별 + 자막 + 썸네일)
- [x] MVP 명세서 작성
- [x] 방향성 정의 (홍보채널→SaaS, 8색 프리셋, Claude CLI)
- [x] 영상 포맷 규격 정의 (S8/S15/L3/L5/L10)
- [x] 스킬 구조 셋팅 (모듈/클래스 설계) ✅ 21개 파일
- [ ] API 서비스 계정 생성 (ElevenLabs, YouTube 등)

## Phase 1: 숏폼 개발 (우선)

### Sprint 1: 기반 인프라
- [x] Python 프로젝트 초기화 (pyproject.toml)
- [x] Pydantic 스키마 정의 (대본 JSON, 포맷 규격)
- [x] 8색 컬러 프리셋 시스템
- [x] FFmpeg 래퍼 (ffmpeg-python)
- [x] VideoPipeline 오케스트레이터 클래스
- [x] Claude CLI 대본 생성 모듈

### Sprint 2: S8 × Pattern A (MVP)
- [x] CSV → bar_chart_race 차트 애니메이션 ✅
- [x] 8초/15초 규격 렌더링 (9:16, 1080x1920) ✅
- [x] FFmpeg 해상도/길이 보정 파이프라인 ✅
- [x] 8색 컬러 프리셋 적용 검증 ✅
- [x] 3대 렌더링 엔진 통합 (Manim/Remotion/AI Pipeline) ✅
- [x] CLI --engine 옵션 추가 ✅
- [x] 엔진별 폴백 렌더링 검증 ✅
- [x] BGM 자동 매칭 + 볼륨 조절 ✅ (6무드, 포맷별 볼륨, 루프+페이드)
- [x] SRT 자막 자동 생성 + 오버레이 ✅ (한글/영어)
- [x] 메타데이터 자동 생성 (Claude CLI) ✅ (제목/설명/태그 자동)
- [x] End-to-End 파이프라인 검증 ✅ (주제→대본→BGM→이미지→영상)
- [ ] YouTube 업로드 테스트

### Sprint 3: S8/S15 × Pattern B (텍스트 숏폼)
- [x] Claude CLI 대본 생성 (통제된 무작위성) ✅ prompt_pool.py
- [x] ElevenLabs TTS 연동 ✅ tts_engine.py (API 키 미설정 시 폴백)
- [x] 자막 자동 생성 (Whisper local) ✅ audio_mixer.py (Whisper 미설치 시 스크립트 기반 폴백)
- [x] 이미지 생성 (Flux) + 로컬 인포그래픽 카드 폴백 ✅ text_shorts.py
- [x] S8/S15 통합 렌더링 ✅ E2E 테스트 통과

### Sprint 4: S8/S15 × Pattern C + 품질관리
- [ ] 무음 인포그래픽 (슬라이드 렌더러)
- [ ] 텍스트 유사도 검사 프리업로드 필터
- [ ] 에러 모니터링
- [ ] 멀티플랫폼 배포 (TikTok/Reels)

## Phase 2: 롱폼 확장
- [ ] L3/L5 × Pattern B (텍스트)
- [ ] L3/L5/L10 × Pattern D (벡터 인포그래픽)
- [ ] L5/L10 × Pattern E (화이트보드)
- [ ] 에셋 라이브러리 구축

## Phase 3: 고급 + 웹사이트
- [ ] Pattern F: 3D 인체
- [ ] FastAPI 백엔드
- [ ] Next.js 프론트엔드 (색상 선택 UI)
- [ ] 비동기 렌더링 큐 (Celery)
