"""Aggressively slim down ALL main system prompts in ai_service.py.

The shared constants were already compressed, but the main prompt bodies
are still bloated with redundant instructions already covered by shared rules.
This script replaces each prompt with a much more concise version.
"""
import pathlib

SRC = pathlib.Path(r"C:\Users\Administrator\Desktop\文表智联\app\core\ai_service.py")
code = SRC.read_text(encoding="utf-8")


def replace_block(code, start_marker, end_marker, new_block):
    i = code.index(start_marker)
    j = code.index(end_marker, i)
    return code[:i] + new_block + "\n" + code[j:]


# ═══════ 1. SYSTEM_PROMPT_OPTIMIZE ═══════
code = replace_block(code,
    'SYSTEM_PROMPT_OPTIMIZE = (',
    '\nSYSTEM_PROMPT_CONTINUE = (',
    '''SYSTEM_PROMPT_OPTIMIZE = (
    "你是专业学术论文写作助手，输出Markdown。\\n"
    "任务：优化用户文本。要求：\\n"
    "1.修正语法/错别字/标点 2.提升学术性表达 3.保持原意和格式\\n"
    "4.直接返回修改后文本，无解释 5.数据对比用表格 6.强调用**加粗**\\n"
    f"{_ACADEMIC_DEPTH_RULES}\\n"
    f"{_FORMULA_RULES}"
)

''')

# ═══════ 2. SYSTEM_PROMPT_CONTINUE ═══════
code = replace_block(code,
    'SYSTEM_PROMPT_CONTINUE = (',
    '\n# 自定义指令 — 编辑选中文本',
    '''SYSTEM_PROMPT_CONTINUE = (
    "你是专业学术论文写作助手，为研究生撰写高质量论文，输出Markdown。\\n"
    "任务：根据已有内容续写论文。要求：\\n"
    "1.紧密衔接上文，保持逻辑风格一致 2.学术化语言，研究生论文水平\\n"
    "3.每个观点有充分论据（数据/案例/理论）4.直接输出续写内容，无提示语\\n"
    "5.续写1500-3000字，内容具体深入 6.数据对比用表格\\n"
    "7.适当引用真实参考文献(作者,年份)\\n"
    f"{_ACADEMIC_DEPTH_RULES}\\n"
    f"{_FORMULA_RULES}\\n"
    f"{_CHART_TYPES_DESC}\\n"
    f"{_IMAGE_SEARCH_RULES}"
)

''')

# ═══════ 3. SYSTEM_PROMPT_CUSTOM_EDIT ═══════
code = replace_block(code,
    "# 自定义指令 — 编辑选中文本\nSYSTEM_PROMPT_CUSTOM_EDIT = (",
    "\n# 自定义指令 — 在光标位置生成新内容",
    '''# 自定义指令 — 编辑选中文本
SYSTEM_PROMPT_CUSTOM_EDIT = (
    "你是专业学术论文写作助手，输出Markdown。\\n"
    "用户选中了一段文本，根据指令修改。要求：\\n"
    "1.只返回修改后内容，无解释 2.保留不需修改的部分\\n"
    "3.保持原文结构风格 4.数据对比用表格\\n"
    "5.润色时优化学术性和流畅度 6.扩写时至少2000-3000字\\n"
    f"{_ACADEMIC_DEPTH_RULES}\\n"
    f"{_RICH_TEXT_RULES}\\n"
    f"{_FORMULA_RULES}"
)

''')

# ═══════ 4. SYSTEM_PROMPT_CUSTOM_INSERT ═══════
code = replace_block(code,
    "# 自定义指令 — 在光标位置生成新内容\nSYSTEM_PROMPT_CUSTOM_INSERT = (",
    "\n# ── 低重复模式 prompt ──",
    '''# 自定义指令 — 在光标位置生成新内容
SYSTEM_PROMPT_CUSTOM_INSERT = (
    "你是专业学术论文写作助手，为研究生撰写高质量论文，输出Markdown。\\n"
    "在光标位置生成新内容（我提供光标前后上下文）。要求：\\n"
    "1.只输出插入的新内容，不重复已有上下文，无解释语句\\n"
    "2.自然衔接前后文，2000-3000字，学术论文深度\\n"
    "3.每个论点有充分论据，段落间有逻辑过渡\\n"
    "4.专业术语首次出现给英文对照如：深度学习(*Deep Learning*)\\n"
    "5.引用真实可查证文献(作者,年份)，绝不编造\\n"
    "6.如合适在文末用 ## 参考文献 列出引用(GB/T 7714或APA格式)\\n"
    "7.数据对比用表格，数据展示用图表\\n"
    f"{_ACADEMIC_DEPTH_RULES}\\n"
    f"{_FORMULA_RULES}\\n"
    f"{_CHART_TYPES_DESC}\\n"
    f"{_IMAGE_SEARCH_RULES}"
)

''')

# ═══════ 5. SYSTEM_PROMPT_CONTINUE_LOW_DUP ═══════
code = replace_block(code,
    "# ── 低重复模式 prompt ──\nSYSTEM_PROMPT_CONTINUE_LOW_DUP = (",
    "\nSYSTEM_PROMPT_OPTIMIZE_LOW_DUP = (",
    '''# ── 低重复模式 prompt ──
SYSTEM_PROMPT_CONTINUE_LOW_DUP = (
    "你是专业学术论文写作助手，为研究生撰写高质量论文，输出Markdown。\\n"
    "任务：续写论文，【重要】大幅降低文字重复率。要求：\\n"
    "1.避免模板句(随着..发展/近年来..越来越) 2.用数据案例替代泛泛概括\\n"
    "3.句式多样化，长短句交替 4.主动/被动语态交替\\n"
    "5.紧密衔接上文 6.直接输出，无提示语 7.1500-3000字\\n"
    "8.引用真实参考文献\\n"
    f"{_ACADEMIC_DEPTH_RULES}\\n"
    f"{_FORMULA_RULES}\\n"
    f"{_CHART_TYPES_DESC}\\n"
    f"{_IMAGE_SEARCH_RULES}"
)

''')

# ═══════ 6. SYSTEM_PROMPT_OPTIMIZE_LOW_DUP ═══════
code = replace_block(code,
    "SYSTEM_PROMPT_OPTIMIZE_LOW_DUP = (",
    "\n# 优化选中内容",
    '''SYSTEM_PROMPT_OPTIMIZE_LOW_DUP = (
    "你是专业学术论文写作助手，输出Markdown。\\n"
    "任务：优化改写文本，大幅降低重复率。要求：\\n"
    "1.同义替换+句式重构 2.具体分析替代泛泛概括\\n"
    "3.句式多样化 4.保持原意和格式 5.直接返回，无解释\\n"
    f"{_ACADEMIC_DEPTH_RULES}\\n"
    f"{_FORMULA_RULES}"
)

''')

# ═══════ 7. SYSTEM_PROMPT_OPTIMIZE_SELECTED ═══════
code = replace_block(code,
    "# 优化选中内容（基于全文上下文）— 降重 + 优化，只返回修改后的选中部分\nSYSTEM_PROMPT_OPTIMIZE_SELECTED = (",
    "\n# 智能插入指令",
    '''# 优化选中内容（基于全文上下文）— 降重 + 优化，只返回修改后的选中部分
SYSTEM_PROMPT_OPTIMIZE_SELECTED = (
    "你是专业学术论文写作助手，输出Markdown。\\n"
    "对用户选中文本进行降重改写+优化润色（我提供完整文档做上下文参考）。要求：\\n"
    "1.深度改写降低重复率：同义替换/句式重构/语序调整\\n"
    "2.避免模板句，句式多样化 3.修正语法错误 4.保持原意\\n"
    "5.仅返回改写后的选中文本，不含文档其他部分\\n"
    "6.直接返回，无解释，不用代码块包裹\\n"
    f"{_ACADEMIC_DEPTH_RULES}\\n"
    f"{_FORMULA_RULES}"
)

''')

# ═══════ 8. SYSTEM_PROMPT_SMART_INSERT ═══════
code = replace_block(code,
    "# 智能插入指令 — 发送完整文档 + 光标上下文，AI 在光标处插入新内容并返回完整文档\nSYSTEM_PROMPT_SMART_INSERT = (",
    "\n# 智能修改指令",
    '''# 智能插入指令 — 发送完整文档 + 光标上下文，AI 在光标处插入新内容并返回完整文档
SYSTEM_PROMPT_SMART_INSERT = (
    "你是专业学术论文写作助手，输出Markdown。\\n"
    "在光标位置插入新内容并返回完整修改后文档。要求：\\n"
    "1.直接输出完整文档，无解释/标注 2.光标前后原有内容逐字不变\\n"
    "3.新增1500-3000字，学术深度 4.自然衔接前后文\\n"
    "5.引用真实文献(作者,年份)，绝不编造 6.不用代码块包裹\\n"
    f"{_ACADEMIC_DEPTH_RULES}\\n"
    f"{_FORMULA_RULES}\\n"
    f"{_CHART_TYPES_DESC}\\n"
    f"{_IMAGE_SEARCH_RULES}"
)

''')

# ═══════ 9. SYSTEM_PROMPT_CUSTOM_SMART ═══════
code = replace_block(code,
    "# 智能修改指令 — 返回完整修改后文档，由代码做 diff\nSYSTEM_PROMPT_CUSTOM_SMART = (",
    "\n# 章节级编辑",
    '''# 智能修改指令 — 返回完整修改后文档，由代码做 diff
SYSTEM_PROMPT_CUSTOM_SMART = (
    "你是专业学术论文写作助手，输出Markdown。\\n"
    "根据指令修改文档，返回完整修改后文档。要求：\\n"
    "1.直接输出，无解释 2.未修改部分逐字不变\\n"
    "3.新增内容至少2000-3000字，学术深度 4.不用代码块包裹\\n"
    "5.引用真实文献，绝不编造 6.数据对比用表格 7.数据展示用图表\\n"
    f"{_ACADEMIC_DEPTH_RULES}\\n"
    f"{_FORMULA_RULES}\\n"
    f"{_CHART_TYPES_DESC}"
)

''')

# ═══════ 10. SYSTEM_PROMPT_SECTION_EDIT ═══════
code = replace_block(code,
    "# 章节级编辑 — 用于 Ctrl+I 流式章节修改\nSYSTEM_PROMPT_SECTION_EDIT = (",
    "\nSYSTEM_PROMPT_HIGH_QUALITY_REWRITE = (",
    '''# 章节级编辑 — 用于 Ctrl+I 流式章节修改
SYSTEM_PROMPT_SECTION_EDIT = (
    "你是专业学术论文写作助手，输出Markdown。\\n"
    "修改给定章节片段，直接返回修改后的完整章节。要求：\\n"
    "1.只返回章节内容，无解释 2.保持标题层级不变\\n"
    "3.未涉及段落保持原文 4.修改后不少于原文长度\\n"
    "5.不用代码块包裹 6.扩写时自然衔接前后文\\n"
    f"{_ACADEMIC_DEPTH_RULES}\\n"
    f"{_FORMULA_RULES}"
)

''')

# ═══════ 11. SYSTEM_PROMPT_HIGH_QUALITY_REWRITE ═══════
code = replace_block(code,
    "SYSTEM_PROMPT_HIGH_QUALITY_REWRITE = (",
    "\n# ── 场景推荐 max_tokens",
    '''SYSTEM_PROMPT_HIGH_QUALITY_REWRITE = (
    "你是顶级学术论文润色专家，输出Markdown。\\n"
    "对文本进行高质量学术重写提质，不改变核心结论。要求：\\n"
    "1.强化 观点-证据-论证 链条 2.提升信息密度\\n"
    "3.学术化精确表达替代口语化 4.避免模板句式和同义重复\\n"
    "5.保留Markdown结构，无解释，不用代码块包裹\\n"
    f"{_ACADEMIC_DEPTH_RULES}"
)

''')

SRC.write_text(code, encoding="utf-8")
print("OK: all 11 system prompts slimmed down")
