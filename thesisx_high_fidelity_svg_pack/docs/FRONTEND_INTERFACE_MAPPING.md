# Frontend Interface Mapping

| 页面 | SVG | 目标前端文件 | 核心接口 / 数据源 | 当前状态 |
|---|---|---|---|---|
| Workspace Home | pages/page_01_workspace_home.svg | app/ui/pages/workspace_home.py | workspace_data / RunHistoryReader | 入口 + mock |
| Main Editor | pages/page_02_main_editor.svg | app/ui/main_window.py | 文档编辑器真实状态 | 真实功能 |
| Run History | pages/page_13_run_history.svg | future page | RunHistoryReader | planned |
| Runtime Diagnostics | pages/page_14_runtime_diagnostics.svg | future page | RunDiagnostics | planned |
| Provider Settings | pages/page_15_provider_settings.svg | future settings | ProviderDetector / providers.json | planned |
| Knowledge Base | pages/page_11_knowledge_base.svg | future page | KnowledgeStore / ingestion | future |
| Theory Matcher | pages/page_12_theory_matcher.svg | future page | TheoryMatcher service | future |
