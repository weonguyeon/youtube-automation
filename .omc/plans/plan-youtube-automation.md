# 계획서: YouTube Faceless Automation Engine

## 목표
인포그래픽/애니메이션 기반 페이스리스 유튜브 채널의 영상 자동 생산 파이프라인 구축

## 변경 범위
- 새 프로젝트 디렉토리: `mins-project/youtube-automation/`
- 6개 영상 패턴별 독립 모듈 개발
- 5단계 파이프라인 (기획→오디오→시각→조립→배포)

## 기술 결정 사항
- 코어: Python 3.13+
- 오케스트레이션: n8n 셀프호스트
- 렌더링: FFmpeg (단순) + Remotion (복잡) 하이브리드
- TTS: ElevenLabs API
- 대본: Claude API (JSON 구조화)
- Phase 1 우선 개발: Pattern A(데이터 비즈), B(텍스트 숏폼), C(무음 인포그래픽)

## 현재 단계
기획 완료 → Sprint 1 (기반 인프라) 대기 중
