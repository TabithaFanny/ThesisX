import { Suspense } from "react";

import { AppShell } from "../../components/shell";
import { LiteratureWorkspace } from "../../components/literature-workspace";

export default function LiteraturePage() {
  return (
    <AppShell
      title="文献库"
      subtitle="浏览、搜索和核对本地文献条目，为写作和引用准备可靠原料。"
    >
      <Suspense fallback={null}>
        <LiteratureWorkspace />
      </Suspense>
    </AppShell>
  );
}
