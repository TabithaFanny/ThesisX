import { Suspense } from "react";

import { AppShell } from "../../components/shell";
import { ExportWorkspace } from "../../components/export-workspace";

export default function ExportPage() {
  return (
    <AppShell
      title="Export Workspace"
      subtitle="围绕当前项目导出引文、DOCX 草稿和 session archive。"
    >
      <Suspense fallback={null}>
        <ExportWorkspace />
      </Suspense>
    </AppShell>
  );
}
