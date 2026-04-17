# GitHub 오픈소스 도구 리서치 결과

> 조사일: 2026-04-17

---

## 핵심 도구 TOP 15 (Star 순)

| # | 프로젝트 | Stars | 카테고리 | 활용 포인트 |
|---|----------|-------|----------|-------------|
| 1 | **3b1b/manim** | 86,078 | 애니메이션 엔진 | Python 코드로 고품질 설명 애니메이션 생성 |
| 2 | **MoneyPrinterTurbo** | 55,843 | E2E 영상 자동화 | AI 대본→소재→편집→자막→음성 전체 자동화 참조 |
| 3 | **remotion-dev/remotion** | 43,645 | React 영상 생성 | 컴포넌트 기반 템플릿 + 데이터 바인딩 대량 렌더링 |
| 4 | **ManimCommunity/manim** | 37,817 | 애니메이션 엔진 | 커뮤니티 버전, 프로덕션 적합 |
| 5 | **MoneyPrinterV2** | 29,816 | Shorts+업로드 | YouTube 업로드 자동화 + Twitter 봇 포함 |
| 6 | **lowlighter/metrics** | 16,476 | SVG 인포그래픽 | 플러그인 기반 인포그래픽 생성 아키텍처 참조 |
| 7 | **Zulko/moviepy** | 14,542 | Python 영상 편집 | 클립 합성, 텍스트 오버레이, 트랜지션 |
| 8 | **FujiwaraChoki/MoneyPrinter** | 13,105 | Shorts 자동 생성 | MoviePy 기반 숏폼 파이프라인 |
| 9 | **kkroening/ffmpeg-python** | 10,988 | FFmpeg 래퍼 | 영상 조립 핵심 도구 |
| 10 | **linyqh/NarratoAI** | 8,830 | AI 내레이션 | AI 음성 자동 삽입 |
| 11 | **ShortGPT** | 7,265 | 숏폼 프레임워크 | 다국어 지원, 한국어 자막/더빙 자동화 |
| 12 | **MoneyPrinterPlus** | 6,093 | 로컬 TTS 특화 | ChatTTS/GPTSoVITS 로컬 음성, API 비용 $0 |
| 13 | **dexplo/bar_chart_race** | 1,448 | 차트 애니메이션 | DataFrame → Bar Chart Race MP4 자동 생성 |
| 14 | **AI-Faceless-Video-Gen** | 411 | AI 아바타 | 토킹 페이스 영상 자동 생성 |
| 15 | **remotion-video-skill** | 189 | Claude 통합 | **Claude Code용 Remotion 영상 생성 스킬** |

---

## 카테고리별 상세

### 1. 영상 자동 생성 파이프라인 (E2E)

#### harry0703/MoneyPrinterTurbo ★55,843
- **URL:** https://github.com/harry0703/MoneyPrinterTurbo
- **기능:** AI로 원클릭 고화질 쇼트 영상 생성 (대본→소재→편집→자막→음성)
- **활용:** 전체 파이프라인 아키텍처 참조. 우리 시스템의 골격 설계에 가장 직접적 참고

#### FujiwaraChoki/MoneyPrinter ★13,105
- **URL:** https://github.com/FujiwaraChoki/MoneyPrinter
- **기능:** MoviePy 활용 YouTube Shorts 자동 생성
- **활용:** MoviePy 기반 영상 조립 코드 참조

#### linyqh/NarratoAI ★8,830
- **URL:** https://github.com/linyqh/NarratoAI
- **기능:** AI 모델로 영상 자동 해설 + 편집
- **활용:** 인포그래픽 영상에 AI 내레이션 자동 추가 모듈 참조

### 2. 애니메이션 엔진 (핵심)

#### 3b1b/manim ★86,078
- **URL:** https://github.com/3b1b/manim
- **기능:** 3Blue1Brown의 수학 설명 애니메이션 엔진. Python 코드로 고품질 영상 생성
- **활용:** 데이터 시각화, 차트, 숫자 변화 애니메이션. 인포그래픽 씬의 코어 렌더러
- **주의:** 오리지널 버전은 API가 불안정

#### ManimCommunity/manim ★37,817
- **URL:** https://github.com/ManimCommunity/manim
- **기능:** 커뮤니티 유지보수 버전. pip 설치, 안정 API, 좋은 문서
- **활용:** 프로덕션 파이프라인에는 이 버전 사용 추천

#### remotion-dev/remotion ★43,645
- **URL:** https://github.com/remotion-dev/remotion
- **기능:** React로 영상 프로그래밍. 컴포넌트 기반 + 데이터 바인딩
- **활용:** 인포그래픽 템플릿 대량 렌더링. Canva 대체 가능

### 3. 차트 애니메이션

#### dexplo/bar_chart_race ★1,448
- **URL:** https://github.com/dexplo/bar_chart_race
- **기능:** DataFrame → Bar Chart Race MP4/GIF 자동 생성
- **활용:** Pattern A (데이터 비주얼라이제이션)의 핵심 도구. 즉시 사용 가능

#### vizzuhq/ipyvizzu ★969
- **URL:** https://github.com/vizzuhq/ipyvizzu
- **기능:** 차트 간 전환 애니메이션 (morphing)
- **활용:** 여러 차트가 자연스럽게 변환되는 데이터 스토리텔링 시퀀스

#### bchao1/chart-race-react ★525
- **URL:** https://github.com/bchao1/chart-race-react
- **기능:** React 컴포넌트로 Bar Chart Race 구현
- **활용:** Remotion과 결합하여 영상 렌더링

### 4. 영상 편집/조립

#### Zulko/moviepy ★14,542
- **URL:** https://github.com/Zulko/moviepy
- **기능:** Python 영상 편집 (자르기, 합치기, 오버레이, 트랜지션, 오디오)
- **활용:** ffmpeg-python보다 고수준 API. 후반 편집 자동화

#### kkroening/ffmpeg-python ★10,988
- **URL:** https://github.com/kkroening/ffmpeg-python
- **기능:** FFmpeg Python 바인딩. 복잡한 필터 체이닝
- **활용:** 최종 영상 조립 (씬 합치기, 오디오 트랙, 자막 삽입)

### 5. 인포그래픽 생성

#### lowlighter/metrics ★16,476
- **URL:** https://github.com/lowlighter/metrics
- **기능:** 30+ 플러그인 기반 SVG/PDF 인포그래픽 생성
- **활용:** 플러그인 아키텍처 참조. 커스텀 데이터 소스용 인포그래픽 시스템

### 6. 화이트보드 애니메이션

#### yogendra-yatnalkar/storyboard-ai ★53
- **URL:** https://github.com/yogendra-yatnalkar/storyboard-ai
- **기능:** 텍스트→화이트보드 스타일 애니메이션 자동 생성
- **활용:** Pattern E (화이트보드) 참조

#### maksimKorzh/automated-whiteboard ★8
- **URL:** https://github.com/maksimKorzh/automated-whiteboard
- **기능:** Python + OpenCV로 화이트보드 드로잉 과정 녹화
- **활용:** 차트/다이어그램 그리는 과정을 화이트보드 스타일로 녹화

---

## 추천 기술 스택 조합

### Option A: Python 중심 (추천 — 빠른 개발)
```
manim (씬 애니메이션)
  + bar_chart_race (차트 애니메이션)
  + moviepy (영상 조립)
  + ffmpeg-python (최종 렌더링)
  + MoneyPrinterTurbo (파이프라인 참조)
```

### Option B: React/웹 중심 (고품질 템플릿)
```
Remotion (인포그래픽 템플릿 + 대량 렌더링)
  + chart-race-react (차트 컴포넌트)
  + FFmpeg (후처리)
```

### Option C: 하이브리드 (최적 균형)
```
Python 파이프라인 (오케스트레이션 + 대본 + 오디오)
  + manim/bar_chart_race (데이터 씬 렌더링)
  + Remotion (복잡한 인포그래픽 템플릿)
  + moviepy + ffmpeg (최종 조립)
```

---

## 추가 발견: 영상 자동화 파이프라인

### MoneyPrinterV2 ★29,816
- **URL:** https://github.com/FujiwaraChoki/MoneyPrinterV2
- **기능:** Shorts 자동 생성 + YouTube 업로드 자동화 + Twitter 봇 + 제휴 마케팅
- **활용:** 업로드 자동화 코드 참조. 멀티플랫폼 배포 로직

### ShortGPT ★7,265
- **URL:** https://github.com/RayVentura/ShortGPT
- **기능:** GPT 기반 스크립트, 자동 자막, 배경 소싱, **다국어 지원**
- **활용:** 한국어 더빙/자막 자동화. 번역 파이프라인 참조

### MoneyPrinterPlus ★6,093
- **URL:** https://github.com/ddean2009/MoneyPrinterPlus
- **기능:** ChatTTS, faster-whisper, GPTSoVITS **로컬 음성 모델** 지원. Stable Diffusion/ComfyUI AI 이미지. 틱톡 자동 업로드
- **활용:** API 비용 $0 로컬 TTS. 완전 로컬 파이프라인 구축 가능

### remotion-video-skill ★189 (핵심!)
- **URL:** https://github.com/wshuyi/remotion-video-skill
- **기능:** **Claude Code용 Remotion 영상 생성 스킬**. AI 에이전트가 코드 작성으로 영상 자동 렌더링
- **활용:** 우리 프로젝트에 직접 통합 가능! Claude CLI로 대본 생성 → Remotion 스킬로 영상 렌더링

### MoneyPrinterAICreate ★284
- **URL:** https://github.com/q1uki/MoneyPrinterAICreate
- **기능:** Wan2.1 AI 텍스트-to-비디오 통합. AI가 스토리보드 → 동적 영상 생성
- **활용:** 차세대 파이프라인 방향. 정적 이미지 → AI 동영상 클립 전환

---

## Canva API 참고사항

Canva 관련 오픈소스 래퍼는 사실상 부재.
Canva Connect API 직접 연동보다는 **Remotion이 Canva를 대체하는 가장 현실적인 대안**.
React 컴포넌트로 디자인 템플릿을 만들면 Canva의 Bulk Create와 동등한 기능을 코드로 구현 가능.

---

## 최종 추천: 우리 프로젝트 최적 조합

### 핵심 스택 (Python 중심 + Claude CLI)
```
[대본]     Claude CLI (MAX) → JSON 대본
[음성]     ElevenLabs API (or 로컬: ChatTTS/GPTSoVITS)
[차트]     bar_chart_race + ipyvizzu + manim
[영상편집] moviepy + ffmpeg-python
[자막]     faster-whisper (로컬)
[업로드]   YouTube Data API v3
```

### 확장 스택 (웹사이트 배포 시)
```
[대본]     Claude API → JSON
[템플릿]   Remotion (React 기반 인포그래픽)
[렌더링]   Remotion Lambda (병렬 렌더링)
[큐]       Celery + Redis
[백엔드]   FastAPI
[프론트]   Next.js
```

### 특별 참고: remotion-video-skill
Claude Code에서 직접 Remotion 영상을 생성하는 스킬.
개발 단계에서 Claude CLI + 이 스킬을 결합하면
**"주제를 말하면 Claude가 알아서 영상을 만드는"** 워크플로우 가능.
