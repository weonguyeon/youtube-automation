# 대본 프롬프트 설계서

> 패턴별 Claude API 프롬프트 구조 + 자막/비주얼 프롬프트 자동 생성 설계

---

## 1. 공통 시스템 프롬프트

모든 패턴에 공유되는 기본 지시:

```
당신은 유튜브 영상 대본 전문 작가입니다.
반드시 아래 JSON 스키마에 맞춰 응답하세요.
마크다운이나 설명 텍스트 없이, 순수 JSON만 출력하세요.

규칙:
1. 각 scene의 narration은 자연스럽고 대화체로 작성
2. visual_prompt는 영어로 작성 (이미지 생성 AI용)
3. subtitle은 한국어로, 화면에 표시될 핵심 키워드만 (15자 이내)
4. Hook(첫 장면)은 3초 이내에 시청자를 사로잡아야 함
5. 총 duration_sec 합계가 target_duration을 초과하지 않도록
```

---

## 2. Pattern A: 데이터 비주얼라이제이션

### 용도
차트 레이스, 랭킹 변화, 통계 비교 영상

### 프롬프트 템플릿
```
[시스템 프롬프트 + 공통 규칙]

주제: {topic}
형식: 데이터 비교 영상 (차트 레이스 / 게이지 바 / 파이차트)
영상 길이: {target_duration}초
언어: {language}

다음 JSON 형식으로 대본을 생성하세요:
{
  "title": "유튜브 제목 (호기심 유발, 40자 이내)",
  "description": "유튜브 설명글 (SEO 최적화, 200자)",
  "tags": ["태그1", "태그2", ...],
  "chart_type": "bar_race|pie|gauge|line",
  "data_source": "사용할 데이터 출처 설명",
  "data": [
    {"label": "항목명", "values": {"2020": 100, "2021": 150, ...}},
    ...
  ],
  "bgm_mood": "epic|dramatic|upbeat|calm",
  "thumbnail_text": "썸네일에 들어갈 텍스트 (8자 이내)"
}

데이터는 실제 통계에 기반하되, 정확한 수치를 사용하세요.
최소 8개 이상의 비교 항목을 포함하세요.
```

### 특이사항
- 내레이션 없음 → narration/subtitle 필드 생략
- data 필드가 핵심 → bar_chart_race 라이브러리에 직접 입력
- BGM만 자동 매칭

---

## 3. Pattern B: 텍스트 인포그래픽 숏폼

### 용도
지식 전달, 명언, 팩트 체크, 리스트형 정보

### 프롬프트 템플릿
```
[시스템 프롬프트 + 공통 규칙]

주제: {topic}
형식: 숏폼 인포그래픽 (9:16 세로, 60초 이내)
톤: {tone} (충격적/유머/진지/호기심)

Hook 유형: {hook_type} (아래 중 랜덤 선택)
- question: 질문으로 시작 ("~하면 어떻게 될까?")
- statistic: 충격적 통계 ("전 세계 인구의 0.001%만...")
- contrast: 대비 ("A는 ~인데, B는...")
- challenge: 도전 ("이것을 아는 사람은 거의 없다")
- timeline: 시간축 ("2020년, 세계는...")

JSON 출력:
{
  "title": "유튜브 제목",
  "description": "설명글",
  "tags": [...],
  "scenes": [
    {
      "scene_id": 1,
      "duration_sec": 3,
      "narration": "내레이션 텍스트 (TTS용, 자연스러운 대화체)",
      "subtitle": "화면 자막 (핵심 키워드 15자 이내, 강조할 단어는 **볼드**)",
      "visual_prompt": "flat 2d infographic, minimalist, dark background, showing [구체적 묘사], vector style, no text",
      "transition": "cut|fade|zoom_in|slide_up",
      "visual_note": "화면 구성 메모 (레이아웃 힌트)"
    },
    ...
  ],
  "voice_style": "energetic|calm|dramatic|curious",
  "bgm_mood": "epic|lofi|tense|upbeat"
}

필수 규칙:
- scenes 6~10개 (60초 기준)
- 첫 scene(Hook)은 반드시 3초 이내
- visual_prompt는 반드시 영어, 구체적이고 일관된 스타일
- visual_prompt에 "no text, no words, no letters" 포함 (텍스트는 자막으로 별도 처리)
- narration의 총 글자 수 ≈ target_duration × 4 (한국어 기준 초당 ~4글자)
```

### 통제된 무작위성 적용
```python
import random

HOOK_TYPES = ["question", "statistic", "contrast", "challenge", "timeline"]
TONES = ["충격적", "유머", "진지", "호기심"]
VOICE_STYLES = ["energetic", "calm", "dramatic", "curious"]

def randomize_prompt_params():
    return {
        "hook_type": random.choice(HOOK_TYPES),
        "tone": random.choice(TONES),
        "voice_style": random.choice(VOICE_STYLES),
    }
```

---

## 4. Pattern C: 무음 인포그래픽

### 용도
통계 요약, 비교 차트, 인포그래픽 슬라이드쇼

### 프롬프트 템플릿
```
[시스템 프롬프트 + 공통 규칙]

주제: {topic}
형식: 무음 인포그래픽 (텍스트+차트만, 내레이션 없음)
영상 길이: {target_duration}초

JSON 출력:
{
  "title": "유튜브 제목",
  "description": "설명글",
  "tags": [...],
  "slides": [
    {
      "slide_id": 1,
      "duration_sec": 4,
      "headline": "슬라이드 제목 (20자 이내)",
      "body_text": "본문 텍스트 (50자 이내)",
      "data_visual": {
        "type": "bar|pie|number|comparison|timeline",
        "data": {"항목1": 65, "항목2": 35},
        "highlight": "항목1"
      },
      "visual_prompt": "clean infographic background, [색상/분위기]",
      "transition": "slide_left|fade|zoom"
    },
    ...
  ],
  "color_scheme": "dark|light|vibrant|pastel",
  "bgm_mood": "calm|ambient|none"
}

필수 규칙:
- 텍스트는 최소화, 숫자와 차트로 전달
- 각 슬라이드는 단일 팩트/비교에 집중
- 글로벌 타겟 가능하도록 숫자/기호 중심
```

---

## 5. Pattern D: 2D 벡터 인포그래픽 (Phase 2)

### 프롬프트 템플릿
```
[시스템 프롬프트 + 공통 규칙]

주제: {topic}
형식: 2D 벡터 인포그래픽 애니메이션 (롱폼 8~15분)

JSON 출력:
{
  "title": "유튜브 제목",
  "scenes": [
    {
      "scene_id": 1,
      "duration_sec": 15,
      "narration": "내레이션 (자연스러운 스토리텔링)",
      "subtitle": "핵심 자막",
      "visual_prompt": "2d vector illustration, flat design, [장면 묘사]",
      "characters": ["주인공", "조연"],
      "character_actions": ["standing", "pointing", "walking"],
      "background": "도시 야경|사무실|지도|우주",
      "overlay_elements": ["텍스트 박스", "화살표", "아이콘"],
      "camera_move": "pan_right|zoom_in|static"
    }
  ]
}

추가 규칙:
- characters는 에셋 라이브러리의 미리 정의된 캐릭터 ID 참조
- background는 재사용 가능한 카테고리 기반
- 스토리 전개: 도입(왜?)→전개(어떻게?)→절정(반전)→결론(교훈)
```

---

## 6. Pattern E: 화이트보드 (Phase 2)

### 프롬프트 템플릿
```
주제: {topic}
형식: 화이트보드 애니메이션 (5~10분)

JSON 출력:
{
  "scenes": [
    {
      "scene_id": 1,
      "duration_sec": 20,
      "narration": "설명 내레이션",
      "drawings": [
        {
          "type": "icon|text|diagram|arrow|character",
          "content": "그릴 대상 설명",
          "svg_keyword": "에셋 라이브러리 검색 키워드",
          "position": "center|left|right|top|bottom",
          "draw_duration_sec": 3
        }
      ],
      "board_action": "continue|clear|pan_right|zoom_in"
    }
  ]
}

규칙:
- 한 보드에 너무 많은 요소를 그리지 않음 (최대 5개)
- 텍스트 대신 상징적 메타포 그림 우선
- 복잡한 개념은 단계별로 하나씩 추가
```

---

## 7. 자막 자동 생성 규칙

### 숏폼 (9:16) 자막 스타일
```
위치: 화면 중앙 (세로 60% 지점)
폰트: Pretendard ExtraBold
크기: 60px (1080x1920 기준)
색상: #FFFFFF (흰색)
배경: 반투명 검정 (#000000, opacity 60%)
강조: 핵심 단어 노란색 (#FFD700)
최대 줄 수: 2줄
최대 글자 수: 줄당 12자
```

### 롱폼 (16:9) 자막 스타일
```
위치: 화면 하단 (세로 85% 지점)
폰트: Pretendard Bold
크기: 42px (1920x1080 기준)
색상: #FFFFFF
테두리: 2px #000000
최대 줄 수: 2줄
최대 글자 수: 줄당 20자
```

### 자막 타이밍 규칙
```python
# Whisper API 출력 → SRT 변환 시 적용
SUBTITLE_RULES = {
    "min_duration_sec": 0.8,    # 최소 표시 시간
    "max_duration_sec": 5.0,    # 최대 표시 시간
    "max_chars_per_line": 12,   # 숏폼 기준
    "gap_between_subs_ms": 100, # 자막 간 간격
    "highlight_keywords": True, # 핵심 키워드 색상 강조
}
```

---

## 8. 비주얼 프롬프트 스타일 가이드

### 일관성을 위한 고정 접미사
```python
STYLE_SUFFIXES = {
    "infographic": ", flat 2d vector infographic style, clean white background, minimalist, no text, no watermark",
    "dark_infographic": ", flat 2d vector infographic, dark navy background (#1a1a2e), neon accent colors, no text",
    "whiteboard": ", hand-drawn sketch style, black ink on white background, simple line art, no color",
    "3d_body": ", 3d medical illustration, anatomical cross-section, soft lighting, translucent skin, no text",
    "data_chart": ", clean data visualization, modern chart design, vibrant colors on dark background",
}
```

### 금지 키워드 (저작권/안전)
```python
BANNED_KEYWORDS = [
    "real photo", "photograph", "realistic face",
    "celebrity", "brand logo", "copyrighted",
    "nsfw", "gore", "violence",
]
```

---

## 9. 썸네일 자동 생성 프롬프트

```
형식: 1280x720, 고대비, 텍스트 최소화
프롬프트 구조:
  "eye-catching youtube thumbnail, {topic 핵심 이미지},
   bold contrasting colors, dramatic lighting,
   simple composition, no text, 4k quality,
   {pattern별 스타일 접미사}"

후처리:
  - PIL/Pillow로 제목 텍스트 오버레이 (최대 6단어)
  - 폰트: Pretendard Black, 크기: 자동 계산
  - 텍스트 위치: 좌측 또는 중앙
  - 배경 그라데이션 오버레이 (가독성 확보)
```
