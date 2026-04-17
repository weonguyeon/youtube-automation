"""프롬프트 빌더 + 통제된 무작위성

패턴/포맷별 프롬프트 생성.
Hook 유형, 톤, 보이스 스타일을 랜덤으로 변형하여
유튜브 '재사용 콘텐츠' 패널티 회피.
"""

from __future__ import annotations

import random

from pipeline.schema import ColorPreset, Pattern, VideoFormat, FORMAT_SPECS

HOOK_TYPES = {
    "question": "질문으로 시작 (예: '~하면 어떻게 될까?')",
    "statistic": "충격적 통계로 시작 (예: '전 세계 인구의 0.001%만...')",
    "contrast": "대비로 시작 (예: 'A는 ~인데, B는...')",
    "challenge": "도전으로 시작 (예: '이것을 아는 사람은 거의 없다')",
    "timeline": "시간축으로 시작 (예: '2020년, 세계는...')",
}

TONES = ["충격적", "유머러스", "진지한", "호기심 자극"]

SYSTEM_PROMPT = """당신은 유튜브 영상 대본 전문 작가입니다.
반드시 아래 JSON 스키마에 맞춰 응답하세요.
마크다운이나 설명 텍스트 없이, 순수 JSON만 출력하세요.

규칙:
1. 각 scene의 narration은 자연스럽고 대화체로 작성
2. visual_prompt는 영어로 작성 (이미지 생성 AI용)
3. subtitle은 한국어로, 화면에 표시될 핵심 키워드만
4. Hook(첫 장면)은 반드시 시청자를 사로잡아야 함
5. 총 duration_sec 합계가 target_duration을 초과하지 않도록
6. visual_prompt에 "no text, no words, no letters" 반드시 포함
"""


def _prompt_pattern_a(topic: str, fmt: VideoFormat, color_preset: ColorPreset) -> str:
    spec = FORMAT_SPECS[fmt]
    return f"""{SYSTEM_PROMPT}

주제: {topic}
형식: 데이터 비교 영상 (차트 레이스 / 게이지 바)
영상 길이: {spec['duration_sec']}초
포맷: {fmt.value} ({spec['resolution'][0]}x{spec['resolution'][1]})
컬러 프리셋: {color_preset.value}

JSON 출력:
{{
  "pattern": "A",
  "format": "{fmt.value}",
  "color_preset": "{color_preset.value}",
  "metadata": {{
    "title": "유튜브 제목 (호기심 유발, 40자 이내)",
    "description": "유튜브 설명글 (SEO 최적화, 200자)",
    "tags": ["태그1", "태그2"],
    "thumbnail_text": "썸네일 텍스트 (8자 이내)"
  }},
  "scenes": [],
  "audio": {{
    "has_narration": false,
    "bgm_mood": "epic|upbeat|dramatic"
  }},
  "chart": {{
    "chart_type": "bar_race",
    "data_source": "데이터 출처 설명",
    "data": [
      {{"label": "항목명", "values": {{"2020": 100, "2021": 150}}}}
    ]
  }}
}}

데이터는 실제 통계에 기반하되 정확한 수치를 사용하세요.
최소 8개 이상의 비교 항목을 포함하세요."""


def _prompt_pattern_b(topic: str, fmt: VideoFormat, color_preset: ColorPreset) -> str:
    spec = FORMAT_SPECS[fmt]
    hook_type = random.choice(list(HOOK_TYPES.keys()))
    hook_desc = HOOK_TYPES[hook_type]
    tone = random.choice(TONES)

    max_scenes = spec["max_scenes"]
    max_chars = spec["subtitle_max_chars"]

    return f"""{SYSTEM_PROMPT}

주제: {topic}
형식: 숏폼 인포그래픽 ({spec['resolution'][0]}x{spec['resolution'][1]}, {spec['duration_sec']}초)
톤: {tone}
Hook 유형: {hook_type} — {hook_desc}
컬러 프리셋: {color_preset.value}

JSON 출력:
{{
  "pattern": "B",
  "format": "{fmt.value}",
  "color_preset": "{color_preset.value}",
  "metadata": {{
    "title": "유튜브 제목",
    "description": "설명글",
    "tags": [...]
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "scene_type": "hook",
      "duration_sec": 2,
      "narration": "내레이션 (TTS용)",
      "subtitle": "자막 ({max_chars}자 이내, 강조 단어는 **볼드**)",
      "visual_prompt": "flat 2d infographic, ..., no text, no words",
      "transition": "cut|fade|zoom_in",
      "asset_type": "generated"
    }}
  ],
  "audio": {{
    "has_narration": true,
    "voice_style": "energetic|calm|dramatic|curious",
    "bgm_mood": "epic|lofi|tense|upbeat"
  }}
}}

필수:
- scenes {max_scenes}개 이내
- 첫 scene(Hook)은 반드시 2~3초
- narration 총 글자 수 ≈ {spec['duration_sec']} × 4 (한국어 초당 ~4글자)
- subtitle 줄당 {max_chars}자 이내"""


def _prompt_pattern_c(topic: str, fmt: VideoFormat, color_preset: ColorPreset) -> str:
    spec = FORMAT_SPECS[fmt]
    return f"""{SYSTEM_PROMPT}

주제: {topic}
형식: 무음 인포그래픽 (텍스트+차트만, 내레이션 없음)
영상 길이: {spec['duration_sec']}초
컬러 프리셋: {color_preset.value}

JSON 출력:
{{
  "pattern": "C",
  "format": "{fmt.value}",
  "color_preset": "{color_preset.value}",
  "metadata": {{
    "title": "유튜브 제목",
    "description": "설명글",
    "tags": [...]
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "scene_type": "content",
      "duration_sec": 4,
      "subtitle": "슬라이드 제목 (20자 이내)",
      "visual_prompt": "clean infographic, ..., no text",
      "visual_note": "차트 유형: bar|pie|number",
      "transition": "slide_left|fade"
    }}
  ],
  "audio": {{
    "has_narration": false,
    "bgm_mood": "calm|ambient"
  }}
}}

필수:
- 텍스트 최소화, 숫자와 차트 중심
- 글로벌 타겟 가능하도록 숫자/기호 중심"""


def _prompt_pattern_d(topic: str, fmt: VideoFormat, color_preset: ColorPreset) -> str:
    spec = FORMAT_SPECS[fmt]
    hook_type = random.choice(list(HOOK_TYPES.keys()))
    hook_desc = HOOK_TYPES[hook_type]
    tone = random.choice(TONES)
    max_scenes = spec["max_scenes"]

    return f"""{SYSTEM_PROMPT}

주제: {topic}
형식: 벡터 인포그래픽 ({spec['resolution'][0]}x{spec['resolution'][1]}, {spec['duration_sec']}초)
톤: {tone}
Hook 유형: {hook_type} — {hook_desc}
컬러 프리셋: {color_preset.value}

이 영상은 벡터 인포그래픽 스타일입니다.
각 씬은 타임라인, 비교(VS), 프로세스, 통계 그리드 중 하나의 레이아웃을 사용합니다.
visual_prompt에 적합한 레이아웃 유형을 명시하세요.

JSON 출력:
{{
  "pattern": "D",
  "format": "{fmt.value}",
  "color_preset": "{color_preset.value}",
  "metadata": {{
    "title": "유튜브 제목",
    "description": "설명글",
    "tags": [...]
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "scene_type": "hook",
      "duration_sec": 3,
      "narration": "내레이션 (TTS용)",
      "subtitle": "자막 텍스트",
      "visual_prompt": "layout: timeline/comparison/process/stats, ..., no text",
      "visual_note": "timeline|comparison|process|stats",
      "transition": "fade|cut|zoom_in"
    }}
  ],
  "audio": {{
    "has_narration": true,
    "voice_style": "narrative|energetic|calm",
    "bgm_mood": "epic|lofi|upbeat"
  }}
}}

필수:
- scenes {max_scenes}개 이내
- 각 씬의 visual_note에 레이아웃 유형 명시 (timeline/comparison/process/stats)
- narration은 구조화된 정보 설명에 적합하게"""


PATTERN_PROMPTS = {
    Pattern.A_DATA_VIZ: _prompt_pattern_a,
    Pattern.B_TEXT_SHORTS: _prompt_pattern_b,
    Pattern.C_SILENT_INFOGRAPHIC: _prompt_pattern_c,
    Pattern.D_VECTOR_INFOGRAPHIC: _prompt_pattern_d,
}


def build_prompt(
    topic: str,
    pattern: Pattern,
    fmt: VideoFormat,
    color_preset: ColorPreset,
    csv_path: str | None = None,
) -> str:
    builder = PATTERN_PROMPTS.get(pattern)
    if builder is None:
        raise ValueError(f"Pattern {pattern.value} 프롬프트 미구현")

    prompt = builder(topic, fmt, color_preset)

    if csv_path:
        prompt += f"\n\n[참고 데이터 파일]: {csv_path}"

    return prompt
