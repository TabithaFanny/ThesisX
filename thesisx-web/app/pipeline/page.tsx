import { Suspense } from "react";

import { AppShell } from "../../components/shell";
import { PipelineWorkspace } from "../../components/pipeline-workspace";

export default function PipelinePage() {
  return (
    <AppShell
      title="AI 助手"
      subtitle="从 mock 到 real 的论文生成任务都在这里发起，事件流和结果摘要会实时展示。"
    >
      <Suspense fallback={null}>
        <PipelineWorkspace />
      </Suspense>
    </AppShell>
  );
}
