import numpy as np

from core.schemas import ChartType, DataSeries, ExtractionResult
from validation.confidence import agreement_score, coverage_score, smoothness_score


class CrossValidator:
    W_SMOOTH = 0.5
    W_AGREE = 0.5
    LOW_THRESHOLD = 0.6

    def validate(
        self,
        cv_series: list[DataSeries],
        semantics: dict,
        img,
    ) -> ExtractionResult:
        if isinstance(cv_series, ExtractionResult):
            return cv_series

        flags: list[str] = []
        legend = semantics.get("legend", []) or []
        agree = agreement_score(len(cv_series), len(legend))

        if agree < 0.7 and legend:
            flags.append(
                f"CV 检测到 {len(cv_series)} 条系列，"
                f"VLM 识别 {len(legend)} 个图例，请人工确认系列数量"
            )

        named_series = self._assign_names(cv_series, semantics)

        for s in named_series:
            smooth = smoothness_score(s)
            s.confidence = float(self.W_SMOOTH * smooth + self.W_AGREE * agree)
            if s.confidence < self.LOW_THRESHOLD:
                flags.append(f"系列 '{s.name}' 置信度偏低，建议人工校正")

        overall = (
            float(np.mean([s.confidence for s in named_series])) if named_series else 0.0
        )

        self._check_range_consistency(named_series, semantics, flags)
        hint = semantics.get("data_range_hint", {}) or {}
        x_hint = hint.get("x_max")
        if x_hint is not None and named_series:
            cov_vals = []
            for s in named_series:
                if s.points:
                    xs = [p.x for p in s.points]
                    cov_vals.append(
                        coverage_score(s, (min(xs), float(x_hint)))
                    )
            if cov_vals and min(cov_vals) < 0.5:
                flags.append("数据覆盖度偏低，曲线/散点可能未完整提取")

        chart_type = semantics.get("chart_type", ChartType.LINE)
        if isinstance(chart_type, str):
            try:
                chart_type = ChartType(chart_type)
            except ValueError:
                chart_type = ChartType.UNKNOWN

        if semantics.get("_parse_error"):
            flags.append("VLM 语义 JSON 解析失败，已仅使用 CV 结果")

        return ExtractionResult(
            chart_type=chart_type,
            series=named_series,
            title=semantics.get("title"),
            x_label=semantics.get("x_label"),
            y_label=semantics.get("y_label"),
            x_quantity=semantics.get("x_quantity"),
            y_quantity=semantics.get("y_quantity"),
            x_unit=semantics.get("x_unit"),
            y_unit=semantics.get("y_unit"),
            legend=legend,
            metadata={"semantics": semantics},
            overall_confidence=overall,
            low_confidence_flags=flags,
        )

    def _assign_names(self, cv_series: list[DataSeries], semantics: dict) -> list[DataSeries]:
        color_map = semantics.get("series_colors", {}) or {}
        hex_to_name = {
            v.lower(): k for k, v in color_map.items() if isinstance(v, str) and v.startswith("#")
        }
        for s in cv_series:
            if s.color_hex and s.color_hex.lower() in hex_to_name:
                s.name = hex_to_name[s.color_hex.lower()]
        return cv_series

    def _check_range_consistency(
        self, series: list[DataSeries], semantics: dict, flags: list[str]
    ) -> None:
        hint = semantics.get("data_range_hint", {}) or {}
        if not series:
            return
        all_y = [p.y for s in series for p in s.points]
        if not all_y:
            return
        y_max = max(all_y)
        hint_max = hint.get("y_max")
        if hint_max is not None and hint_max != 0:
            if abs(y_max - hint_max) / abs(hint_max) > 0.3:
                flags.append(
                    f"提取的 Y 最大值 ({y_max:.2g}) 与 VLM 估计 ({hint_max}) 差异较大，请检查标定"
                )
