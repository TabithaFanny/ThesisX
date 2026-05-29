import { Suspense } from "react";

import { QualityWorkspace } from "../../components/quality-workspace";
import { AppShell } from "../../components/shell";

export default function QualityPage() {
  return (
    <AppShell title="Quality Dashboard" subtitle="按项目查看写作、Claim、证据和引文质量。">
      <Suspense fallback={null}>
        <QualityWorkspace />
      </Suspense>
    </AppShell>
  );
}
