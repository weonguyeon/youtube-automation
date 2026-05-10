# YouTube Automation Project

## 개요
인포그래픽/애니메이션 기반 페이스리스(Faceless) 유튜브 채널 영상 자동 생산 파이프라인

## 기술 스택
- **Python 3.13+** — 파이프라인 코어
- **FFmpeg 8.x** — 영상 렌더링/조립
- **edge-tts** — 무료 TTS (ElevenLabs 유료 폴백)
- **Whisper** — 음성→자막 타임스탬프
- **Replicate (Flux)** — AI 이미지 생성 (Pexels/로컬 카드 폴백)
- **Pydantic v2** — 대본 JSON 스키마 검증
- **Claude CLI/API** — 대본 생성

## CLI 사용법
```bash
# 주제 지정
yt-auto --topic "주제" --pattern B --format S15 --engine ai_pipeline

# 트렌드 자동 선택
yt-auto --category ai_tech --pattern B --format S15

# 컬러/엔진 지정
yt-auto --topic "주제" --color ocean_blue --engine manim

# 멀티플랫폼 익스포트 (영상 생성 후 자동으로 플랫폼별 mp4 추가 생성)
yt-auto --topic "주제" --platforms youtube_shorts,tiktok,instagram_reels

# 배치 모드 (config/batch.example.yaml 참고)
yt-auto --batch config/batch.example.yaml
```

## 멀티플랫폼 익스포트
지원 플랫폼: `youtube_shorts`, `youtube_long`, `tiktok`, `instagram_reels`,
`instagram_feed`, `x_twitter`. 각 플랫폼의 비율/최대 길이에 맞춰
`output/{video_id}/exports/{platform}.mp4` 로 자동 변환.
원본 비율은 letterbox(검은 패드)로 보존 — 콘텐츠 손실 없음.
업로드 자동화는 미포함 (수동/예약 업로드용 산출물 생성만).

## 배치 모드
YAML/JSON 파일에 `defaults` + `jobs` 정의 후 `--batch` 로 일괄 실행.
배치 리포트는 `output/_batches/batch-{date}.json` 에 저장.

## 디렉토리 구조
```
youtube-automation/
├── pipeline/
│   ├��─ main.py                # CLI 진입점
│   ├── orchestrator.py        # 5단계 파이프라인 엔진
│   ├── schema.py              # Pydantic 모델 (VideoScript, Scene 등)
│   ├── config.py              # 환경변수/설정 관리
│   ├── colors.py              # 8색 컬러 프리셋
│   ├── monitoring.py          # 실행 시간 + JSON 리포트
│   ├── ideation/              # Stage 1: 기획/대본
│   │   ├── script_writer.py   # Claude CLI/API 대본 생성
│   │   ├── prompt_pool.py     # 패턴별 프롬프트 (A~E)
│   │   ├── quality_filter.py  # 유사도 검사
│   │   └── trend_collector.py # 트렌드 키워드 수집
│   ├── audio/                 # Stage 2: ��디오
│   │   ├── tts_engine.py      # ElevenLabs → edge-tts 폴백
│   │   └── audio_mixer.py     # TTS + BGM + Whisper SRT
│   ├── visual/                # Stage 3: 시각 에셋
│   │   ├── base_renderer.py   # 렌더러 인터페이스 + 팩토리
│   │   ├── engine_ai_pipeline.py  # Flux → Pexels → 로컬 카드
│   │   ├── engine_manim.py    # Manim 차트/애니메이션
│   │   ├── engine_remotion.py # Remotion React 템플릿
│   │   ├── data_viz.py        # Pattern A
│   │   ├── text_shorts.py     # Pattern B
│   │   ├── silent_infographic.py  # Pattern C
│   │   ├── vector_infographic.py  # Pattern D
│   │   └── whiteboard.py      # Pattern E
│   ├── assembly/              # Stage 4: 조립
│   │   ├── ffmpeg_renderer.py # FFmpeg 영상 조립
│   │   └── thumbnail.py       # 썸네일 자동 생성
│   └── publish/               # Stage 5: 배포
│       └── youtube_uploader.py
├── web/                         # 웹 대시보드
│   ├── backend/
│   │   ├── app.py              # FastAPI 앱 (CORS, static mount)
│   │   ├── models.py           # API Pydantic 모델
│   │   ├── routes/             # jobs, presets, videos 라우트
│   │   └── services/
│   │       └── job_manager.py  # ProcessPoolExecutor 기반 비동기 잡
│   └── frontend/               # React (Vite) + Tailwind CSS
│       └── src/
│           ├── pages/          # Dashboard, CreateVideo, VideoGallery
│           ├── components/     # JobCard, StageProgress
│           └── lib/api.ts      # API 클라이언트
├── assets/bgm/                # 6종 BGM (mood별)
├── config/.env.example        # API 키 템플릿
├── tests/                     # E2E 테스트
├── output/                    # 생성된 영상
└── docs/                      # 기획 문서
```

## 이미지 생성 폴백 체인
1. **Replicate (Flux)** — `FLUX_API_KEY` 설정 시
2. **Pexels 스톡** — `PEXELS_API_KEY` 설정 시
3. **로컬 카드** — PIL 기반 인포그래픽 (항상 동작)

## 웹 대시보드 실행
```bash
# 백엔드 (FastAPI)
cd youtube-automation
python -m uvicorn web.backend.app:app --reload --port 8000

# 프론트엔드 (Vite dev server → localhost:5173, API proxy → :8000)
cd web/frontend
npm run dev
```

### API 엔드포인트
- `POST /api/jobs` — 새 영상 생성 (platforms 배열 옵션)
- `POST /api/jobs/batch` — 배치 잡 생성 (defaults + jobs)
- `GET /api/jobs` — 잡 목록
- `GET /api/jobs/batches` — 배치 그룹 목록
- `GET /api/presets/{patterns,formats,colors,engines,platforms}` — 프리셋
- `GET /api/videos` — 완성된 영상 갤러리
- `GET /api/videos/{id}/stream` — 영상 스트리밍
- `GET /api/videos/{id}/thumbnail` — 썸네일
- `GET /api/jobs/{id}/sse` — SSE 실시간 진행 스트리밍
- `GET /api/settings` — 설정 조회
- `PUT /api/settings` — 설정 업데이트 (.env 반영)

## 규칙
- 영상 소스는 실사 촬영 없이 인포그래픽/디자인 기반만 사용
- 자막과 프롬프트는 자동 생성 필수
- 패턴별 버전 분리하여 독립 개발
- 테스트는 15초(S15) 포맷으로 통일
- 로컬 개발 시 Claude MAX 토큰 사용 (API 아님)
