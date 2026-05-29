"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { getPipelineSessionDetail, getPipelineSessions, getProjectRuns, getProjects } from "../lib/api";
import { getActiveProjectId, getHistorySessionId, setActiveProjectId, setHistorySessionId } from "../lib/project-context";
import type { PipelineSessionDetail, Project } from "../lib/types";
import { EmptyState, ErrorState, Panel, StatCard } from "./ui";

export function RunHistoryWorkspace() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [sessions, setSessions] = useState<string[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [detail, setDetail] = useState<PipelineSessionDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getProjects()
      .then((projectData) => {
        const activeProjectId = searchParams.get("project_id") || getActiveProjectId();
        if (!active) {
          return;
        }
        setProjects(projectData);
        setProjectId(activeProjectId);
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "无法加载运行记录。");
        }
      });
    return () => {
      active = false;
    };
  }, [searchParams]);

  useEffect(() => {
    setActiveProjectId(projectId);
    let active = true;
    const preferredSessionId = getHistorySessionId();
    const load = async () => {
      const list = projectId
        ? await getProjectRuns(projectId)
        : await getPipelineSessions();
      if (!active) {
        return;
      }
      setSessions(list);
      const first = list.includes(preferredSessionId) ? preferredSessionId : list[0] ?? "";
      setSelected(first);
      if (!first) {
        setDetail(null);
        return;
      }
      const nextDetail = await getPipelineSessionDetail(first);
      if (active) {
        setDetail(nextDetail);
      }
    };
    load().catch((loadError) =>
      setError(loadError instanceof Error ? loadError.message : "无法切换项目运行记录。"),
    );
    return () => {
      active = false;
    };
  }, [projectId]);

  useEffect(() => {
    if (!selected) {
      setDetail(null);
      setHistorySessionId("");
      return;
    }
    setHistorySessionId(selected);
    let active = true;
    getPipelineSessionDetail(selected)
      .then((data) => {
        if (active) {
          setDetail(data);
        }
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "无法加载会话详情。");
        }
      });
    return () => {
      active = false;
    };
  }, [selected]);

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="stack">
      <div className="stats-grid">
        <StatCard label="会话总数" value={sessions.length} hint={projectId ? "当前项目关联的 session" : "本地 runs 目录中的 session"} />
        <StatCard label="当前会话事件" value={detail?.event_count ?? 0} hint="事件流和状态记录" />
        <StatCard label="消息数" value={detail?.message_count ?? 0} hint="运行中的消息日志" />
        <StatCard label="错误标记" value={detail?.has_errors ? "有" : "无"} hint="是否存在 error.log" />
      </div>

      <div className="two-column">
        <Panel title="会话列表" eyebrow="Runs">
          <label className="full-span">
            项目过滤
            <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
              <option value="">全部运行记录</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          {sessions.length === 0 ? (
            <EmptyState title="还没有运行记录" body="先在 AI 助手里启动一次任务，这里就会出现 session。" />
          ) : (
            <ul className="entity-list">
              {sessions.map((sessionId) => (
                <li key={sessionId}>
                  <button
                    className={`list-button${selected === sessionId ? " active" : ""}`}
                    onClick={() => {
                      setHistorySessionId(sessionId);
                      setSelected(sessionId);
                    }}
                    type="button"
                  >
                    <strong>{sessionId}</strong>
                    <p>打开查看事件、消息和输出文件。</p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="会话详情" eyebrow="Session">
          {detail ? (
            <div className="stack tight">
              <div className="detail-grid">
                <div>
                  <span className="muted-label">状态</span>
                  <p>{detail.status}</p>
                </div>
                <div>
                  <span className="muted-label">创建时间</span>
                  <p>{detail.created_at || "未记录"}</p>
                </div>
                <div>
                  <span className="muted-label">更新时间</span>
                  <p>{detail.updated_at || "未记录"}</p>
                </div>
                <div className="full-span">
                  <span className="muted-label">输出文件</span>
                  <p>{Object.keys(detail.output_files).length ? Object.keys(detail.output_files).join(" / ") : "暂无"}</p>
                </div>
              </div>
              <pre className="code-block">{JSON.stringify(detail.output_files, null, 2)}</pre>
            </div>
          ) : (
            <EmptyState title="选择一个会话" body="左侧点开 session 后，这里会显示详细信息。" />
          )}
        </Panel>
      </div>
    </div>
  );
}
