# MVP (Minimum Viable Product) 명세서

> 가장 빠르게 검증 가능한 최소 기능 단위 정의

---

## MVP 목표

**"CSV 데이터 하나를 넣으면 차트 레이스 숏폼 영상이 자동으로 만들어진다"**

Pattern A (데이터 비주얼라이제이션)를 MVP로 선정한 이유:
1. 내레이션 불필요 → TTS 연동 생략 가능
2. 자막 불필요 → 자막 엔진 생략 가능
3. bar_chart_race 라이브러리로 즉시 구현 가능
4. 글로벌 타겟 → 언어 제약 없음
5. 자동화율 95%+ → 인간 개입 최소

---

## MVP 기능 범위

### 포함 (In Scope)
- [x] CSV 파일 입력 → DataFrame 변환
- [x] bar_chart_race로 차트 애니메이션 렌더링
- [x] 9:16 (숏폼) / 16:9 (롱폼) 자동 리사이징
- [x] 로열티프리 BGM 자동 삽입
- [x] 메타데이터 자동 생성 (제목, 설명, 태그)
- [x] YouTube API로 예약 업로드

### 제외 (Out of Scope — 이후 Sprint)
- AI 대본 생성
- TTS 음성
- 자막 오버레이
- 이미지 생성 (Flux)
- 멀티플랫폼 배포
- n8n 워크플로우

---

## MVP 파이프라인 흐름

```
[입력]
CSV 파일 (데이터)
  + 주제명 (string)
  + chart_type (bar_race | pie | gauge)

    ↓

[1] 데이터 로드 & 검증
    pandas.read_csv()
    → 컬럼 검증
    → 결측값 처리

    ↓

[2] 차트 애니메이션 렌더링
    bar_chart_race.bar_chart_race(df, ...)
    → MP4 출력 (1920x1080 기본)

    ↓

[3] 리사이징 & BGM 합성
    ffmpeg-python으로:
    → 9:16 크롭/리사이징
    → BGM 오디오 트랙 믹싱
    → 제목 텍스트 오버레이 (상단)

    ↓

[4] 메타데이터 생성
    Claude API 호출:
    → 주제명 + 데이터 요약 → 제목/설명/태그 JSON

    ↓

[5] YouTube 업로드
    YouTube Data API v3
    → 예약 시간 설정
    → 썸네일 자동 설정

    ↓

[출력]
YouTube에 게시된 영상 URL
```

---

## MVP 기술 요구사항

### 필수 패키지
```
python >= 3.13
bar-chart-race >= 0.2
pandas >= 2.2
ffmpeg-python >= 0.2
anthropic >= 0.40  (Claude API)
google-api-python-client >= 2.0  (YouTube API)
google-auth-oauthlib >= 1.0
pillow >= 10.0  (썸네일 생성)
```

### 필수 시스템 도구
```
ffmpeg >= 6.0
```

### API 키
```
ANTHROPIC_API_KEY=   # Claude API (메타데이터 생성)
YOUTUBE_CLIENT_ID=   # YouTube Data API
YOUTUBE_CLIENT_SECRET=
```

---

## MVP 파일 구조

```
youtube-automation/
├── pipeline/
│   ├── __init__.py
│   ├── config.py           # 환경변수 관리
│   ├── schema.py           # Pydantic 모델
│   ├── data_viz.py         # 차트 렌더링 (핵심)
│   ├── audio_mixer.py      # BGM 합성
│   ├── metadata_gen.py     # AI 메타데이터 생성
│   ├── youtube_upload.py   # 업로드 모듈
│   └── main.py             # CLI 진입점
├── assets/
│   └── bgm/
│       ├── epic_01.mp3
│       ├── upbeat_01.mp3
│       └── calm_01.mp3
├── data/
│   └── sample.csv          # 테스트 데이터
├── output/                 # 렌더링 결과물
├── config/
│   └── .env
├── requirements.txt
└── CLAUDE.md
```

---

## MVP CLI 사용법 (목표)

```bash
# 기본 사용
python -m pipeline.main --csv data/gdp_by_country.csv --topic "세계 GDP 순위 변화"

# 옵션 지정
python -m pipeline.main \
  --csv data/kpop_views.csv \
  --topic "K-Pop 그룹 유튜브 조회수 레이스" \
  --format shorts \
  --bgm epic \
  --upload \
  --schedule "2026-04-18T18:00:00"

# 배치 실행 (여러 CSV)
python -m pipeline.main --batch data/batch_config.yaml
```

---

## MVP 성공 기준

| 기준 | 목표 |
|------|------|
| CSV → 완성 영상 | 5분 이내 |
| 영상 품질 | 1080p, 부드러운 차트 애니메이션 |
| BGM 동기화 | 영상 길이에 맞춰 자동 루프/페이드 |
| YouTube 업로드 | 자동 예약 업로드 성공 |
| 메타데이터 | SEO 최적화된 제목/설명/태그 자동 생성 |

---

## MVP 이후 확장 계획

```
MVP (Pattern A: 차트 레이스)
  ↓ Sprint 3
Pattern B 추가 (텍스트 숏폼: + TTS + 자막 + 이미지 생성)
  ↓ Sprint 4
Pattern C 추가 (무음 인포그래픽: + 슬라이드 렌더러)
  ↓ Sprint 4
품질관리 모듈 (유사도 검사, 프롬프트 변형)
  ↓ Sprint 5+
Phase 2 패턴 (벡터, 화이트보드, 3D)
  ↓
n8n 워크플로우 → 완전 무인 운영
```
