import { Suspense } from "react";

import { AppShell } from "../../components/shell";
import { TheoryWorkspace } from "../../components/theory-workspace";

export default function TheoryPage() {
  return (
    <AppShell
      title="Theory Workspace"
      subtitle="围绕当前项目研究问题匹配理论，并查看理论库的适用范围与局限。"
    >
      <Suspense fallback={null}>
        <TheoryWorkspace />
      </Suspense>
    </AppShell>
  );
}
