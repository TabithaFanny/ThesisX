import { Suspense } from "react";

import { AppShell } from "../../components/shell";
import { KnowledgeWorkspace } from "../../components/knowledge-workspace";

export default function KnowledgePage() {
  return (
    <AppShell
      title="知识库"
      subtitle="统一管理 note、theory、evidence 等知识对象，让项目和 RAG 都能复用。"
    >
      <Suspense fallback={null}>
        <KnowledgeWorkspace />
      </Suspense>
    </AppShell>
  );
}
