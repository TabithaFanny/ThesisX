"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState, useTransition } from "react";

import {
  buildRagIndex,
  createDirection,
  createGoal,
  createResearchQuestion,
  getKnowledgeItems,
  getProjectRuns,
  getProject,
  getProjectDirections,
  getProjectGoals,
  getQualityScore,
  getRagIndexStatus,
  getResearchQuestion,
} from "../lib/api";
import { setActiveProjectId, setHistorySessionId } from "../lib/project-context";
import type { KnowledgeItem, Project, RagIndexStatus, ResearchDirection, ResearchGoal, ResearchQuestion } from "../lib/types";
import { EmptyState, ErrorState, Panel, StatCard } from "./ui";

type ProjectDetailData = {
  directions: ResearchDirection[];
  goals: ResearchGoal[];
  knowledgeItems: KnowledgeItem[];
  project: Project;
  qualityScore: { overall_score: number; grade: string };
  ragStatus: RagIndexStatus | null;
  researchQuestion: ResearchQuestion | null;
  runs: string[];
};

async function fetchProjectDetailData(projectId: string): Promise<ProjectDetailData> {
  const [projectData, directionData, goalData, runData, knowledgeData, ragData, qualityData] = await Promise.all([
    getProject(projectId),
    getProjectDirections(projectId),
    getProjectGoals(projectId),
    getProjectRuns(projectId),
    getKnowledgeItems(projectId),
    getRagIndexStatus(projectId),
    getQualityScore(projectId),
  ]);
  let rqData: ResearchQuestion | null = null;
  try {
    rqData = await getResearchQuestion(projectId);
  } catch {
    rqData = null;
  }
  return {
    directions: directionData,
    goals: goalData,
    knowledgeItems: knowledgeData,
    project: projectData,
    qualityScore: qualityData,
    ragStatus: ragData,
    researchQuestion: rqData,
    runs: runData,
  };
}

export function ProjectDetail({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [rq, setRq] = useState<ResearchQuestion | null>(null);
  const [directions, setDirections] = useState<ResearchDirection[]>([]);
  const [goals, setGoals] = useState<ResearchGoal[]>([]);
  const [runs, setRuns] = useState<string[]>([]);
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
  const [ragStatus, setRagStatus] = useState<RagIndexStatus | null>(null);
  const [qualityScore, setQualityScore] = useState<{ overall_score: number; grade: string } | null>(null);
  const [rqInput, setRqInput] = useState("");
  const [directionInput, setDirectionInput] = useState("");
  const [goalInput, setGoalInput] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  const hasResearchQuestion = Boolean(rq?.question || project?.research_question);
  const hasKnowledge = knowledgeItems.length > 0;
  const hasRagIndex = (ragStatus?.size ?? 0) > 0;
  const hasRuns = runs.length > 0;
  const hasQualitySignals = (qualityScore?.overall_score ?? 0) > 0;
  const pipelineTopic = encodeURIComponent(project?.research_question || project?.name || projectId);
  const noteTitle = encodeURIComponent(`${project?.name || "当前项目"} 研究笔记`);
  const evidenceTitle = encodeURIComponent(`${project?.name || "当前项目"} 证据摘录`);

  async function refreshProjectDetail() {
    const data = await fetchProjectDetailData(projectId);
    setProject(data.project);
    setRq(data.researchQuestion);
    setDirections(data.directions);
    setGoals(data.goals);
    setRuns(data.runs);
    setKnowledgeItems(data.knowledgeItems);
    setRagStatus(data.ragStatus);
    setQualityScore(data.qualityScore);
  }

  useEffect(() => {
    let active = true;
    setActiveProjectId(projectId);
    setError("");
    fetchProjectDetailData(projectId)
      .then((data) => {
        if (!active) {
          return;
        }
        setProject(data.project);
        setRq(data.researchQuestion);
        setDirections(data.directions);
        setGoals(data.goals);
        setRuns(data.runs);
        setKnowledgeItems(data.knowledgeItems);
        setRagStatus(data.ragStatus);
        setQualityScore(data.qualityScore);
      })
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "无法加载项目详情。"),
      );
    return () => {
      active = false;
    };
  }, [projectId]);

  function submitResearchQuestion(event: FormEvent) {
    event.preventDefault();
    startTransition(async () => {
      try {
        await createResearchQuestion(projectId, { question: rqInput, keywords: [], discipline: null });
        setRqInput("");
        await refreshProjectDetail();
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "无法保存研究问题。");
      }
    });
  }

  function submitDirection(event: FormEvent) {
    event.preventDefault();
    startTransition(async () => {
      try {
        await createDirection(projectId, { direction: directionInput, rationale: null });
        setDirectionInput("");
        await refreshProjectDetail();
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "无法新增研究方向。");
      }
    });
  }

  function submitGoal(event: FormEvent) {
    event.preventDefault();
    startTransition(async () => {
      try {
        await createGoal(projectId, { goal: goalInput, milestone: null, deadline: null });
        setGoalInput("");
        await refreshProjectDetail();
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "无法新增研究目标。");
      }
    });
  }

  function onBuildRagIndex() {
    startTransition(async () => {
      try {
        await buildRagIndex(projectId);
        await refreshProjectDetail();
      } catch (buildError) {
        setError(buildError instanceof Error ? buildError.message : "无法为当前项目构建 RAG 索引。");
      }
    });
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!project) {
    return <div className="loading-card">正在加载项目详情...</div>;
  }

  return (
    <div className="stack">
      <div className="stats-grid">
        <StatCard label="知识条目" value={knowledgeItems.length} hint="绑定到当前项目的知识对象" />
        <StatCard label="RAG Chunk" value={ragStatus?.size ?? 0} hint={ragStatus?.message ?? "等待索引状态"} />
        <StatCard label="关联运行" value={runs.length} hint="当前项目的 pipeline session" />
        <StatCard label="质量分数" value={qualityScore?.overall_score ?? 0} hint={qualityScore?.grade ?? "暂无评分"} />
      </div>

      <Panel title={project.name} eyebrow="Project Detail">
        <div className="detail-grid">
          <div>
            <span className="muted-label">学科</span>
            <p>{project.discipline || "未指定"}</p>
          </div>
          <div>
            <span className="muted-label">状态</span>
            <p>{project.status}</p>
          </div>
          <div className="full-span">
            <span className="muted-label">项目摘要</span>
            <p>{project.research_question || "当前项目还没有摘要研究问题。"}</p>
          </div>
        </div>
      </Panel>

      <div className="three-column">
        <Panel title="研究问题" eyebrow="Research">
          {rq ? <p className="body-copy">{rq.question}</p> : <p className="body-copy">当前还没有研究问题。</p>}
          <form className="compact-form" onSubmit={submitResearchQuestion}>
            <textarea
              value={rqInput}
              onChange={(event) => setRqInput(event.target.value)}
              rows={4}
              placeholder="输入当前项目的核心研究问题"
            />
            <button className="primary-button" disabled={isPending || !rqInput.trim()} type="submit">
              保存问题
            </button>
          </form>
        </Panel>

        <Panel title="研究方向" eyebrow="Directions">
          <ul className="mini-list">
            {directions.map((direction) => (
              <li key={direction.id}>{direction.direction}</li>
            ))}
          </ul>
          <form className="compact-form" onSubmit={submitDirection}>
            <input
              value={directionInput}
              onChange={(event) => setDirectionInput(event.target.value)}
              placeholder="新增研究方向"
            />
            <button className="primary-button" disabled={isPending || !directionInput.trim()} type="submit">
              添加
            </button>
          </form>
        </Panel>

        <Panel title="研究目标" eyebrow="Goals">
          <ul className="mini-list">
            {goals.map((goal) => (
              <li key={goal.id}>{goal.goal}</li>
            ))}
          </ul>
          <form className="compact-form" onSubmit={submitGoal}>
            <input value={goalInput} onChange={(event) => setGoalInput(event.target.value)} placeholder="新增研究目标" />
            <button className="primary-button" disabled={isPending || !goalInput.trim()} type="submit">
              添加
            </button>
          </form>
        </Panel>
      </div>

      <div className="two-column">
        <Panel
          title="当前建议"
          eyebrow="Readiness"
          actions={
            !hasRagIndex ? (
              <button className="secondary-button" disabled={isPending} onClick={onBuildRagIndex} type="button">
                {isPending ? "处理中..." : "立即 Build RAG"}
              </button>
            ) : null
          }
        >
          <div className="quick-link-grid">
            {!hasResearchQuestion ? (
              <Link className="selector-card" href={`/projects/${projectId}`}>
                <strong>先定义研究问题</strong>
                <p>没有研究问题时，后续知识组织和写作目标会比较散。</p>
              </Link>
            ) : null}
            {!hasKnowledge ? (
              <Link className="selector-card" href={`/knowledge?project_id=${projectId}&item_type=note&title=${noteTitle}`}>
                <strong>补知识条目</strong>
                <p>当前项目还没有 note、theory 或 evidence，RAG 和质量页会偏空。</p>
              </Link>
            ) : null}
            {!hasRagIndex ? (
              <Link className="selector-card" href={`/rag?project_id=${projectId}`}>
                <strong>Build RAG 索引</strong>
                <p>当前项目还没有 chunk 索引，检索和上下文注入还没开始工作。</p>
              </Link>
            ) : null}
            {!hasRuns ? (
              <Link className="selector-card" href={`/pipeline?project_id=${projectId}&topic=${pipelineTopic}`}>
                <strong>启动第一轮生成</strong>
                <p>为当前项目创建一个 pipeline session，才能开始积累运行历史。</p>
              </Link>
            ) : null}
            {!hasQualitySignals ? (
              <Link className="selector-card" href={`/quality?project_id=${projectId}`}>
                <strong>查看质量面板</strong>
                <p>当前项目还没有形成质量信号，可以先检查进度、Claim 和证据状态。</p>
              </Link>
            ) : null}
            {hasResearchQuestion && hasKnowledge && hasRagIndex && hasRuns ? (
              <Link className="selector-card" href={`/pipeline?project_id=${projectId}&topic=${pipelineTopic}`}>
                <strong>继续推进写作</strong>
                <p>当前项目已经具备基础上下文，可以继续新建 session 或重放历史运行。</p>
              </Link>
            ) : null}
          </div>
        </Panel>

        <Panel title="相关运行" eyebrow="Project Runs">
          {runs.length === 0 ? (
            <EmptyState title="还没有关联运行" body="在当前项目上下文下到 AI 助手页启动一次任务，这里就会出现相关 session。" />
          ) : (
            <ul className="entity-list">
              {runs.slice(0, 8).map((runId) => (
                <li key={runId}>
                  <div>
                    <strong>{runId}</strong>
                    <p>这个 session 已经关联到当前项目。</p>
                  </div>
                  <Link
                    className="secondary-link"
                    href={`/history?project_id=${projectId}`}
                    onClick={() => setHistorySessionId(runId)}
                  >
                    查看历史
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="下一步动作" eyebrow="Workflow">
          <div className="quick-link-grid">
            <Link className="selector-card" href={`/pipeline?project_id=${projectId}&topic=${pipelineTopic}`}>
              <strong>启动 AI 任务</strong>
              <p>在当前项目上下文下创建新的 pipeline session。</p>
            </Link>
            <Link className="selector-card" href={`/writing?project_id=${projectId}`}>
              <strong>进入写作工作台</strong>
              <p>把当前项目草稿、session 论文和 AI 改写都放到同一处推进。</p>
            </Link>
            <Link className="selector-card" href={`/theory?project_id=${projectId}`}>
              <strong>匹配理论框架</strong>
              <p>基于当前研究问题查看最相关的理论候选和适用范围。</p>
            </Link>
            <Link className="selector-card" href={`/knowledge?project_id=${projectId}&item_type=note&title=${noteTitle}`}>
              <strong>整理知识条目</strong>
              <p>直接进入当前项目的知识条目创建状态。</p>
            </Link>
            <Link className="selector-card" href={`/evidence?project_id=${projectId}`}>
              <strong>补 Claim 与证据</strong>
              <p>把当前项目的关键论断和证据链补起来。</p>
            </Link>
            <Link className="selector-card" href={`/rag?project_id=${projectId}`}>
              <strong>检索项目上下文</strong>
              <p>围绕当前项目 build 索引并执行检索。</p>
            </Link>
            <Link className="selector-card" href={`/quality?project_id=${projectId}`}>
              <strong>查看质量</strong>
              <p>检查当前项目的进度、Claim 和证据状态。</p>
            </Link>
            <Link className="selector-card" href={`/knowledge?project_id=${projectId}&item_type=evidence&title=${evidenceTitle}`}>
              <strong>补证据摘录</strong>
              <p>快速为当前项目新增 evidence 类型条目。</p>
            </Link>
            <Link className="selector-card" href={`/export?project_id=${projectId}`}>
              <strong>导出当前成果</strong>
              <p>导出引文、DOCX 草稿或 session archive 供后续整理。</p>
            </Link>
          </div>
        </Panel>
      </div>
    </div>
  );
}
