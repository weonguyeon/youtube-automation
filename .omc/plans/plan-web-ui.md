# Web UI Dashboard 계획서

## 목표
YouTube 자동화 파이프라인을 웹에서 관리하는 대시보드 구축

## 기술 스택
- **Backend**: FastAPI + ProcessPoolExecutor (비동기 잡 실행)
- **Frontend**: React (Vite) + Tailwind CSS
- **실시간**: SSE (Server-Sent Events) 진행상황 스트리밍
- **상태관리**: In-memory dict (MVP) → SQLite (추후)

## 핵심 설계 결정
1. 기존 `VideoPipeline.run()`을 그대로 래핑 — 파이프라인 코드 최소 수정
2. `pipeline/schema.py`의 Pydantic 모델을 API 스키마로 재사용
3. `pipeline/monitoring.py`에 callback 추가하여 SSE 진행 추적
4. `output/` 디렉토리를 정적 파일로 서빙

## 디렉토리 구조
```
web/
├── backend/
│   ├── app.py              # FastAPI 앱 + CORS + static
│   ├── routes/
│   │   ├── jobs.py         # 잡 생성/조회/삭제
│   │   ├── presets.py      # 패턴/포맷/컬러/엔진 프리셋
│   │   └── videos.py       # 영상 목록/스트리밍
│   ├── services/
│   │   └── job_manager.py  # 잡 큐 + 비동기 실행
│   └── models.py           # API 전용 Pydantic 모델
└── frontend/
    ├── src/
    │   ├── pages/           # Dashboard, CreateVideo, VideoGallery, Settings
    │   ├── components/      # JobCard, StageProgress, ColorPicker 등
    │   └── hooks/           # useSSE, useJobs
    └── package.json
```

## 구현 단계
- Phase 1: FastAPI 백엔드 MVP (잡 생성/조회 + 프리셋 API)
- Phase 2: React 프론트엔드 MVP (생성 폼 + 대시보드)
- Phase 3: SSE 실시간 진행 모니터링
- Phase 4: 영상 갤러리 + 미리보기
