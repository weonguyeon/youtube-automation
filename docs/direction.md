# 프로젝트 방향성 정의

> 사용자 피드백 반영 (2026-04-17)

---

## 1. 프로젝트 비전 (수정)

### 1차 목표: 서비스 홍보 채널
- 특정 서비스를 홍보하기 위한 인포그래픽 영상 자동 제작
- 다양한 패턴(차트, 텍스트 숏폼, 인포그래픽)으로 홍보 콘텐츠 생산

### 2차 목표: SaaS 웹사이트 배포
- "자동화 영상 생성 웹사이트" — 사용자가 웹에서 영상을 자동 생성
- 누구나 접속하여 주제/스타일/색상 선택 → 완성 영상 다운로드
- 웹 프론트엔드 + Python 백엔드 파이프라인 통합

### 핵심 방향
```
[1차] CLI 기반 자동화 도구 개발 (개발자용)
  ↓
[2차] 웹 UI 래핑 (일반 사용자용 SaaS)
  ↓
[3차] 유료 플랜 / 구독 모델로 수익화
```

---

## 2. 채널 브랜딩 — 8색 프리셋 시스템

**핵심 개념**: 8색 프리셋은 "영상별" 색상이 아니라 **"채널/브랜드별" 고정 색상**.
웹사이트에서 사용자가 자신의 브랜드에 맞는 색상을 **한 번 선택**하면,
해당 채널의 **모든 영상에 일관되게** 적용되어 브랜드 아이덴티티를 형성함.

- 회원가입/채널 설정 시 8가지 중 1개 선택
- 선택된 프리셋이 차트, 자막, 배경, AI 이미지 프롬프트에 자동 반영
- 채널의 모든 영상이 동일한 색감 → 시각적 일관성 = 브랜드 인지도

### 8색 프리셋 정의

| # | 프리셋명 | Primary | Secondary | Accent | Background | Text | 분위기 |
|---|----------|---------|-----------|--------|------------|------|--------|
| 1 | **미드나잇 네이비** | #1a1a2e | #16213e | #e94560 | #0f0f23 | #ffffff | 프로페셔널, 테크 |
| 2 | **오션 블루** | #0077b6 | #00b4d8 | #90e0ef | #03045e | #ffffff | 신뢰감, 기업용 |
| 3 | **선셋 오렌지** | #ff6b35 | #f7c59f | #efefd0 | #1a1a2e | #ffffff | 에너지, 활력 |
| 4 | **포레스트 그린** | #2d6a4f | #40916c | #95d5b2 | #1b2a1f | #ffffff | 자연, 건강 |
| 5 | **로얄 퍼플** | #7b2cbf | #9d4edd | #c77dff | #10002b | #ffffff | 크리에이티브, 혁신 |
| 6 | **코랄 핑크** | #ff6b6b | #ffa07a | #ffd1dc | #2d2d2d | #ffffff | 트렌디, 소셜 |
| 7 | **골드 프리미엄** | #d4a373 | #e6b980 | #fefae0 | #1a1a1a | #ffffff | 럭셔리, 금융 |
| 8 | **모노 그레이** | #adb5bd | #6c757d | #e9ecef | #212529 | #ffffff | 미니멀, 클린 |

### 컬러 적용 규칙
```python
COLOR_PRESETS = {
    "midnight_navy": {
        "primary": "#1a1a2e",      # 메인 요소 (차트 바, 아이콘)
        "secondary": "#16213e",    # 보조 요소 (배경 섹션, 서브 차트)
        "accent": "#e94560",       # 강조 (하이라이트, CTA, 핵심 데이터)
        "background": "#0f0f23",   # 전체 배경
        "text": "#ffffff",         # 텍스트, 자막
        "text_highlight": "#e94560", # 강조 텍스트 (자막 핵심 단어)
        "chart_colors": ["#e94560", "#16213e", "#533483", "#0f3460", "#2b9348"],
    },
    # ... 나머지 7개
}

def apply_color_preset(preset_name: str) -> dict:
    """선택된 프리셋을 파이프라인 전체에 적용"""
    preset = COLOR_PRESETS[preset_name]
    return {
        "subtitle_color": preset["text"],
        "subtitle_highlight": preset["text_highlight"],
        "subtitle_bg": f"{preset['background']}99",  # 60% opacity
        "chart_palette": preset["chart_colors"],
        "visual_prompt_suffix": f", color scheme: {preset['primary']} and {preset['accent']} on {preset['background']} background",
        "thumbnail_overlay": preset["primary"],
    }
```

### 인포그래픽 적용 범위
- 차트/그래프 색상 → `chart_colors`
- 자막 색상/배경 → `text` + `background`
- 강조 키워드 → `accent`
- AI 이미지 프롬프트 → 색상 지시어 자동 삽입
- 썸네일 → `primary` + `accent` 기반

---

## 3. 대본 생성 — Claude CLI (MAX 토큰)

### 개발 단계
- **Claude CLI** (Claude MAX 구독 토큰) 사용
- 로컬에서 `claude` 명령어로 대본 생성
- API 비용 $0

### 배포 단계 (웹사이트)
- **Claude API** (유료 API 키) 전환
- 웹 백엔드에서 API 호출
- 사용자당 과금 모델

### CLI 기반 대본 생성 설계
```python
import subprocess
import json

def generate_script_cli(topic: str, pattern: str, options: dict) -> dict:
    """Claude CLI를 사용하여 대본 생성 (MAX 토큰)"""

    prompt = build_prompt(topic, pattern, options)

    # Claude CLI 호출
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    script_data = json.loads(result.stdout)
    return script_data


def generate_script_api(topic: str, pattern: str, options: dict) -> dict:
    """Claude API를 사용하여 대본 생성 (배포용)"""
    import anthropic

    client = anthropic.Anthropic()
    prompt = build_prompt(topic, pattern, options)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    script_data = json.loads(response.content[0].text)
    return script_data


# 환경에 따라 자동 분기
def generate_script(topic, pattern, options):
    if os.getenv("DEPLOY_MODE") == "api":
        return generate_script_api(topic, pattern, options)
    else:
        return generate_script_cli(topic, pattern, options)
```

---

## 4. 워크플로우 — 순수 Python (n8n 제거)

### 변경 사유
- n8n 외부 의존성 제거
- 디버깅/버전관리 용이
- 웹사이트 백엔드 통합 자연스러움
- 개발자가 직접 운영

### 대체 설계: Python Orchestrator
```python
# pipeline/orchestrator.py

class VideoPipeline:
    """순수 Python 기반 영상 제작 파이프라인"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.script_gen = ScriptGenerator(config)
        self.audio_gen = AudioGenerator(config)
        self.visual_gen = VisualGenerator(config)
        self.assembler = VideoAssembler(config)
        self.publisher = VideoPublisher(config)

    async def run(self, topic: str, pattern: str, options: dict) -> str:
        """전체 파이프라인 실행"""

        # Stage 1: 대본 생성
        script = await self.script_gen.generate(topic, pattern, options)

        # Stage 2: 오디오 생성 (Pattern A/C는 BGM만)
        audio = await self.audio_gen.generate(script)

        # Stage 3: 시각 에셋 생성
        visuals = await self.visual_gen.generate(script)

        # Stage 4: 조립 & 렌더링
        video_path = await self.assembler.assemble(script, audio, visuals)

        # Stage 5: 배포 (선택적)
        if options.get("upload"):
            url = await self.publisher.upload(video_path, script["metadata"])
            return url

        return video_path


# 스케줄링은 APScheduler 또는 시스템 cron 사용
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    pipeline.run_batch,
    trigger="cron",
    hour=18,  # 매일 18시
    kwargs={"batch_config": "config/daily_batch.yaml"}
)
```

### 스케줄링 옵션
| 방식 | 용도 |
|------|------|
| `APScheduler` | Python 내장 스케줄러 (개발/테스트) |
| `crontab` / `Task Scheduler` | OS 레벨 스케줄링 (프로덕션) |
| `Celery + Redis` | 웹사이트 배포 시 비동기 작업 큐 |

---

## 5. 개발 순서 정리

```
[현재] 개발 기획 완료
  ↓
[다음] 스킬 구조 셋팅
  - 패턴별 Python 모듈 구조 확정
  - 공통 스키마 (Pydantic) 정의
  - 컬러 프리셋 시스템
  - CLI 인터페이스 설계
  ↓
[이후] 패턴별 순차 개발
  - Pattern A (데이터 비즈) → MVP
  - Pattern B (텍스트 숏폼)
  - Pattern C (무음 인포그래픽)
  ↓
[최종] 웹사이트 래핑
  - FastAPI 백엔드
  - Next.js 프론트엔드
  - 색상 선택 UI
  - 비동기 렌더링 큐
```
