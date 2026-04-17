# 유튜브 자동화 개발 기획서

> 프로젝트명: YouTube Faceless Automation Engine
> 작성일: 2026-04-17
> 목표: 인포그래픽/애니메이션 기반 페이스리스 영상을 자동 생산하는 파이프라인 구축

---

## 1. 프로젝트 비전

**"대본만 넣으면 완성 영상이 나오는 공장"**

- 실사 촬영 0% — 모든 영상은 인포그래픽/디자인 기반
- 자막, 프롬프트, 음성 모두 자동 생성
- 패턴별 템플릿 시스템으로 다양한 장르 대응
- 숏폼(60초) + 롱폼(8~15분) 모두 지원

---

## 2. 영상 패턴 분류 (버전별 독립 개발)

리서치 결과를 기반으로 **6개 패턴**으로 분류하고, 난이도/ROI 순서대로 개발한다.

### Phase 1 — 즉시 개발 가능 (완전자동화 목표)

#### Pattern A: 데이터 비주얼라이제이션 (Data Viz)
- **형태**: 막대차트 레이스, 파이차트 변화, 퍼센트 게이지
- **벤치마크**: WatchData, Reigarw Comparisons
- **핵심**: 데이터(CSV) → 차트 애니메이션 → 영상 자동 렌더링
- **내레이션**: 없음 (BGM only) → 글로벌 트래픽 가능
- **난이도**: ★☆☆☆☆
- **자동화율**: 95%+
- **도구**: Python (matplotlib/plotly) + Flourish + FFmpeg

#### Pattern B: 텍스트 인포그래픽 숏폼 (Text-Heavy Shorts)
- **형태**: 큰 자막 + 빠른 컷 + 픽토그램/스톡이미지
- **벤치마크**: 1분만, 명언 쇼츠 채널들
- **핵심**: AI 대본 → TTS → 자막 오버레이 + 이미지 매칭
- **내레이션**: TTS (ElevenLabs/Google)
- **난이도**: ★★☆☆☆
- **자동화율**: 90%
- **도구**: Canva Bulk Create / Remotion + FFmpeg

#### Pattern C: 무음 인포그래픽 (Silent Infographic)
- **형태**: 차트/그래프/분할 이미지 + 텍스트만
- **벤치마크**: 틱톡 지식 큐레이션 채널들
- **핵심**: 통계 데이터 → 인포그래픽 이미지 생성 → 슬라이드쇼
- **내레이션**: 없음
- **난이도**: ★☆☆☆☆
- **자동화율**: 95%+
- **도구**: Canva API / Python PIL + FFmpeg

### Phase 2 — 반자동화 (에셋 선구축 필요)

#### Pattern D: 2D 벡터 인포그래픽 (Vector Infographic)
- **형태**: 캐릭터 + 배경 + 아이콘 조합 애니메이션
- **벤치마크**: The Infographics Show, 지식해적단
- **핵심**: 모듈형 에셋 라이브러리 → 대본에 맞춰 자동 조립
- **내레이션**: TTS + 자막
- **난이도**: ★★★☆☆
- **자동화율**: 70~80%
- **도구**: Vyond API / Remotion + 커스텀 에셋

#### Pattern E: 화이트보드 애니메이션 (Whiteboard)
- **형태**: 가상 손이 그리는 드로잉 + 내레이션
- **벤치마크**: After Skool, Practical Psychology
- **핵심**: 대본 → SVG 에셋 배치 → 드로잉 패스 자동 생성
- **내레이션**: TTS (감정선 풍부한 고급 보이스)
- **난이도**: ★★★☆☆
- **자동화율**: 60~70%
- **도구**: Doodly API / VideoScribe + FFmpeg

### Phase 3 — 고급 자동화 (3D/고품질)

#### Pattern F: 3D 인체/과학 (3D Body Science)
- **형태**: 3D 인체 모델 + 장기/골격 애니메이션
- **벤치마크**: Helix2
- **핵심**: 고정 3D 모델 + 대본별 카메라/하이라이트 변경
- **내레이션**: TTS + 자막
- **난이도**: ★★★★☆
- **자동화율**: 50~60%
- **도구**: Blender Python API / Three.js + Remotion

---

## 3. 공통 파이프라인 (5단계)

모든 패턴이 공유하는 자동화 흐름:

```
[1단계] 기획/대본   →  [2단계] 오디오   →  [3단계] 시각 에셋
   ↓                      ↓                    ↓
트렌드 키워드 수집    TTS 음성 생성        이미지/영상 생성
AI 대본 작성         BGM 매칭             스타일 파라미터 고정
JSON 구조화          효과음 삽입           에셋 라이브러리 조회
   ↓                      ↓                    ↓
         ──────→  [4단계] 조립/렌더링  ←──────
                      ↓
              FFmpeg/Shotstack
              자막 하드코딩
              9:16 or 16:9 리사이징
                      ↓
              [5단계] 배포
                      ↓
              YouTube API 예약업로드
              TikTok/Reels 동시 배포
              메타데이터 자동 생성
```

---

## 4. 기술 스택 선정

### 코어 엔진 (GitHub 오픈소스 리서치 반영)
| 레이어 | 선택 | Stars | 용도 |
|--------|------|-------|------|
| 오케스트레이션 | **Python (VideoPipeline)** | APScheduler | 순수 Python 파이프라인 |
| 대본 생성 | **Claude CLI (MAX)** | Claude API (배포용) | 구조화된 JSON 대본 |
| TTS | **ElevenLabs API** | — | 고품질 한국어/영어 음성 |
| 이미지 생성 | **Flux-pro / Leonardo AI** | — | 인포그래픽 스타일 고정 |
| 씬 애니메이션 | **ManimCommunity/manim** | 37.8k | 차트/그래프/숫자 애니메이션 렌더링 |
| 차트 레이스 | **dexplo/bar_chart_race** | 1.4k | DataFrame → 차트 레이스 MP4 |
| 차트 전환 | **vizzuhq/ipyvizzu** | 969 | 차트 간 morphing 애니메이션 |
| 템플릿 영상 | **remotion-dev/remotion** | 43.6k | React 기반 인포그래픽 대량 렌더링 |
| 영상 편집 | **Zulko/moviepy** | 14.5k | 클립 합성, 오버레이, 트랜지션 |
| FFmpeg 래퍼 | **kkroening/ffmpeg-python** | 11k | 최종 인코딩/자막/합성 |
| 자막 생성 | **Whisper (local)** | — | 타임스탬프 기반 SRT |
| 배포 | **YouTube Data API v3** | — | 예약 업로드 |
| 멀티배포 | **Blotato** / 커스텀 | — | TikTok/Reels 동시 배포 |
| 참조 아키텍처 | **MoneyPrinterTurbo** | 55.8k | E2E 파이프라인 설계 참고 |
| 내레이션 참조 | **NarratoAI** | 8.8k | AI 음성 자동 삽입 참고 |

### 데이터 저장
| 용도 | 선택지 |
|------|--------|
| 대본/메타데이터 | Google Sheets / Supabase |
| 에셋 파일 | Google Drive / AWS S3 |
| 워크플로우 상태 | n8n 내장 DB / SQLite |

---

## 5. 개발 로드맵

### Sprint 1 (Week 1~2): 기반 인프라
- [ ] 프로젝트 구조 세팅 (Python)
- [ ] 공통 데이터 스키마 정의 (Pydantic 모델)
- [ ] 8색 컬러 프리셋 시스템 구현
- [ ] FFmpeg 래퍼 유틸리티 개발 (ffmpeg-python)
- [ ] VideoPipeline 오케스트레이터 클래스 설계
- [ ] Claude CLI 연동 대본 생성 모듈
- [ ] API 키 연동 (ElevenLabs, YouTube)

### Sprint 2 (Week 3~4): Pattern A — 데이터 비주얼라이제이션
- [ ] CSV → 차트 애니메이션 파이프라인
- [ ] Flourish/Plotly 연동 또는 커스텀 차트 렌더러
- [ ] BGM 자동 매칭 모듈
- [ ] 9:16 / 16:9 자동 리사이징
- [ ] YouTube 업로드 자동화 테스트

### Sprint 3 (Week 5~6): Pattern B — 텍스트 인포그래픽 숏폼
- [ ] AI 대본 생성 (Claude API → JSON)
- [ ] ElevenLabs TTS 연동
- [ ] Canva Bulk Create 또는 Remotion 템플릿
- [ ] 자막 자동 생성 (Whisper)
- [ ] 통합 렌더링 파이프라인

### Sprint 4 (Week 7~8): Pattern C + 품질관리
- [ ] 무음 인포그래픽 패턴 구현
- [ ] 통제된 무작위성 모듈 (프롬프트 변형)
- [ ] 텍스트 유사도 검사 프리업로드 필터
- [ ] 에러 모니터링 대시보드
- [ ] 멀티플랫폼 배포 (TikTok/Reels)

### Sprint 5+ (Week 9~): Phase 2 패턴 확장
- [ ] Pattern D: 에셋 라이브러리 구축 + Vyond/Remotion
- [ ] Pattern E: 화이트보드 SVG 자동 드로잉
- [ ] Pattern F: 3D 모델 연동 (Blender Python)

---

## 6. 수익화 전략

### 니치 선정 (우선순위)
1. **데이터 비교/통계** — 완전자동, 글로벌, 빠른 론칭
2. **AI/생산성 튜토리얼** — 높은 RPM + 제휴마케팅
3. **역사 What If** — 소재 무한, 인포그래픽 적합
4. **동기부여/철학** — 고정 시청자, 몰아보기 유도

### 수익 다각화
- YouTube 광고 수익 (AdSense)
- 제휴 마케팅 (AI 도구/SaaS 추천)
- 디지털 상품 (템플릿, 워크플로우 판매)
- 채널 자체를 자산으로 매각

---

## 7. 리스크 관리

| 리스크 | 대응 전략 |
|--------|-----------|
| 재사용 콘텐츠 판정 | 통제된 무작위성 + 프롬프트 변형 풀 |
| TTS 거부감 | ElevenLabs 고급 보이스 + 감정선 조절 |
| 에셋 저작권 | CC0/상업용 라이선스만 사용 |
| API 비용 과다 | 로컬 대안 병행 (Whisper local, Ollama) |
| 알고리즘 변경 | 멀티플랫폼 분산 + 80/20 인간개입 |

---

## 8. 성공 지표 (KPI)

| 지표 | 목표 (3개월) |
|------|-------------|
| 영상 생산 속도 | 숏폼 10개/일, 롱폼 2개/주 |
| 영상당 제작 시간 | 숏폼 < 5분, 롱폼 < 30분 |
| 인간 개입 비율 | < 20% (검수/기획만) |
| 구독자 | 1만+ |
| 월 조회수 | 100만+ |
