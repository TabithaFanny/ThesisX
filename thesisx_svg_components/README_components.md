# ThesisX SVG 组件拆分包

本包将「ThesisX 主要交互页面总览」拆成可复用 SVG 组件与页面缩略图。每个 SVG 都包含 `<desc>` 描述，另有 `components_manifest.json` 提供尺寸、用途、元素清单和详细说明。整体视觉为浅色学术工具界面，以蓝色强调、细线边框、柔和卡片、低饱和背景和清晰信息层级构成。SVG 内不包含“白蓝”字样。

## 文件结构

- `svg/00_overview_infographic.svg`：整页总览复刻。
- `svg/page_01_*.svg` 至 `svg/page_10_*.svg`：10 个主要页面缩略 SVG。
- `svg/component_*.svg`：可复用原子/复合组件。
- `specs/components_manifest.json`：组件清单、用途、尺寸、元素描述。
- `specs/page_prompts.md`：逐页生成提示词。
- `specs/reconstruction_guide.md`：给另一个 Agent 的复原说明。

## 使用方式

1. 让前端 Agent 读取 `components_manifest.json`，了解每个组件的位置、视觉规则和用途。
2. 需要重建某一页时，先读取对应 `page_XX_*.svg`，再结合 `page_prompts.md` 的提示词生成高保真界面。
3. 若要生成真实前端，可将 SVG 视为结构线框和视觉基准，再用 React/Tailwind 或 PyQt6 控件实现。
