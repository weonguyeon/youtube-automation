# 계획서: 3대 렌더링 엔진 통합

## 목표
Manim / Remotion / AI Pipeline(MoneyPrinter 스타일) 3가지 렌더링 엔진을
사용자가 웹사이트에서 선택 가능하도록 통합

## 엔진 정의
- **Engine 1: Manim** — Python 코드 기반 애니메이션 (차트, 도형, 텍스트 모션)
- **Engine 2: Remotion** — React 컴포넌트 기반 인포그래픽 템플릿
- **Engine 3: AI Pipeline** — AI 이미지 생성 + TTS + 자동 조립 (MoneyPrinter 스타일)

## 변경 범위
1. schema.py에 RenderEngine enum 추가
2. 각 엔진별 렌더러 모듈 생성
3. orchestrator에서 엔진 분기
4. CLI에 --engine 옵션 추가

## 현재 단계
구현 시작
