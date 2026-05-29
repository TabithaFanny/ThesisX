"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getApiHealth, getKnowledgeItems, getLiterature, getProjects, getProjectRuns, getSessions } from "../lib/api";
import { getActiveProjectId } from "../lib/project-context";
import type { ApiHealth, KnowledgeItem, LiteratureReference, Project } from "../lib/types";
import { EmptyState, ErrorState, Panel, StatCard } from "./ui";

type HealthState = ApiHealth & {
  ok?: boolean;
  statusCode?: number | null;
  statusText?: string;
};

export function WorkspaceHome() {
  const [health, setHealth] = useState<HealthState | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [literature, setLiterature] = useState<LiteratureReference[]>([]);
  const [sessions, setSessions] = useState<string[]>([]);
  const [activeProjectRuns, setActiveProjectRuns] = useState<string[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [error, setError] = useState<string>("");
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    let active = true;
    async function load() {
      const [healthResult, projectResult, knowledgeResult, literatureResult, sessionResult] =
        await Promise.allSettled([
          getApiHealth(),
          getProjects(),
          getKnowledgeItems(),
          getLiterature(),
          getSessions(),
        ]);
      if (!active) {
        return;
      }
      const healthData = healthResult.status === "fulfilled" ? healthResult.value : null;
      const projectData = projectResult.status === "fulfilled" ? projectResult.value : [];
      const knowledgeData = knowledgeResult.status === "fulfilled" ? knowledgeResult.value : [];
      const literatureData = literatureResult.status === "fulfilled" ? literatureResult.value : [];
      const sessionData = sessionResult.status === "fulfilled" ? sessionResult.value : [];
      const failedLoads = [projectResult, knowledgeResult, literatureResult, sessionResult].filter(
        (result) => result.status === "rejected",
      );

      setHealth(healthData);
      setProjects(projectData);
      setKnowledge(knowledgeData);
      setLiterature(literatureData);
      setSessions(sessionData);
      setIsOffline(Boolean(!healthData?.ok || failedLoads.length > 0));
      setError(
        failedLoads.length > 0
          ? "后端数据暂时不可用。请确认 FastAPI 正在运行，工作台会在刷新后恢复完整数据。"
          : "",
      );

      const activeProjectId = getActiveProjectId();
      const currentProject = projectData.find((project) => project.id === activeProjectId) ?? null;
      setActiveProject(currentProject);
      if (activeProjectId && projectResult.status === "fulfilled") {
        const runResult = await Promise.allSettled([getProjectRuns(activeProjectId)]);
        if (active && runResult[0].status === "fulfilled") {
          setActiveProjectRuns(runResult[0].value);
        }
      } else {
        setActiveProjectRuns([]);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="stack">
      {error ? <ErrorState message={error} /> : null}
      <div className="stats-grid">
        <StatCard label="项目" value={projects.length} hint="当前工作空间中的论文项目" />
        <StatCard label="知识条目" value={knowledge.length} hint="知识库可检索对象总数" />
        <StatCard label="文献" value={literature.length} hint="本地文献条目" />
        <StatCard
          label="运行记录"
          value={sessions.length}
          hint={health?.ok ? "后端在线" : "等待后端连接"}
        />
      </div>

      {isOffline ? (
        <Panel title="后端状态" eyebrow="API">
          <div className="detail-grid">
            <div>
              <span className="muted-label">状态</span>
              <p>{health?.statusText || "无法连接 ThesisX API"}</p>
            </div>
            <div>
              <span className="muted-label">HTTP</span>
              <p>{health?.statusCode ?? "未连接"}</p>
            </div>
            <div className="full-span">
              <span className="muted-label">启动命令</span>
              <p>在项目根目录运行 `python -m uvicorn thesisx_api.main:app --reload`，然后刷新此页。</p>
            </div>
          </div>
        </Panel>
      ) : null}

      <div className="two-column">
        <Panel title="当前上下文" eyebrow="Active Project">
          {!activeProject ? (
            <EmptyState title="还没有当前项目" body="从项目页选择一个项目后，这里会显示跨页面的工作上下文。" />
          ) : (
            <div className="detail-stack">
              <div>
                <strong>{activeProject.name}</strong>
                <p className="body-copy">{activeProject.research_question || "当前项目还没有研究问题摘要。"}</p>
              </div>
              <div className="quick-link-grid">
                <Link className="selector-card" href={`/projects/${activeProject.id}`}>
                  <strong>项目工作区</strong>
                  <p>查看研究问题、方向与目标。</p>
                </Link>
                <Link className="selector-card" href="/knowledge">
                  <strong>知识库</strong>
                  <p>围绕当前项目整理 note、theory、evidence。</p>
                </Link>
                <Link className="selector-card" href="/rag">
                  <strong>RAG</strong>
                  <p>按当前项目 build 索引并做检索。</p>
                </Link>
                <Link className="selector-card" href="/writing">
                  <strong>写作</strong>
                  <p>把项目上下文、AI 结果和草稿真正接回写作闭环。</p>
                </Link>
                <Link className="selector-card" href="/quality">
                  <strong>质量</strong>
                  <p>检查当前项目的进度、Claim 和证据状态。</p>
                </Link>
              </div>
            </div>
          )}
        </Panel>

        <Panel title="当前项目" eyebrow="Workspace">
          {projects.length === 0 ? (
            <EmptyState title="还没有项目" body="先在项目页创建论文项目，后续页面会围绕它展开。" />
          ) : (
            <ul className="entity-list">
              {projects.slice(0, 5).map((project) => (
                <li key={project.id}>
                  <div>
                    <strong>{project.name}</strong>
                    <p>{project.research_question || "还没有研究问题摘要"}</p>
                  </div>
                  <span className={`badge${activeProject?.id === project.id ? " accent" : ""}`}>
                    {activeProject?.id === project.id ? "当前项目" : project.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <Panel title="最近运行" eyebrow="Pipeline">
        {(activeProject ? activeProjectRuns : sessions).length === 0 ? (
          <EmptyState title="还没有运行记录" body="在 AI 助手页发起一次任务后，这里会显示最近 session。" />
        ) : (
          <ul className="entity-list">
            {(activeProject ? activeProjectRuns : sessions).slice(0, 6).map((sessionId) => (
              <li key={sessionId}>
                <div>
                  <strong>{sessionId}</strong>
                  <p>{activeProject ? "当前项目关联的运行记录。" : "可在 AI 助手页查看详情和事件流。"}</p>
                </div>
                <span className="badge accent">session</span>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
