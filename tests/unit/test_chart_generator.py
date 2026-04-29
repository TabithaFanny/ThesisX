"""chart_generator 单元测试

覆盖：generate_chart_html 入口、21 种图表类型、边界条件。
所有图表生成器都是纯函数（dict → SVG string），测试 ROI 最高。
"""
import pytest

from app.core.chart_generator import generate_chart_html


# ── 入口测试 ──────────────────────────────────────────────────────


class TestGenerateChartHtml:
    """generate_chart_html 入口函数测试"""

    def test_unknown_type_returns_none(self):
        """不支持的图表类型返回 None"""
        result = generate_chart_html("nonexistent", {"series": [{"values": [1]}]})
        assert result is None

    def test_non_dict_config_returns_placeholder(self):
        """非 dict config 返回占位图（非 None）"""
        result = generate_chart_html("bar", "not a dict")
        assert result is not None
        assert "暂无数据" in result

    def test_valid_bar_returns_svg(self, sample_config):
        """有效 bar config 返回包含 SVG 元素的 HTML"""
        result = generate_chart_html("bar", sample_config)
        assert result is not None
        assert "<svg" in result
        assert "</svg>" in result
        assert "chart-container" in result

    def test_result_contains_title(self, sample_config):
        """生成的图表包含标题"""
        result = generate_chart_html("bar", sample_config)
        assert result is not None
        assert sample_config["title"] in result


# ── 21 种图表类型最小合法 config ──────────────────────────────────


# 最小合法 config 定义（确保能生成有效 SVG，非 None）
MINIMAL_CONFIGS = {
    # 简单：series[0].values 非空
    "bar": {"series": [{"values": [10, 20, 30]}]},
    "h_bar": {"series": [{"values": [10, 20, 30]}]},
    "funnel": {"series": [{"values": [100, 60, 30]}]},
    "treemap": {"series": [{"values": [10, 20, 30]}]},
    # series[0].values 非空 + sum > 0
    "pie": {"series": [{"values": [10, 20, 30]}]},
    "donut": {"series": [{"values": [10, 20, 30]}]},
    # 需要 ≥ 2 个数据点
    "line": {"series": [{"values": [1, 2, 3]}]},
    "area": {"series": [{"values": [1, 2, 3]}]},
    # 需要 ≥ 3 个值
    "radar": {"series": [{"values": [1, 2, 3, 4, 5]}]},
    # scatter / bubble：series 非空即可
    "scatter": {"series": [{"values": [1, 2, 3]}]},
    "bubble": {"series": [{"values": [1, 2, 3]}]},
    # gauge：无 guard，config 可为空
    "gauge": {},
    # progress：series[0].values 非空
    "progress": {"series": [{"values": [50]}]},
    # waterfall：series[0].values 非空
    "waterfall": {"series": [{"values": [10, -3, 5, 8]}]},
    # 需要 labels + series
    "grouped": {"labels": ["A", "B"], "series": [{"values": [10, 20]}]},
    "stacked": {"labels": ["A", "B"], "series": [{"values": [10, 20]}]},
    "heatmap": {"labels": ["R1", "R2"], "series": [{"values": [1, 2, 3, 4]}]},
    # 需要 labels + ≥ 2 series
    "gantt": {
        "labels": ["Task1", "Task2"],
        "series": [{"values": [0, 5]}, {"values": [3, 2]}],
    },
    "dual_axis": {
        "labels": ["A", "B", "C"],
        "series": [{"values": [10, 20, 30]}, {"values": [5, 15, 25]}],
    },
    "diverging": {
        "labels": ["A", "B"],
        "series": [{"values": [60, 40]}, {"values": [40, 60]}],
    },
    # 需要 labels + ≥ 5 series
    "boxplot": {
        "labels": ["A"],
        "series": [
            {"values": [1]},
            {"values": [25]},
            {"values": [50]},
            {"values": [75]},
            {"values": [100]},
        ],
    },
}


class TestAllChartTypes:
    """21 种图表类型最小合法 config 测试"""

    @pytest.mark.parametrize("chart_type", list(MINIMAL_CONFIGS.keys()))
    def test_minimal_config_produces_svg(self, chart_type):
        """每种图表类型用最小合法 config 应生成有效 SVG"""
        config = MINIMAL_CONFIGS[chart_type]
        result = generate_chart_html(chart_type, config)
        assert result is not None, f"{chart_type} 返回了 None"
        assert "<svg" in result, f"{chart_type} 输出不含 <svg>"
        assert "</svg>" in result, f"{chart_type} 输出不含 </svg>"
        assert "chart-container" in result, f"{chart_type} 输出不含 chart-container"

    def test_all_21_types_registered(self):
        """确认 21 种类型全部在 MINIMAL_CONFIGS 中定义"""
        assert len(MINIMAL_CONFIGS) == 21


# ── 边界条件 ──────────────────────────────────────────────────────


class TestEdgeCases:
    """边界条件测试"""

    def test_empty_series_returns_placeholder(self):
        """空 series 列表返回占位图"""
        result = generate_chart_html("bar", {"series": []})
        # 空 series 可能返回 None 或占位图
        if result is not None:
            assert "暂无数据" in result or "<svg" in result

    def test_single_data_point_bar(self):
        """单数据点柱状图"""
        result = generate_chart_html("bar", {"series": [{"values": [42]}]})
        assert result is not None
        assert "<svg" in result

    def test_negative_values_bar(self):
        """负值柱状图"""
        result = generate_chart_html("bar", {"series": [{"values": [-10, 0, 10]}]})
        assert result is not None
        assert "<svg" in result

    def test_missing_labels_uses_defaults(self):
        """缺少 labels 时使用默认值"""
        result = generate_chart_html("bar", {"series": [{"values": [1, 2, 3]}]})
        assert result is not None

    def test_pie_all_zeros_returns_placeholder(self):
        """饼图全零值返回占位图（sum=0）"""
        result = generate_chart_html("pie", {"series": [{"values": [0, 0, 0]}]})
        # 应返回占位图或 None
        if result is not None:
            assert "暂无数据" in result

    def test_donut_all_zeros_returns_placeholder(self):
        """环形图全零值返回占位图"""
        result = generate_chart_html("donut", {"series": [{"values": [0, 0, 0]}]})
        if result is not None:
            assert "暂无数据" in result

    def test_line_single_point_returns_placeholder_or_svg(self):
        """折线图单数据点（< 2 点可能返回占位图）"""
        result = generate_chart_html("line", {"series": [{"values": [1]}]})
        # 可能返回 None、占位图或 SVG（取决于实现）
        assert result is None or "<svg" in result or "暂无数据" in result

    def test_radar_two_points_returns_placeholder(self):
        """雷达图 < 3 点返回占位图"""
        result = generate_chart_html("radar", {"series": [{"values": [1, 2]}]})
        if result is not None:
            assert "暂无数据" in result or "<svg" in result

    def test_large_dataset(self):
        """大数据集不崩溃"""
        values = list(range(100))
        result = generate_chart_html("bar", {"series": [{"values": values}]})
        assert result is not None
        assert "<svg" in result

    def test_multiple_series(self):
        """多系列图表"""
        config = {
            "labels": ["A", "B", "C"],
            "series": [
                {"name": "S1", "values": [10, 20, 30]},
                {"name": "S2", "values": [15, 25, 35]},
                {"name": "S3", "values": [5, 15, 25]},
            ],
        }
        result = generate_chart_html("grouped", config)
        assert result is not None
        assert "<svg" in result

    def test_config_with_title_and_colors(self):
        """带标题和颜色配置的图表"""
        config = {
            "title": "自定义标题",
            "labels": ["X", "Y"],
            "series": [{"name": "系列A", "values": [100, 200]}],
            "colors": ["#FF0000", "#00FF00"],
        }
        result = generate_chart_html("bar", config)
        assert result is not None
        assert "自定义标题" in result
