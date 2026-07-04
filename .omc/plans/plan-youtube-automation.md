# 계획서: YouTube Faceless Automation Engine

## 목표
인포그래픽/애니메이션 기반 페이스리스 유튜브 채널의 영상 자동 생산 파이프라인 구축

## 변경 범위
- 프로젝트 디렉토리: `projects/youtube-automation/`
- 6개 영상 패턴별 독립 모듈 개발
- 5단계 파이프라인 (기획→오디오→시각→조립→배포)

## 기술 결정 사항
- 코어: Python 3.13+
- 렌더링: FFmpeg (조립) + Manim/Remotion/AI Pipeline (시각)
- TTS: edge-tts (무료) → ElevenLabs (유료 폴백)
- 이미지: Replicate Flux → Pexels → 로컬 카드 (3단 폴백)
- 대본: Claude CLI (개발) / Claude API (배포)
- 자막: Whisper (음성→SRT) → 스크립트 기반 폴백

## 현재 단계 (2026-04-17)
Sprint 1~3 완료 → Sprint 4 (품질관리 + 배포) 진행 중

### 완료
- [x] 프로젝트 구조 + pyproject.toml + CLI
- [x] Pydantic 스키마 (VideoScript, Scene, 모든 Enum)
- [x] 8색 컬러 프리셋 시스템
- [x] 대본 생성 (Claude CLI/API + 프롬프트 풀 A~E + 유사도 필터)
- [x] TTS (ElevenLabs → edge-tts 자동 폴백)
- [x] 오디오 믹싱 (TTS + BGM + Whisper/스크립트 SRT)
- [x] 시각 렌더러 5종 (DataViz, TextShorts, SilentInfographic, VectorInfographic, Whiteboard)
- [x] 엔진 렌더러 3종 (Manim, Remotion, AI Pipeline)
- [x] AI Pipeline 이미지 생성 (Flux → Pexels → 로컬 카드 3단 폴백)
- [x] FFmpeg 영상 조립 (이미지 시퀀스 + 영상 클립)
- [x] 썸네일 자동 생성
- [x] 트렌드 키워드 수집 (Google Trends + 시드 카테고리)
- [x] 모니터링 (실행 시간 + JSON 리포트)
- [x] E2E 테스트 (Stage 2~4 검증 통과)

### 남은 작업
- [ ] YouTube Data API v3 실 연동
- [ ] TikTok/Reels 멀티플랫폼 배포
- [ ] 배치 실행 모드 (여러 영상 연속 생성)
- [ ] 에러 모니터링 대시보드
- [ ] 웹 UI (영상 생성 요청/미리보기)
