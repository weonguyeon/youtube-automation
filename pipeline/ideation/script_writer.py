"""대본 생성 모듈

개발: Claude CLI (MAX 토큰) 사용
배포: Claude API 전환
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from pipeline.config import settings
from pipeline.ideation.prompt_pool import build_prompt
from pipeline.schema import ColorPreset, Pattern, VideoFormat, VideoScript

logger = logging.getLogger(__name__)


class ScriptWriter:
    """Claude CLI/API를 사용한 대본 생성기"""

    def generate(
        self,
        topic: str,
        pattern: Pattern,
        fmt: VideoFormat,
        color_preset: ColorPreset,
        csv_path: str | None = None,
    ) -> VideoScript:
        prompt = build_prompt(topic, pattern, fmt, color_preset, csv_path)

        if settings.deploy_mode == "api":
            raw = self._generate_api(prompt)
        else:
            raw = self._generate_cli(prompt)

        script = VideoScript.model_validate(raw)
        logger.info("대본 생성 완료: %s씬, %s초", len(script.scenes), script.total_scene_duration)
        return script

    def _generate_cli(self, prompt: str) -> dict:
        """Claude CLI (MAX 토큰) 사용"""
        import os
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
            env=env,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI 에러: {result.stderr}")

        response = json.loads(result.stdout)

        # Claude CLI JSON 출력에서 실제 텍스트 추출
        if isinstance(response, dict) and "result" in response:
            text = response["result"]
        elif isinstance(response, list):
            text = next(
                (b.get("text", "") for b in response if b.get("type") == "text"),
                "",
            )
        else:
            text = str(response)

        # 마크다운 코드블록 제거 (```json ... ```)
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # ```json 제거
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        data = self._extract_json(text)

        # scene_type 정규화 (Claude가 스키마 외 값 반환할 경우)
        valid_types = {"hook", "content", "wrapup", "cta"}
        for scene in data.get("scenes", []):
            if scene.get("scene_type") not in valid_types:
                scene["scene_type"] = "content"

        return data

    @staticmethod
    def _extract_json(text: str) -> dict:
        """텍스트에서 첫 번째 유효한 JSON 객체 추출"""
        text = text.strip()
        # 중괄호 시작 위치 찾기
        start = text.find("{")
        if start == -1:
            raise ValueError("JSON 객체를 찾을 수 없습니다")

        # 중괄호 매칭으로 JSON 끝 위치 찾기
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])

        # 폴백: 그냥 파싱 시도
        return json.loads(text[start:])

    def _generate_api(self, prompt: str) -> dict:
        """Claude API 사용 (배포용)"""
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        return json.loads(text)
