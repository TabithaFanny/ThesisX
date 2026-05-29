import { Suspense } from "react";

import { AppShell } from "../../components/shell";
import { EvidenceWorkspace } from "../../components/evidence-workspace";

export default function EvidencePage() {
  return (
    <AppShell
      title="Evidence Workspace"
      subtitle="把 Claim、证据和项目知识连成链，按项目查看 coverage 缺口。"
    >
      <Suspense fallback={null}>
        <EvidenceWorkspace />
      </Suspense>
    </AppShell>
  );
}
