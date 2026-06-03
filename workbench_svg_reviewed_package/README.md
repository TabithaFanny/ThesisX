# Workbench SVG Review Package

本包是对上一版 SVG 的完整性复核与增强版输出。

## 文件

- `svg/workbench-main-interface.svg`：高保真五栏 Workbench 主界面图。
- `svg/workbench-prompt-compiler-dataflow.svg`：Prompt 0-4 编译链与数据对象流。
- `svg/workbench-component-map.svg`：前端组件拆分与工程映射图。
- `svg/workbench-interaction-states.svg`：关键交互与状态机图。
- `png_preview/`：由 SVG 渲染出的 PNG 预览，用于人工检查。

## 完整性检查

- XML 可解析。
- SVG 可渲染为 PNG。
- 覆盖五栏工作台结构：左一原 PPT 页面、左二原页 Prompt、中间 AI PPT 助手、右一新页 Prompt、右二生成结果/微调。
- 覆盖 Prompt 编译链：Prompt 0 / 1 / 2 / 转换层 / Prompt 3 / PPTX。
- 明确旧五步流程不再是默认主界面，只作为 Legacy/Fallback。
