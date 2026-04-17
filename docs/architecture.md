# 기술 아키텍처 설계서

> YouTube Faceless Automation Engine — System Architecture

---

## 1. 시스템 전체 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (Python)                     │
│         VideoPipeline 클래스 + APScheduler + 에러 핸들링      │
└────┬──────────┬──────────┬──────────┬──────────┬────────┘
     │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│ Stage 1  ││ Stage 2  ││ Stage 3  ││ Stage 4  ││ Stage 5  │
│ Ideation ││ Audio    ││ Visual   ││ Assembly ││ Publish  │
│          ││          ││          ││          ││          │
│ Claude   ││ Eleven   ││ Flux/    ││ FFmpeg/  ││ YouTube  │
│ API      ││ Labs     ││ Canva    ││ Remotion ││ API v3   │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
     │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────┐
│              STORAGE LAYER                               │
│  Google Sheets (메타) │ S3/GDrive (파일) │ SQLite (상태)  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 대본 JSON 스키마 (공통 포맷)

모든 패턴이 이 스키마를 입력으로 사용:

```json
{
  "video_id": "uuid",
  "pattern": "A|B|C|D|E|F",
  "format": "shorts|longform",
  "aspect_ratio": "9:16|16:9",
  "language": "ko|en",
  "metadata": {
    "title": "영상 제목",
    "description": "설명글",
    "tags": ["태그1", "태그2"],
    "scheduled_at": "2026-04-18T18:00:00+09:00"
  },
  "scenes": [
    {
      "scene_id": 1,
      "duration_sec": 3,
      "narration": "도입부 텍스트 (Hook)",
      "visual_prompt": "flat 2d infographic showing...",
      "subtitle": "화면에 표시될 자막",
      "transition": "fade|cut|slide",
      "asset_type": "generated|stock|template|chart",
      "style_params": {
        "color_palette": "#1a1a2e,#16213e,#0f3460",
        "font": "Pretendard Bold",
        "layout": "center_text|split_screen|full_image"
      }
    }
  ],
  "audio": {
    "voice_id": "elevenlabs_voice_id",
    "voice_style": "narrative|energetic|calm",
    "bgm_mood": "epic|lofi|tense|upbeat",
    "bgm_volume": 0.15
  }
}
```

---

## 3. Stage별 상세 설계

### Stage 1: Ideation & Scripting

```
[트렌드 수집]                    [대본 생성]
VidIQ API ──┐                   ┌── Claude API
Reddit API ──┼── 키워드 풀 ──→  │   (구조화 프롬프트)
Google Trends┘   (Sheets)       └── JSON 대본 출력
                                      │
                                [품질 필터]
                                ├── 유사도 검사 (이전 대본과 비교)
                                ├── 프롬프트 변형 (Hook 유형 랜덤)
                                └── 인간 검수 큐 (선택적)
```

**프롬프트 변형 풀 (통제된 무작위성):**
```python
HOOK_TYPES = [
    "question",      # "~하면 어떻게 될까?"
    "statistic",     # "전 세계 인구의 0.001%만..."
    "contrast",      # "A는 ~인데, B는..."
    "challenge",     # "이것을 아는 사람은 거의 없다"
    "timeline",      # "2020년, 세계는..."
]
```

### Stage 2: Audio Generation

```
[음성 생성]                      [사운드 디자인]
대본.narration ──→ ElevenLabs ──→ voice.mp3
                   API              │
                                    ├── Whisper API ──→ subtitles.srt
                                    │                   (타임스탬프)
                                    │
BGM_MOOD ──→ 음악 라이브러리 ──→ bgm.mp3
             (Storyblocks/         │
              로열티프리)           │
                                    ▼
                              merged_audio.mp3
                              (음성 + BGM 믹싱)
```

### Stage 3: Visual Asset Generation

```
[패턴별 분기]

Pattern A (Data Viz):
  CSV 데이터 ──→ Python matplotlib/plotly ──→ chart_animation.mp4

Pattern B (Text Shorts):
  visual_prompt ──→ Flux API ──→ background.png
  subtitle ──→ 자막 레이어 생성 ──→ subtitle_overlay.png

Pattern C (Silent Infographic):
  데이터 ──→ Canva API / PIL ──→ infographic_slides.png[]

Pattern D (Vector Infographic):
  visual_prompt ──→ 에셋 라이브러리 검색 ──→ 캐릭터 + 배경 조립
                 ──→ Remotion 컴포넌트 렌더 ──→ scene.mp4

Pattern E (Whiteboard):
  visual_prompt ──→ SVG 에셋 매핑 ──→ Doodly/커스텀 드로잉 렌더

Pattern F (3D Body):
  visual_prompt ──→ Blender Python ──→ 3D 렌더 + 카메라 무브
```

### Stage 4: Assembly & Rendering

```
                  ┌── voice.mp3
                  ├── bgm.mp3
                  ├── subtitles.srt
INPUT ────────→   ├── visual_assets[] (png/mp4)
                  └── style_params (font, color, layout)
                       │
                       ▼
              ┌─────────────────┐
              │   RENDER ENGINE  │
              │                  │
              │  Option A:       │
              │  FFmpeg Pipeline │
              │  (스크립트 기반)  │
              │                  │
              │  Option B:       │
              │  Remotion        │
              │  (React 컴포넌트)│
              │                  │
              │  Option C:       │
              │  Shotstack API   │
              │  (클라우드 렌더)  │
              └────────┬────────┘
                       │
                       ▼
              final_video.mp4
              (1080x1920 or 1920x1080)
```

**FFmpeg 핵심 커맨드 패턴:**
```bash
# 이미지 시퀀스 + 오디오 + 자막 합성
ffmpeg -i visual_%03d.png \
       -i merged_audio.mp3 \
       -vf "subtitles=subs.srt:force_style='FontName=Pretendard,FontSize=24,Bold=1'" \
       -c:v libx264 -preset fast \
       -s 1080x1920 \
       -t $AUDIO_DURATION \
       output.mp4
```

### Stage 5: Auto-Publishing

```
final_video.mp4 ──┬──→ YouTube Data API v3 ──→ 예약 업로드
                  │     (제목, 설명, 태그, 썸네일)
metadata.json ────┤
                  ├──→ TikTok API ──→ 동시 배포
                  │
                  └──→ Instagram Reels API ──→ 동시 배포

[스케줄링]
├── 숏폼: 매일 오후 6시, 9시 (2회)
├── 롱폼: 수/토 오전 10시 (주 2회)
└── 플랫폼별 최적 시간대 자동 조절
```

---

## 4. 디렉토리 구조 (구현)

```
youtube-automation/
├── pipeline/
│   ├── __init__.py
│   ├── config.py              # 환경변수, API 키 관리
│   ├── schema.py              # Pydantic 모델 (JSON 스키마)
│   ├── orchestrator.py        # 파이프라인 실행 엔진
│   │
│   ├── ideation/
│   │   ├── trend_collector.py # 트렌드 키워드 수집
│   │   ├── script_writer.py   # Claude API 대본 생성
│   │   ├── prompt_pool.py     # 프롬프트 변형 풀
│   │   └── quality_filter.py  # 유사도 검사 필터
│   │
│   ├── audio/
│   │   ├── tts_engine.py      # ElevenLabs TTS
│   │   ├── bgm_selector.py    # BGM 자동 매칭
│   │   └── audio_mixer.py     # 음성 + BGM 믹싱
│   │
│   ├── visual/
│   │   ├── base_renderer.py   # 렌더러 인터페이스
│   │   ├── data_viz.py        # Pattern A: 차트 렌더러
│   │   ├── text_shorts.py     # Pattern B: 텍스트 숏폼
│   │   ├── silent_infographic.py  # Pattern C
│   │   ├── vector_infographic.py  # Pattern D
│   │   ├── whiteboard.py      # Pattern E
│   │   └── body_3d.py         # Pattern F
│   │
│   ├── assembly/
│   │   ├── ffmpeg_renderer.py # FFmpeg 기반 조립
│   │   ├── remotion_renderer.py # Remotion 기반 (대안)
│   │   ├── subtitle_engine.py # 자막 생성/오버레이
│   │   └── thumbnail.py       # 썸네일 자동 생성
│   │
│   └── publish/
│       ├── youtube_uploader.py    # YouTube API v3
│       ├── tiktok_uploader.py     # TikTok 배포
│       └── scheduler.py          # 예약 스케줄링
│
├── templates/
│   ├── pattern_a/             # 차트 템플릿
│   ├── pattern_b/             # 텍스트 숏폼 템플릿
│   ├── pattern_c/             # 무음 인포그래픽
│   ├── pattern_d/             # 벡터 인포그래픽
│   ├── pattern_e/             # 화이트보드
│   └── pattern_f/             # 3D
│
├── assets/
│   ├── fonts/                 # 폰트 (Pretendard 등)
│   ├── icons/                 # 재사용 아이콘
│   ├── characters/            # 캐릭터 에셋
│   ├── backgrounds/           # 배경 에셋
│   └── bgm/                   # 로열티프리 BGM
│
├── config/
│   ├── .env                   # API 키 (gitignore)
│   ├── settings.yaml          # 채널 설정
│   └── schedules.yaml         # 업로드 스케줄
│
├── tests/
│   ├── test_script_writer.py
│   ├── test_tts.py
│   ├── test_renderer.py
│   └── test_pipeline.py
│
├── n8n/
│   └── workflows/             # n8n 워크플로우 JSON 백업
│
├── requirements.txt
├── pyproject.toml
└── CLAUDE.md
```

---

## 5. 렌더링 엔진 비교 (4종)

| 기준 | FFmpeg | MoviePy | Manim | Remotion |
|------|--------|---------|-------|----------|
| 언어 | CLI/Python | Python | Python | React/TS |
| 유연성 | 낮음 | 중간 | 높음 (수학/차트) | 최고 (UI 자유도) |
| 학습곡선 | 중간 | 낮음 | 중간 | 높음 |
| 텍스트/차트 | 제한적 | 중간 | 최고 | 자유로움 |
| 애니메이션 | 기초 | 기초 | 고급 (수학적) | CSS/Spring |
| 대량 렌더링 | 빠름 | 보통 | 보통 | Lambda 병렬 |
| 추천 패턴 | 최종 조립 | A/C (단순) | A (차트/데이터) | B/D (복잡 템플릿) |

**결론**: 하이브리드 전략
- **Manim** → Pattern A (데이터/차트 애니메이션 씬 렌더링)
- **MoviePy** → Pattern B/C (이미지+텍스트 슬라이드 조립)
- **Remotion** → Pattern D (복잡한 인포그래픽 템플릿)
- **FFmpeg** → 모든 패턴의 최종 인코딩/자막/오디오 합성

---

## 6. API 비용 추정 (월간)

| 서비스 | 용도 | 예상 사용량 | 월 비용 |
|--------|------|------------|---------|
| Claude API | 대본 생성 | 300건/월 | ~$30 |
| ElevenLabs | TTS | 300분/월 | ~$22 (Scale) |
| Flux-pro | 이미지 생성 | 1,000장/월 | ~$20 |
| YouTube API | 업로드 | 무료 | $0 |
| n8n Cloud | 오케스트레이션 | - | $20 (또는 셀프호스트 $0) |
| **합계** | | | **~$92/월** |

> 로컬 대안 활용 시 (Ollama + local Whisper + Canva 무료) → $22/월까지 절감 가능
