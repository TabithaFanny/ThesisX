import { AppShell } from "../../../components/shell";
import { ProjectDetail } from "../../../components/project-detail";

export default function ProjectDetailPage({
  params,
}: {
  params: { projectId: string };
}) {
  return (
    <AppShell
      title="项目工作区"
      subtitle="围绕单个项目整理研究问题、方向和目标，让后续页面都有共同上下文。"
    >
      <ProjectDetail projectId={params.projectId} />
    </AppShell>
  );
}
