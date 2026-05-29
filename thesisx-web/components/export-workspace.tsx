"use client";

import { FormEvent, useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import {
  exportDocx,
  exportSessionArchive,
  getCitationExport,
  getPipelineSessions,
  getProjectRuns,
  getProjects,
} from "../lib/api";
import { getActiveProjectId, getHistorySessionId, setActiveProjectId } from "../lib/project-context";
import type { Project } from "../lib/types";
import { EmptyState, ErrorState, Panel, StatCard } from "./ui";

export function ExportWorkspace() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [sessions, setSessions] = useState<string[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [citationFormat, setCitationFormat] = useState<"bibtex" | "ris" | "csl_json">("bibtex");
  const [citationContent, setCitationContent] = useState("");
  const [docTitle, setDocTitle] = useState("论文草稿");
  const [docMarkdown, setDocMarkdown] = useState("");
  const [lastExportMessage, setLastExportMessage] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  function downloadBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function downloadText(text: string, filename: string, mimeType: string) {
    const blob = new Blob([text], { type: mimeType });
    downloadBlob(blob, filename);
  }

  async function loadSessions(nextProjectId: string) {
    const data = nextProjectId ? await getProjectRuns(nextProjectId) : await getPipelineSessions();
    setSessions(data);
    const preferred = getHistorySessionId();
    setSelectedSessionId(data.includes(preferred) ? preferred : data[0] ?? "");
  }

  useEffect(() => {
    let active = true;
    getProjects()
      .then((projectData) => {
        if (!active) {
          return;
        }
        const nextProjectId = searchParams.get("project_id") || getActiveProjectId();
        setProjects(projectData);
        if (nextProjectId) {
          setProjectId(nextProjectId);
        }
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "无法加载导出工作区。");
        }
      });
    return () => {
      active = false;
    };
  }, [searchParams]);

  useEffect(() => {
    setActiveProjectId(projectId);
    loadSessions(projectId).catch((loadError) =>
      setError(loadError instanceof Error ? loadError.message : "无法加载运行会话。"),
    );
  }, [projectId]);

  function onLoadCitations() {
    startTransition(async () => {
      try {
        const data = await getCitationExport(citationFormat);
        setCitationContent(data.content);
        setLastExportMessage(`引文内容已生成，可直接下载 ${citationFormat} 文件。`);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "无法导出引文。");
      }
    });
  }

  function onExportDocx(event: FormEvent) {
    event.preventDefault();
    startTransition(async () => {
      try {
        const blob = await exportDocx({ title: docTitle, markdown: docMarkdown });
        downloadBlob(blob, `${docTitle || "论文草稿"}.docx`);
        setLastExportMessage(`DOCX 已生成并开始下载，大小 ${blob.size} bytes。`);
      } catch (exportError) {
        setError(exportError instanceof Error ? exportError.message : "无法导出 DOCX。");
      }
    });
  }

  function onArchiveSession() {
    if (!selectedSessionId) {
      setError("请先选择一个 session。");
      return;
    }
    startTransition(async () => {
      try {
        const blob = await exportSessionArchive(selectedSessionId);
        downloadBlob(blob, `${selectedSessionId}.zip`);
        setLastExportMessage(`Session archive 已生成并开始下载，大小 ${blob.size} bytes。`);
      } catch (archiveError) {
        setError(archiveError instanceof Error ? archiveError.message : "无法归档 session。");
      }
    });
  }

  return (
    <div className="stack">
      {error ? <ErrorState message={error} /> : null}
      <div className="stats-grid">
        <StatCard label="当前项目" value={projectId || "未指定"} />
        <StatCard label="可归档 Session" value={sessions.length} />
        <StatCard label="引文格式" value={citationFormat} />
        <StatCard label="导出状态" value={lastExportMessage || "未执行"} />
      </div>

      <div className="two-column">
        <Panel title="引文导出" eyebrow="Citations">
          <div className="compact-form">
            <select value={citationFormat} onChange={(event) => setCitationFormat(event.target.value as "bibtex" | "ris" | "csl_json")}>
              <option value="bibtex">bibtex</option>
              <option value="ris">ris</option>
              <option value="csl_json">csl_json</option>
            </select>
            <button className="primary-button" disabled={isPending} onClick={onLoadCitations} type="button">
              生成引文内容
            </button>
            <button
              className="secondary-button"
              disabled={!citationContent}
              onClick={() =>
                downloadText(
                  citationContent,
                  `citations.${citationFormat === "csl_json" ? "json" : citationFormat}`,
                  citationFormat === "csl_json" ? "application/json" : "text/plain;charset=utf-8",
                )
              }
              type="button"
            >
              下载引文文件
            </button>
          </div>
          {citationContent ? <pre className="code-block">{citationContent}</pre> : <EmptyState title="还没有引文导出内容" body="选择格式后生成，便于检查当前文献库输出。" />}
        </Panel>

        <Panel title="Session 归档" eyebrow="Archive">
          <label className="full-span">
            项目
            <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
              <option value="">全部项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="full-span">
            Session
            <select value={selectedSessionId} onChange={(event) => setSelectedSessionId(event.target.value)}>
              <option value="">选择 session</option>
              {sessions.map((sessionId) => (
                <option key={sessionId} value={sessionId}>
                  {sessionId}
                </option>
              ))}
            </select>
          </label>
          <button className="secondary-button" disabled={isPending || !selectedSessionId} onClick={onArchiveSession} type="button">
            生成 session archive
          </button>
          {sessions.length === 0 ? <EmptyState title="没有可归档的 session" body="先在 AI 助手里跑一次任务，归档入口才会有内容。" /> : null}
        </Panel>
      </div>

      <Panel title="DOCX 导出" eyebrow="Document">
        <form className="form-grid" onSubmit={onExportDocx}>
          <label className="full-span">
            标题
            <input value={docTitle} onChange={(event) => setDocTitle(event.target.value)} />
          </label>
          <label className="full-span">
            Markdown
            <textarea value={docMarkdown} onChange={(event) => setDocMarkdown(event.target.value)} rows={12} placeholder="# 摘要&#10;&#10;在这里粘贴当前项目的 Markdown 草稿" />
          </label>
          <button className="primary-button" disabled={isPending || !docMarkdown.trim()} type="submit">
            生成 DOCX
          </button>
        </form>
      </Panel>
    </div>
  );
}
