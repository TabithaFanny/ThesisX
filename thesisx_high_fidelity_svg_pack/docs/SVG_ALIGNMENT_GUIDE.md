# ThesisX SVG Alignment Guide

本包是 ThesisX 高保真前端构建参考包，目标是给前端 Agent 提供稳定的信息架构、状态边界、组件状态和接口映射。

## 对齐原则

1. Main Editor 是真实功能，禁止为了视觉复刻破坏 PreviewWidget / Toolbar。
2. Workspace 其他页面若未接真实链路，必须保留“仅预览 / V2 计划 / V3 计划 / 未接入真实功能”。
3. 高风险按钮如“回滚、提交、启用、同步、上传、生成”在未接链路前必须 disabled / preview。
4. Provider、Runtime、Knowledge 页面可以作为最终产品蓝图，但实现时必须按 Vision 阶段拆分。
5. SVG 是信息架构母版，不是业务完成证明。
