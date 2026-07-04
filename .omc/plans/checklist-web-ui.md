# Web UI 체크리스트 — ALL COMPLETE

## Phase 1: FastAPI 백엔드 MVP
- [x] pyproject.toml에 fastapi, uvicorn 의존성 추가
- [x] web/backend/app.py — FastAPI 앱 생성
- [x] web/backend/models.py — API 요청/응답 모델
- [x] web/backend/services/job_manager.py — 잡 매니저
- [x] web/backend/routes/jobs.py — POST/GET/DELETE /api/jobs
- [x] web/backend/routes/presets.py — GET /api/presets/*
- [x] web/backend/routes/videos.py — GET /api/videos
- [x] 백엔드 동작 확인 (TestClient 전체 API 통과)

## Phase 2: React 프론트엔드 MVP
- [x] Vite + React + Tailwind 프로젝트 초기화
- [x] API 클라이언트 (lib/api.ts)
- [x] Dashboard 페이지 (잡 목록 + 통계)
- [x] CreateVideo 페이지 (생성 폼 — 패턴/포맷/컬러/엔진 선택)
- [x] VideoGallery 페이지 (그리드 + 플레이어)
- [x] StageProgress 컴포넌트, JobCard 컴포넌트
- [x] TypeScript 타입체크 + Vite 빌드 통과
- [x] 백엔드 서버 스모크 테스트 통과

## Phase 3: 실시간 진행 모니터링
- [x] PipelineMonitor에 매 Stage 완료 시 중간 리포트 저장 (_save_report)
- [x] SSE endpoint 구현 (GET /api/jobs/{id}/sse — 파일 폴링 기반)
- [x] useJobSSE 훅 (EventSource 구독, 완료 시 자동 종료)
- [x] JobCard에 SSE 연동 (running 잡 실시간 Stage 업데이트)
- [x] StageProgress에 currentStage 애니메이션 표시
- [x] Dashboard 폴링 제거 → SSE 완료 콜백으로 교체
- [x] TypeScript 타입체크 + Vite 빌드 통과
- [x] SSE 엔드포인트 테스트 통과

## Phase 4: 마무리
- [x] Settings 페이지 (API 키 상태, deploy mode, 브랜드 컬러 등)
- [x] Settings 백엔드 API (GET/PUT /api/settings — .env 읽기/쓰기)
- [x] 에러 핸들링 (API 자동 재시도 + Toast 알림)
- [x] 프론트-백 통합 테스트 (10개 전체 통과)
- [x] 전체 TypeScript + Vite 빌드 통과
