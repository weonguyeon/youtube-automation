"""Pattern A: 데이터 비주얼라이제이션 렌더러

CSV/DataFrame → bar_chart_race → MP4 차트 애니메이션
렌더링 후 FFmpeg로 정확한 해상도/길이 보정
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from pipeline.colors import ColorTheme, get_theme
from pipeline.schema import FORMAT_SPECS, VideoScript
from pipeline.visual.base_renderer import BaseRenderer, VisualResult

matplotlib.use("Agg")
logger = logging.getLogger(__name__)


class DataVizRenderer(BaseRenderer):
    """차트 레이스 / 데이터 시각화 영상 렌더러"""

    def render(self, script: VideoScript, output_dir: Path) -> VisualResult:
        result = VisualResult()

        theme = get_theme(script.color_preset)

        if script.chart is not None:
            df = self._build_dataframe(script)
        else:
            df = self._load_csv(script, output_dir)

        # 1차: bar_chart_race 렌더링 (해상도 근사)
        raw_path = output_dir / "chart_raw.mp4"
        self._render_bar_chart_race(df, raw_path, theme, script)

        # 2차: FFmpeg로 정확한 해상도/길이 보정
        final_path = output_dir / "chart_animation.mp4"
        self._normalize_video(raw_path, final_path, script)

        result.video_clip_path = final_path
        logger.info("차트 애니메이션 렌더링 완료: %s", final_path)
        return result

    def render_from_csv(self, csv_path: str, output_dir: Path, script: VideoScript) -> VisualResult:
        """CSV 파일로부터 직접 렌더링"""
        result = VisualResult()
        theme = get_theme(script.color_preset)

        df = pd.read_csv(csv_path, index_col=0)

        raw_path = output_dir / "chart_raw.mp4"
        self._render_bar_chart_race(df, raw_path, theme, script)

        final_path = output_dir / "chart_animation.mp4"
        self._normalize_video(raw_path, final_path, script)

        result.video_clip_path = final_path
        return result

    def _build_dataframe(self, script: VideoScript) -> pd.DataFrame:
        """chart.data → pandas DataFrame"""
        if script.chart is None:
            raise ValueError("chart 데이터 없음")

        data = {}
        for item in script.chart.data:
            data[item.label] = item.values

        df = pd.DataFrame(data).T
        df.columns = [str(c) for c in df.columns]
        df = df.astype(float)
        return df.T

    def _load_csv(self, script: VideoScript, output_dir: Path) -> pd.DataFrame:
        """외부 CSV 로드 (첫 번째 컬럼을 인덱스로)"""
        raise ValueError("chart 데이터 또는 CSV 경로 필수")

    def _render_bar_chart_race(
        self,
        df: pd.DataFrame,
        output_path: Path,
        theme: ColorTheme,
        script: VideoScript,
    ):
        """bar_chart_race로 MP4 렌더링"""
        import bar_chart_race as bcr

        # 다크 테마 적용
        plt.rcParams["figure.facecolor"] = theme.background
        plt.rcParams["axes.facecolor"] = theme.background
        plt.rcParams["text.color"] = theme.text
        plt.rcParams["axes.labelcolor"] = theme.text
        plt.rcParams["xtick.color"] = theme.text
        plt.rcParams["ytick.color"] = theme.text

        spec = FORMAT_SPECS[script.format]
        target_duration = spec["duration_sec"]
        n_periods = len(df) - 1

        # 타겟 길이에 맞게 속도 계산
        # total_time ≈ n_periods * period_length(ms) / 1000
        if n_periods > 0:
            period_ms = int(target_duration * 1000 / n_periods)
            steps = 30
        else:
            steps = 20
            period_ms = 800

        # 9:16 세로 비율
        w, h = spec["resolution"]
        fig_w = 6.0
        fig_h = fig_w * h / w

        n_bars = min(10, len(df.columns))

        bcr.bar_chart_race(
            df=df,
            filename=str(output_path),
            n_bars=n_bars,
            steps_per_period=steps,
            period_length=period_ms,
            figsize=(fig_w, fig_h),
            dpi=int(w / fig_w),
            cmap=theme.chart_colors[: len(df.columns)],
            title="",
            bar_label_size=9,
            tick_label_size=8,
            shared_fontdict={"family": "sans-serif", "weight": "bold", "color": theme.text},
            bar_kwargs={"alpha": 0.9},
        )

    def _normalize_video(self, input_path: Path, output_path: Path, script: VideoScript):
        """FFmpeg로 정확한 해상도와 길이 보정"""
        import ffmpeg

        spec = FORMAT_SPECS[script.format]
        w, h = spec["resolution"]
        duration = spec["duration_sec"]

        (
            ffmpeg
            .input(str(input_path))
            .filter("scale", w, h, force_original_aspect_ratio="decrease")
            .filter("pad", w, h, "(ow-iw)/2", "(oh-ih)/2", color=get_theme(script.color_preset).background)
            .output(
                str(output_path),
                vcodec="libx264",
                pix_fmt="yuv420p",
                preset="fast",
                t=duration,
            )
            .overwrite_output()
            .run(quiet=True)
        )

        # 원본 삭제
        if input_path.exists() and output_path.exists():
            input_path.unlink()
