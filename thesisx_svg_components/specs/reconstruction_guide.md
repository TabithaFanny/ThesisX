# 界面复原说明

## 总体视觉规则

- 画布比例：16:9 横版，建议 1536×864 或 1920×1080。
- 背景：极浅冷色调背景，接近 `#F7FAFF`。
- 卡片：白色底，1px 低饱和蓝灰边框，圆角 8-12px，轻微阴影。
- 强调色：主按钮和当前选中态使用清爽蓝，辅助强调可使用淡紫。
- 字体：中文优先 PingFang SC / Microsoft YaHei；英文 Inter / Arial。
- 信息层级：标题 20-28px，模块标题 14-16px，正文 11-13px，辅助说明 9-11px。
- 图标：线性、低饱和，尽量少用 emoji。若使用 emoji，仅作为小型状态辅助，不要成为视觉中心。
- 不在界面文字中出现“白蓝”两个字，只通过视觉体现该方向。

## 组件复原方法

1. 先读取 `00_overview_infographic.svg` 理解总览结构。
2. 单页生成时读取对应 `page_XX_*.svg`，按其布局比例还原。
3. 可复用组件来自 `component_*.svg`：导航、工具栏、大纲树、正文画布、Agent 对话、版本 diff、技能卡片。
4. 所有具体文本可替换，但布局关系、卡片密度、边框、色彩层级应保持一致。

## React/Tailwind 映射建议

- 页面容器：`bg-[#F7FAFF] text-slate-800`。
- 卡片：`bg-white border border-slate-200 rounded-xl shadow-sm`。
- 主按钮：`bg-blue-600 text-white rounded-lg`。
- 次按钮：`bg-blue-50 text-blue-700 border border-blue-100 rounded-lg`。
- muted 文本：`text-slate-500`。
- 表格：细分隔线、hover 浅底色、标签 pill。
