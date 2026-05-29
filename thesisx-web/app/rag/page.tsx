import { Suspense } from "react";

import { AppShell } from "../../components/shell";
import { RagWorkspace } from "../../components/rag-workspace";

export default function RagPage() {
  return (
    <AppShell
      title="RAG 检索"
      subtitle="构建本地持久化索引，按项目或对象过滤检索片段，并为写作准备上下文。"
    >
      <Suspense fallback={null}>
        <RagWorkspace />
      </Suspense>
    </AppShell>
  );
}
