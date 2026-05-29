import { AppShell } from "../../components/shell";
import { ProjectsWorkspace } from "../../components/projects-workspace";

export default function ProjectsPage() {
  return (
    <AppShell
      title="项目管理"
      subtitle="创建论文项目，进入后续知识、RAG 与 AI 写作的主工作流。"
    >
      <ProjectsWorkspace />
    </AppShell>
  );
}
