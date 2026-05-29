---

## 12. 与其他模块的关系

| 模块 | 关系 |
|------|------|
| Research Workspace（3.0） | 读取 ResearchQuestion，影响理论推荐 |
| Knowledge Base（3.1） | TheoryItem 是 KnowledgeBase 的扩展类型 |
| RAG Context Engine（3.5） | 可结合 RAG 检索结果辅助理论匹配 |
| Editor AI Loop（3.6） | 理论可写入论文框架 |

---

*本文档是 Theory Matcher 模块的产品需求基准。*
*技术实现以 TECHNICAL_ARCHITECTURE.md 和 DATA_MODEL.md 为准。*
*产品决策以 PRODUCT_DECISIONS.md 为准。*