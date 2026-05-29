import { AppShell } from "../components/shell";
import { WorkspaceHome } from "../components/workspace-home";

export default function HomePage() {
  return (
    <AppShell
      title="工作台"
      subtitle="从项目、知识、文献到 AI 生成的主流程入口都先收拢在这里。"
    >
      <WorkspaceHome />
    </AppShell>
  );
}
