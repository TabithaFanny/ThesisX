"use client";

import { FormEvent, useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import {
  createPipelineSession,
  deletePipelineSession,
  getPipelineSessionDetail,
  getPipelineSessions,
  linkProjectRun,
  streamPipelineSession,
  writePipelineContext,
} from "../lib/api";
import {
  getActiveProjectId,
  getHistorySessionId,
  setActiveProjectId,
  setHistorySessionId,
} from "../lib/project-context";
import type { PipelineSessionDetail } from "../lib/types";
import { EmptyState, ErrorState, Panel, StatCard } from "./ui";

type StreamEvent = {
  event: string;
  data: string;
};

type PipelineSessionBundle = {
  detail: PipelineSessionDetail | null;
  selectedSessionId: string;
  sessions: string[];
};

async function fetchPipelineSessionBundle(
  preferredSessionId?: string,
  fallbackSessionId?: string,
): Promise<PipelineSessionBundle> {
  const list = await getPipelineSessions();
  const nextId = preferredSessionId ?? fallbackSessionId ?? list[0] ?? "";
  if (!nextId) {
    return { detail: null, selectedSessionId: "", sessions: list };
  }
  return {
    detail: await getPipelineSessionDetail(nextId),
    selectedSessionId: nextId,
    sessions: list,
  };
}

export function PipelineWorkspace() {
  const searchParams = useSearchParams();
  const [activeProjectId, setActiveProjectIdState] = useState("");
  const [sessions, setSessions] = useState<string[]>([]);
  const [topic, setTopic] = useState("");
  const [runMode, setRunMode] = useState("mock");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [detail, setDetail] = useState<PipelineSessionDetail | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  async function reloadSessions(preferredSessionId?: string) {
    const data = await fetchPipelineSessionBundle(preferredSessionId, sessionId);
    setSessions(data.sessions);
    setSessionId(data.selectedSessionId);
    setDetail(data.detail);
  }

  useEffect(() => {
    const currentProjectId = searchParams.get("project_id") || getActiveProjectId();
    const nextTopic = searchParams.get("topic");
    setActiveProjectIdState(currentProjectId);
    if (currentProjectId) {
      setActiveProjectId(currentProjectId);
    }
    setTopic((current) => {
      if (nextTopic) {
        return nextTopic;
      }
      if (current) {
        return current;
      }
      return currentProjectId ? `基于项目 ${currentProjectId} 的论文草稿生成` : current;
    });
    fetchPipelineSessionBundle(getHistorySessionId())
      .then((data) => {
        setSessions(data.sessions);
        setSessionId(data.selectedSessionId);
        setDetail(data.detail);
      })
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "无法加载运行会话。"),
      );
  }, [searchParams]);

  async function openSession(nextSessionId: string) {
    setError("");
    setSessionId(nextSessionId);
    setDetail(await getPipelineSessionDetail(nextSessionId));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setEvents([]);
    startTransition(async () => {
      try {
        const created = await createPipelineSession({
          topic,
          run_mode: runMode,
          api_key: apiKey,
          base_url: baseUrl,
          model,
        });
        const currentProjectId = activeProjectId || getActiveProjectId();
        if (currentProjectId) {
          await linkProjectRun(currentProjectId, created.session_id);
        }
        setHistorySessionId(created.session_id);
        await writePipelineContext(created.session_id, {
          topic,
          run_mode: runMode,
          api_key: apiKey,
          base_url: baseUrl,
          model,
        });
        await reloadSessions(created.session_id);
        const streamEvents = await streamPipelineSession(created.session_id);
        setEvents(streamEvents);
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "无法启动任务。");
      }
    });
  }

  function onDeleteSession(targetSessionId: string) {
    startTransition(async () => {
      try {
        await deletePipelineSession(targetSessionId);
        if (targetSessionId === sessionId) {
          setEvents([]);
        }
        await reloadSessions(targetSessionId === sessionId ? undefined : sessionId);
      } catch (deleteError) {
        setError(deleteError instanceof Error ? deleteError.message : "无法删除会话。");
      }
    });
  }

  function onReplaySession() {
    if (!sessionId) {
      return;
    }
    setError("");
    setEvents([]);
    setHistorySessionId(sessionId);
    startTransition(async () => {
      try {
        setDetail(await getPipelineSessionDetail(sessionId));
        const streamEvents = await streamPipelineSession(sessionId);
        setEvents(streamEvents);
      } catch (streamError) {
        setError(streamError instanceof Error ? streamError.message : "无法读取事件流。");
      }
    });
  }

  return (
    <div className="stack">
      {error ? <ErrorState message={error} /> : null}
      <div className="stats-grid">
        <StatCard label="总会话数" value={sessions.length} hint="本地 runs 历史" />
        <StatCard label="当前项目" value={activeProjectId || "未指定"} hint="新建 session 会优先绑定这里" />
        <StatCard label="当前会话" value={sessionId || "未选择"} hint="当前工作 session" />
        <StatCard label="事件数" value={detail?.event_count ?? 0} hint="会话事件记录" />
        <StatCard label="错误标记" value={detail?.has_errors ? "有" : "无"} hint="是否存在错误日志" />
      </div>

      <div className="two-column">
        <Panel title="发起任务" eyebrow="Pipeline">
          {activeProjectId ? (
            <p className="body-copy">当前会把新 session 关联到项目 `{activeProjectId}`。</p>
          ) : (
            <p className="body-copy">当前未指定项目，新 session 将只进入全局运行历史。</p>
          )}
          <form className="form-grid" onSubmit={onSubmit}>
            <label className="full-span">
              文献综述主题
              <textarea value={topic} onChange={(event) => setTopic(event.target.value)} rows={4} required />
            </label>
            <label>
              运行模式
              <select value={runMode} onChange={(event) => setRunMode(event.target.value)}>
                <option value="mock">mock</option>
                <option value="real">real</option>
              </select>
            </label>
            <label>
              模型
              <input value={model} onChange={(event) => setModel(event.target.value)} placeholder="real 模式必填" />
            </label>
            <label className="full-span">
              Base URL
              <input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} placeholder="https://..." />
            </label>
            <label className="full-span">
              API Key
              <input value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="real 模式必填" />
            </label>
            <button className="primary-button" disabled={isPending || !topic.trim()} type="submit">
              {isPending ? "任务运行中..." : "开始生成"}
            </button>
          </form>
        </Panel>

        <Panel title="会话列表" eyebrow="Runs">
          {sessions.length === 0 ? (
            <EmptyState title="还没有运行会话" body="先发起一次任务，这里会显示新建 session 和历史记录。" />
          ) : (
            <ul className="entity-list">
              {sessions.slice(0, 12).map((candidateId) => (
                <li key={candidateId}>
                  <button
                    className={`list-button${sessionId === candidateId ? " active" : ""}`}
                    onClick={() => {
                      setHistorySessionId(candidateId);
                      openSession(candidateId).catch((loadError) =>
                        setError(loadError instanceof Error ? loadError.message : "无法切换会话。"),
                      );
                    }}
                    type="button"
                  >
                    <strong>{candidateId}</strong>
                    <p>查看详情、重放事件流或删除该 session。</p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <Panel
        title="运行摘要"
        eyebrow="Session"
        actions={
          <div className="panel-actions">
            <button className="secondary-button" disabled={isPending || !sessionId} onClick={onReplaySession} type="button">
              重放事件流
            </button>
            <button
              className="secondary-button"
              disabled={isPending || !sessionId}
              onClick={() => onDeleteSession(sessionId)}
              type="button"
            >
              删除会话
            </button>
          </div>
        }
      >
        <div className="detail-grid">
          <div>
            <span className="muted-label">Session ID</span>
            <p>{sessionId || "尚未创建"}</p>
          </div>
          <div>
            <span className="muted-label">事件数</span>
            <p>{detail?.event_count ?? 0}</p>
          </div>
          <div>
            <span className="muted-label">消息数</span>
            <p>{detail?.message_count ?? 0}</p>
          </div>
          <div>
            <span className="muted-label">错误标记</span>
            <p>{detail?.has_errors ? "是" : "否"}</p>
          </div>
          <div className="full-span">
            <span className="muted-label">输出文件</span>
            <p>{detail ? Object.keys(detail.output_files).join(" / ") || "暂无输出文件" : "暂无"}</p>
          </div>
        </div>
      </Panel>

      <Panel title="事件流" eyebrow="Streaming">
        {events.length === 0 ? (
          <EmptyState title="还没有事件流" body="创建新任务，或者选中一个已有 session 后点击“重放事件流”。" />
        ) : (
          <ul className="result-list">
            {events.map((streamEvent, index) => (
              <li key={`${streamEvent.event}-${index}`}>
                <div className="result-topline">
                  <strong>{streamEvent.event}</strong>
                </div>
                <p>{streamEvent.data}</p>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
