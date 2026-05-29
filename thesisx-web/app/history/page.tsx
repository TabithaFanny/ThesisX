import { Suspense } from "react";

import { RunHistoryWorkspace } from "../../components/run-history-workspace";
import { AppShell } from "../../components/shell";

export default function HistoryPage() {
  return (
    <AppShell title="Run History" subtitle="查看本地 session、事件流和输出文件。">
      <Suspense fallback={null}>
        <RunHistoryWorkspace />
      </Suspense>
    </AppShell>
  );
}
