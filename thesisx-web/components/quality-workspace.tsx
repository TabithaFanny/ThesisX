"use client";

import { useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import { AgentArtifactPanel } from "./agent-artifact-panel";
import {
  getAgentArtifact,
  getProject,
  getProjects,
  getQualityDashboard,
  getResearchQuestion,
  recordAgentFeedback,
  runAgentRewrite,
} from "../lib/api";
import { getActiveProjectId, setActiveProjectId } from "../lib/project-context";
import type { AgentArtifact, Project, QualityDashboard, ResearchQuestion } from "../lib/types";
import { EmptyState, ErrorState, Panel, StatCard } from "./ui";

export function QualityWorkspace() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState("default");
  const [projectDetail, setProjectDetail] = useState<Project | null>(null);
  const [researchQuestion, setResearchQuestion] = useState<ResearchQuestion | null>(null);
  const [dashboard, setDashboard] = useState<QualityDashboard | null>(null);
  const [aiPlan, setAiPlan] = useState<AgentArtifact | null>(null);
  const [aiEvidenceDraft, setAiEvidenceDraft] = useState("");
  const [aiTheoryDraft, setAiTheoryDraft] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    let active = true;
    getProjects()
      .then((data) => {
        const activeProjectId = searchParams.get("project_id") || getActiveProjectId();
        if (!active) {
          return;
        }
        setProjects(data);
        if (activeProjectId) {
          setSelectedProject(activeProjectId);
        } else if (data[0]?.id) {
          setSelectedProject(data[0].id);
        }
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "无法加载项目。");
        }
      });
    return () => {
      active = false;
    };
  }, [searchParams]);

  useEffect(() => {
    setActiveProjectId(selectedProject === "default" ? "" : selectedProject);
    let active = true;
    Promise.all([
      getQualityDashboard(selectedProject),
      selectedProject === "default" ? Promise.resolve(null) : getProject(selectedProject),
      selectedProject === "default"
        ? Promise.resolve(null)
        : getResearchQuestion(selectedProject).catch(() => null),
    ])
      .then(([qualityData, projectData, rqData]) => {
        if (!active) {
          return;
        }
        setDashboard(qualityData);
        setProjectDetail(projectData);
        setResearchQuestion(rqData);
        setAiPlan(null);
        setAiEvidenceDraft("");
        setAiTheoryDraft("");
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "无法加载质量面板。");
        }
      });
    return () => {
      active = false;
    };
  }, [selectedProject]);

  function buildQualityContext() {
    const lines = [
      `项目: ${projectDetail?.name || selectedProject}`,
      `研究问题: ${researchQuestion?.question || projectDetail?.research_question || "未提供"}`,
      `总分: ${dashboard?.overall_score ?? 0}`,
      `写作进度: ${dashboard?.writing_progress ?? 0}%`,
      `Claim 覆盖: ${dashboard?.claim_coverage ?? 0}%`,
      `证据完整性: ${dashboard?.evidence_integrity ?? 0}%`,
      `引文完整性: ${dashboard?.citation_completeness ?? 0}%`,
    ];
    if (dashboard?.suggestions?.length) {
      lines.push("质量建议:");
      for (const item of dashboard.suggestions) {
        lines.push(`- ${item}`);
      }
    }
    return lines.join("\n");
  }

  function onGeneratePlan() {
    if (!dashboard) {
      setError("请先加载质量面板。");
      return;
    }
    startTransition(async () => {
      try {
        const result = await getAgentArtifact({
          task_type: "quality",
          project_id: selectedProject === "default" ? "" : selectedProject,
          query: "generate revision plan from quality dashboard",
          extra_context: "请把这些质量信号整理成一份可以执行的修订计划草稿。",
        });
        setAiPlan(result);
      } catch (rewriteError) {
        setError(rewriteError instanceof Error ? rewriteError.message : "无法生成修订计划。");
      }
    });
  }

  function onGenerateEvidenceDraft() {
    if (!dashboard) {
      setError("请先加载质量面板。");
      return;
    }
    startTransition(async () => {
      try {
        const result = await runAgentRewrite({
          task_type: "evidence",
          selected_text: buildQualityContext(),
          mode: "add_evidence",
          project_id: selectedProject === "default" ? "" : selectedProject,
          query: "generate evidence reinforcement draft from quality dashboard",
          extra_context: "优先围绕 Claim 覆盖率和证据完整性较低的问题给出补强草稿。",
        });
        setAiEvidenceDraft(result.rewritten);
      } catch (rewriteError) {
        setError(rewriteError instanceof Error ? rewriteError.message : "无法生成证据补强草稿。");
      }
    });
  }

  function onGenerateTheoryDraft() {
    const promptSource =
      researchQuestion?.question || projectDetail?.research_question || projectDetail?.name || "";
    if (!promptSource.trim()) {
      setError("当前项目没有研究问题，暂时无法生成理论补强草稿。");
      return;
    }
    startTransition(async () => {
      try {
        const result = await runAgentRewrite({
          task_type: "theory",
          selected_text: promptSource,
          mode: "add_theory",
          project_id: selectedProject === "default" ? "" : selectedProject,
          query: "generate theory reinforcement draft from quality dashboard",
          extra_context: buildQualityContext(),
        });
        setAiTheoryDraft(result.rewritten);
      } catch (rewriteError) {
        setError(rewriteError instanceof Error ? rewriteError.message : "无法生成理论补强草稿。");
      }
    });
  }

  function onQualityFeedback(accepted: boolean) {
    if (!aiPlan) {
      return;
    }
    startTransition(async () => {
      try {
        await recordAgentFeedback({
          task_type: "quality",
          accepted,
          signal: accepted
            ? `Accepted quality artifact (${aiPlan.artifact_type})`
            : `Rejected quality artifact (${aiPlan.artifact_type})`,
        });
        setError("");
      } catch (feedbackError) {
        setError(feedbackError instanceof Error ? feedbackError.message : "无法记录质量反馈。");
      }
    });
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="stack">
      <div className="stats-grid">
        <StatCard label="总分" value={dashboard?.overall_score ?? 0} hint={dashboard?.grade ?? "暂无评分"} />
        <StatCard label="写作进度" value={`${dashboard?.writing_progress ?? 0}%`} />
        <StatCard label="Claim 覆盖" value={`${dashboard?.claim_coverage ?? 0}%`} />
        <StatCard label="证据完整性" value={`${dashboard?.evidence_integrity ?? 0}%`} />
      </div>

      <div className="two-column">
        <Panel title="项目选择" eyebrow="Quality">
          {projects.length === 0 ? (
            <EmptyState title="没有项目" body="先创建一个项目，质量面板会按项目展示。" />
          ) : (
            <div className="selector-grid">
              {projects.map((project) => (
                <button
                  key={project.id}
                  className={`selector-card${selectedProject === project.id ? " active" : ""}`}
                  onClick={() => setSelectedProject(project.id)}
                  type="button"
                >
                  <strong>{project.name}</strong>
                  <p>{project.discipline || "未指定学科"}</p>
                </button>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="质量建议" eyebrow="Signals">
          {dashboard?.suggestions?.length ? (
            <ul className="todo">
              {dashboard.suggestions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <EmptyState title="暂无建议" body="当项目有写作、Claim、证据或引文数据时，这里会给出建议。" />
          )}
        </Panel>
      </div>

      <Panel
        title="AI 修订助手"
        eyebrow="Quality AI"
        actions={
          <div className="panel-actions">
            <button className="secondary-button" disabled={isPending || !dashboard} onClick={onGeneratePlan} type="button">
              生成修订计划
            </button>
            <button className="secondary-button" disabled={isPending || !dashboard} onClick={onGenerateEvidenceDraft} type="button">
              补证据草稿
            </button>
            <button className="secondary-button" disabled={isPending || !selectedProject} onClick={onGenerateTheoryDraft} type="button">
              补理论草稿
            </button>
          </div>
        }
      >
        <div className="three-column">
          <div className="detail-stack">
            <span className="muted-label">修订计划</span>
            {aiPlan ? (
              <AgentArtifactPanel
                artifact={aiPlan}
                acceptLabel="接受计划"
                rejectLabel="拒绝计划"
                onAccept={() => onQualityFeedback(true)}
                onReject={() => onQualityFeedback(false)}
              />
            ) : (
              <p className="body-copy">把当前质量指标和建议整理成一份可执行的修改顺序草稿。</p>
            )}
          </div>
          <div className="detail-stack">
            <span className="muted-label">证据补强</span>
            {aiEvidenceDraft ? (
              <pre className="code-block">{aiEvidenceDraft}</pre>
            ) : (
              <p className="body-copy">围绕 Claim 覆盖率和证据完整性较弱的地方，先生成一段补证据工作草稿。</p>
            )}
          </div>
          <div className="detail-stack">
            <span className="muted-label">理论补强</span>
            {aiTheoryDraft ? (
              <pre className="code-block">{aiTheoryDraft}</pre>
            ) : (
              <p className="body-copy">基于当前项目研究问题，先生成一段可继续加工的理论补强草稿。</p>
            )}
          </div>
        </div>
      </Panel>

      <Panel title="指标明细" eyebrow="Dashboard">
        <div className="detail-grid">
          <div>
            <span className="muted-label">Sections</span>
            <p>
              {dashboard?.sections_completed ?? 0} / {dashboard?.total_sections ?? 0}
            </p>
          </div>
          <div>
            <span className="muted-label">Claims</span>
            <p>
              {dashboard?.claims_covered ?? 0} / {dashboard?.total_claims ?? 0}
            </p>
          </div>
          <div>
            <span className="muted-label">Evidence</span>
            <p>
              {dashboard?.evidence_verified ?? 0} / {dashboard?.total_evidence_items ?? 0}
            </p>
          </div>
          <div>
            <span className="muted-label">Citations</span>
            <p>
              {dashboard?.citations_complete ?? 0} / {dashboard?.total_citations ?? 0}
            </p>
          </div>
        </div>
      </Panel>
    </div>
  );
}
