import { Suspense } from "react";

import { AppShell } from "../../components/shell";
import { WritingWorkspace } from "../../components/writing-workspace";

export default function WritingPage() {
  return (
    <AppShell
      title="写作工作台"
      subtitle="围绕当前项目维护 Markdown 草稿，把 pipeline、理论、证据和 AI 改写真正接回写作闭环。"
    >
      <Suspense fallback={null}>
        <WritingWorkspace />
      </Suspense>
    </AppShell>
  );
}
