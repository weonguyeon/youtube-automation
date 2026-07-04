# Web UI 맥락 노트

## 기존 코드 핵심 연동점
- `orchestrator.py:73-81` — `VideoPipeline.run()` 시그니처 (topic, pattern, format, color, engine, upload, csv_path)
- `orchestrator.py:24-29` — `PipelineResult` (video_id, video_path, upload_url, errors, success)
- `schema.py:18-101` — Pattern, VideoFormat, ColorPreset, RenderEngine Enum 정의
- `monitoring.py:67-131` — PipelineMonitor (start_stage/end_stage, JSON 리포트 저장)
- `colors.py:143-155` — list_presets() 이미 UI-ready
- `config.py:22-53` — Settings 클래스 (.env 기반)
- `main.py:27-118` — CLI 진입점 (API가 동일 파라미터 매핑)

## 제약 조건
- VideoPipeline.run()은 동기 함수 → ProcessPoolExecutor로 비동기 래핑 필수
- AI 이미지 생성 + FFmpeg 렌더링에 30-120초 소요
- output/{video_id}/ 구조로 결과물 저장됨
- 로컬 개발 시 Claude MAX 토큰 사용 (API 아님)

## 주의사항
- pipeline/ 코드는 최소한만 수정 (monitoring.py callback 추가 정도)
- .env 파일에 민감한 API 키 — Settings 페이지에서 마스킹 표시
