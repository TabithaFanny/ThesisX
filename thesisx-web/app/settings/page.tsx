import { AppShell } from "../../components/shell";
import { SettingsWorkspace } from "../../components/settings-workspace";

export default function SettingsPage() {
  return (
    <AppShell
      title="系统设置"
      subtitle="查看本地状态、后端连接情况，以及 mock / real 模式当前遵循的运行语义。"
    >
      <SettingsWorkspace />
    </AppShell>
  );
}
