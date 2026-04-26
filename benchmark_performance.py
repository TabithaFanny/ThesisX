"""性能基准测试

测试各个模块的性能指标。
"""
import time
import tempfile
import os
from pathlib import Path

from app.core.document_manager import DocumentManager
from app.core.table_handler import TableHandler
from app.core.chart_generator import generate_chart_html
from app.core.markdown_renderer import MarkdownRenderer
from app.core.performance import measure_time, get_monitor


def benchmark_document_operations():
    """测试文档操作性能"""
    print("\n" + "=" * 60)
    print("基准测试 1: 文档操作")
    print("=" * 60)

    dm = DocumentManager()

    # 测试新建文档
    with measure_time("document_new", log_threshold_ms=0):
        doc = dm.new_document()

    # 测试保存小文档
    small_content = "# 测试\n\n" + "这是测试内容。\n" * 100
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        temp_path = f.name

    try:
        with measure_time("document_save_small", log_threshold_ms=0):
            dm.current_document.content = small_content
            dm.save_document(temp_path)

        # 测试打开小文档
        with measure_time("document_open_small", log_threshold_ms=0):
            dm.open_document(temp_path)
    finally:
        os.unlink(temp_path)

    # 测试保存大文档
    large_content = "# 大文档\n\n" + "这是测试内容。\n" * 10000
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        temp_path = f.name

    try:
        with measure_time("document_save_large", log_threshold_ms=0):
            dm.current_document.content = large_content
            dm.save_document(temp_path)

        # 测试打开大文档
        with measure_time("document_open_large", log_threshold_ms=0):
            dm.open_document(temp_path)
    finally:
        os.unlink(temp_path)


def benchmark_table_operations():
    """测试表格操作性能"""
    print("\n" + "=" * 60)
    print("基准测试 2: 表格操作")
    print("=" * 60)

    # 测试创建小表格
    with measure_time("table_create_small", log_threshold_ms=0):
        table = TableHandler.create_empty_table(5, 5)

    # 测试创建大表格
    with measure_time("table_create_large", log_threshold_ms=0):
        table = TableHandler.create_empty_table(50, 20)

    # 测试 CSV 导入
    csv_data = "\n".join([f"col{i},value{i}" for i in range(100)])
    with measure_time("table_csv_import", log_threshold_ms=0):
        table = TableHandler.from_csv_text(csv_data)

    # 测试 TSV 导入
    tsv_data = "\n".join([f"col{i}\tvalue{i}" for i in range(100)])
    with measure_time("table_tsv_import", log_threshold_ms=0):
        table = TableHandler.from_tsv_text(tsv_data)


def benchmark_chart_generation():
    """测试图表生成性能"""
    print("\n" + "=" * 60)
    print("基准测试 3: 图表生成")
    print("=" * 60)

    # 小数据集
    small_config = {
        "title": "测试图表",
        "labels": ["A", "B", "C", "D", "E"],
        "series": [
            {"name": "系列1", "values": [10, 20, 30, 40, 50]}
        ]
    }

    # 测试柱状图
    with measure_time("chart_bar_small", log_threshold_ms=0):
        html = generate_chart_html("bar", small_config)

    # 测试折线图
    with measure_time("chart_line_small", log_threshold_ms=0):
        html = generate_chart_html("line", small_config)

    # 测试饼图
    pie_config = {
        "title": "饼图",
        "labels": ["A", "B", "C", "D", "E"],
        "values": [20, 25, 15, 30, 10]
    }
    with measure_time("chart_pie_small", log_threshold_ms=0):
        html = generate_chart_html("pie", pie_config)

    # 大数据集
    large_config = {
        "title": "大数据图表",
        "labels": [f"Label{i}" for i in range(100)],
        "series": [
            {"name": "系列1", "values": list(range(100))},
            {"name": "系列2", "values": list(range(100, 200))}
        ]
    }

    with measure_time("chart_bar_large", log_threshold_ms=0):
        html = generate_chart_html("bar", large_config)


def benchmark_markdown_rendering():
    """测试 Markdown 渲染性能"""
    print("\n" + "=" * 60)
    print("基准测试 4: Markdown 渲染")
    print("=" * 60)

    renderer = MarkdownRenderer()

    # 简单文本
    simple_text = "# 标题\n\n这是**粗体**和*斜体*。\n\n- 列表项 1\n- 列表项 2"
    with measure_time("markdown_simple", log_threshold_ms=0):
        html = renderer.render(simple_text)

    # 包含代码块
    code_text = simple_text + "\n\n```python\n" + "print('hello')\n" * 10 + "```"
    with measure_time("markdown_with_code", log_threshold_ms=0):
        html = renderer.render(code_text)

    # 包含表格
    table_text = simple_text + "\n\n| A | B | C |\n|---|---|---|\n" + "| 1 | 2 | 3 |\n" * 20
    with measure_time("markdown_with_table", log_threshold_ms=0):
        html = renderer.render(table_text)

    # 大文档
    large_text = "# 大文档\n\n" + ("## 章节\n\n这是内容。\n\n" * 500)
    with measure_time("markdown_large", log_threshold_ms=0):
        html = renderer.render(large_text)


def print_benchmark_results():
    """打印基准测试结果"""
    print("\n" + "=" * 60)
    print("基准测试结果汇总")
    print("=" * 60)

    monitor = get_monitor()
    all_stats = monitor.get_all_stats()

    # 按平均耗时排序
    sorted_stats = sorted(all_stats.items(), key=lambda x: x[1]["avg_ms"], reverse=True)

    print(f"\n{'操作':<30} {'平均耗时':<15} {'最小':<15} {'最大':<15}")
    print("-" * 75)

    for operation, stats in sorted_stats:
        print(
            f"{operation:<30} "
            f"{stats['avg_ms']:>10.2f}ms    "
            f"{stats['min_ms']:>10.2f}ms    "
            f"{stats['max_ms']:>10.2f}ms"
        )

    # 性能评估
    print("\n" + "=" * 60)
    print("性能评估")
    print("=" * 60)

    thresholds = {
        "document_open_small": 50,
        "document_open_large": 500,
        "document_save_small": 50,
        "document_save_large": 500,
        "markdown_simple": 10,
        "markdown_large": 1000,
        "chart_bar_small": 100,
        "chart_bar_large": 500,
    }

    for operation, threshold in thresholds.items():
        if operation in all_stats:
            avg_ms = all_stats[operation]["avg_ms"]
            status = "PASS" if avg_ms <= threshold else "FAIL"
            print(f"{status} {operation}: {avg_ms:.2f}ms (阈值: {threshold}ms)")


def main():
    """运行所有基准测试"""
    print("开始性能基准测试...")

    benchmark_document_operations()
    benchmark_table_operations()
    benchmark_chart_generation()
    benchmark_markdown_rendering()

    print_benchmark_results()


if __name__ == "__main__":
    main()
