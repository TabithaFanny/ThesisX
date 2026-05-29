"use client";

import { FormEvent, useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import { AgentArtifactPanel } from "./agent-artifact-panel";
import {
  applyInsertPreview,
  buildInsertPreview,
  exportDocx,
  getAgentArtifact,
  getPipelineSessionPaper,
  getProjectRuns,
  getProjects,
  parseEditorHeadings,
  recordAgentFeedback,
} from "../lib/api";
import { getActiveProjectId, getHistorySessionId, setActiveProjectId, setHistorySessionId } from "../lib/project-context";
import type { AgentArtifact, InsertPreview, Project } from "../lib/types";
import { EmptyState, ErrorState, Panel, StatCard } from "./ui";

function draftStorageKey(projectId: string) {
  return `thesisx.writing.draft.${projectId || "global"}`;
}

export function WritingWorkspace() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [sessions, setSessions] = useState<string[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [title, setTitle] = useState("论文草稿");
  const [markdown, setMarkdown] = useState("");
  const [previews, setPreviews] = useState<InsertPreview[]>([]);
  const [selectedPreviewSections, setSelectedPreviewSections] = useState<string[]>([]);
  const [aiResult, setAiResult] = useState<AgentArtifact | null>(null);
  const [lastMessage, setLastMessage] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  async function loadSessions(nextProjectId: string) {
    const runs = nextProjectId ? await getProjectRuns(nextProjectId) : [];
    setSessions(runs);
    const preferred = getHistorySessionId();
    setSelectedSessionId(runs.includes(preferred) ? preferred : runs[0] ?? "");
  }

  useEffect(() => {
    getProjects()
      .then((projectData) => {
        const activeProjectId = searchParams.get("project_id") || getActiveProjectId();
        setProjects(projectData);
        setProjectId(activeProjectId);
      })
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "无法加载写作工作区。"),
      );
  }, [searchParams]);

  useEffect(() => {
    setActiveProjectId(projectId);
    const saved = window.localStorage.getItem(draftStorageKey(projectId)) || "";
    setMarkdown(saved);
    loadSessions(projectId).catch((loadError) =>
      setError(loadError instanceof Error ? loadError.message : "无法加载项目运行记录。"),
    );
  }, [projectId]);

  useEffect(() => {
    window.localStorage.setItem(draftStorageKey(projectId), markdown);
  }, [markdown, projectId]);

  function onRewrite(mode: "polish" | "expand" | "add_theory" | "add_evidence") {
    const sourceText = markdown.trim();
    if (!sourceText) {
      setError("请先写入或导入草稿内容，再发起 AI 改写。");
      return;
    }
    startTransition(async () => {
      try {
        const result = await getAgentArtifact({
          task_type: "writing",
          selected_text: sourceText,
          mode,
          project_id: projectId,
          session_id: selectedSessionId,
          query: `rewrite_mode=${mode}`,
          extra_context: `title=${title}`,
        });
        setAiResult(result);
        setLastMessage("AI 草稿已生成。可以直接替换当前草稿。");
      } catch (rewriteError) {
        setError(rewriteError instanceof Error ? rewriteError.message : "无法生成 AI 草稿。");
      }
    });
  }

  function onImportSessionPaper() {
    if (!selectedSessionId) {
      setError("请先选择一个 session。");
      return;
    }
    startTransition(async () => {
      try {
        const paper = await getPipelineSessionPaper(selectedSessionId);
        setMarkdown(paper.markdown);
        setHistorySessionId(selectedSessionId);
        setLastMessage(`已导入 session ${selectedSessionId} 的 paper.md。`);
      } catch (paperError) {
        setError(paperError instanceof Error ? paperError.message : "无法导入 session 论文。");
      }
    });
  }

  function onBuildInsertPreview() {
    if (!markdown.trim() || !selectedSessionId) {
      setError("请先准备当前草稿，并选择一个 session 论文。");
      return;
    }
    startTransition(async () => {
      try {
        const [sections, paper] = await Promise.all([
          parseEditorHeadings(markdown),
          getPipelineSessionPaper(selectedSessionId),
        ]);
        const nextPreviews = await buildInsertPreview({
          paper_text: paper.markdown,
          editor_sections: sections,
        });
        setPreviews(nextPreviews);
        setSelectedPreviewSections(nextPreviews.map((item) => item.section_title));
        setLastMessage("已生成结构插入预览。可以选择要合并的章节。");
      } catch (previewError) {
        setError(previewError instanceof Error ? previewError.message : "无法生成插入预览。");
      }
    });
  }

  function onApplyPreview() {
    if (!previews.length) {
      setError("当前没有可应用的结构预览。");
      return;
    }
    startTransition(async () => {
      try {
        const result = await applyInsertPreview({
          editor_content: markdown,
          previews,
          selected: selectedPreviewSections,
        });
        setMarkdown(result.new_content);
        setLastMessage("已将选中的章节结构合并到当前草稿。");
      } catch (applyError) {
        setError(applyError instanceof Error ? applyError.message : "无法应用结构预览。");
      }
    });
  }

  function onReplaceWithAi() {
    if (!aiResult?.markdown.trim()) {
      setError("当前没有 AI 草稿可替换。");
      return;
    }
    setMarkdown(aiResult.markdown);
    setLastMessage("已用 AI 草稿替换当前写作内容。");
  }

  function onFeedback(accepted: boolean) {
    if (!aiResult) {
      return;
    }
    startTransition(async () => {
      try {
        await recordAgentFeedback({
          task_type: "writing",
          accepted,
          signal: accepted
            ? `Accepted writing artifact (${aiResult.metadata.mode || "unknown"})`
            : `Rejected writing artifact (${aiResult.metadata.mode || "unknown"})`,
        });
        setLastMessage(accepted ? "已记录：本次写作结果被接受。" : "已记录：本次写作结果被拒绝。");
      } catch (feedbackError) {
        setError(feedbackError instanceof Error ? feedbackError.message : "无法记录反馈。");
      }
    });
  }

  function onExportDocx(event: FormEvent) {
    event.preventDefault();
    if (!markdown.trim()) {
      setError("请先写入草稿内容，再导出 DOCX。");
      return;
    }
    startTransition(async () => {
      try {
        const blob = await exportDocx({ title, markdown });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${title || "论文草稿"}.docx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        setLastMessage("DOCX 已导出并开始下载。");
      } catch (exportError) {
        setError(exportError instanceof Error ? exportError.message : "无法导出 DOCX。");
      }
    });
  }

  return (
    <div className="stack">
      {error ? <ErrorState message={error} /> : null}
      <div className="stats-grid">
        <StatCard label="当前项目" value={projectId || "未指定"} />
        <StatCard label="可导入 Session" value={sessions.length} />
        <StatCard label="预览章节" value={previews.length} />
        <StatCard label="状态" value={lastMessage || "编辑中"} />
      </div>

      <div className="two-column">
        <Panel title="写作控制台" eyebrow="Writing">
          <div className="compact-form">
            <label className="full-span">
              项目
              <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
                <option value="">未指定</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="full-span">
              Session 论文
              <select value={selectedSessionId} onChange={(event) => setSelectedSessionId(event.target.value)}>
                <option value="">选择 session</option>
                {sessions.map((sessionId) => (
                  <option key={sessionId} value={sessionId}>
                    {sessionId}
                  </option>
                ))}
              </select>
            </label>
            <div className="panel-actions">
              <button className="secondary-button" disabled={isPending || !selectedSessionId} onClick={onImportSessionPaper} type="button">
                导入 paper.md
              </button>
              <button className="secondary-button" disabled={isPending || !selectedSessionId || !markdown.trim()} onClick={onBuildInsertPreview} type="button">
                生成结构预览
              </button>
              <button className="secondary-button" disabled={isPending || !previews.length} onClick={onApplyPreview} type="button">
                应用结构合并
              </button>
            </div>
          </div>
          {previews.length === 0 ? (
            <EmptyState title="还没有结构预览" body="选一个 session 并准备当前草稿后，可以生成章节级插入预览。" />
          ) : (
            <ul className="entity-list selectable">
              {previews.map((preview) => {
                const checked = selectedPreviewSections.includes(preview.section_title);
                return (
                  <li
                    key={preview.section_title}
                    className={checked ? "selected" : ""}
                    onClick={() =>
                      setSelectedPreviewSections((current) =>
                        current.includes(preview.section_title)
                          ? current.filter((item) => item !== preview.section_title)
                          : [...current, preview.section_title],
                      )
                    }
                  >
                    <div>
                      <strong>{preview.section_title}</strong>
                      <p>{preview.action}{preview.target_section ? ` -> ${preview.target_section}` : ""}</p>
                    </div>
                    <span className="badge">{preview.level}</span>
                  </li>
                );
              })}
            </ul>
          )}
        </Panel>

        <Panel title="AI 改写助手" eyebrow="Rewrite">
          <div className="panel-actions">
            <button className="secondary-button" disabled={isPending || !markdown.trim()} onClick={() => onRewrite("polish")} type="button">
              润色
            </button>
            <button className="secondary-button" disabled={isPending || !markdown.trim()} onClick={() => onRewrite("expand")} type="button">
              扩写
            </button>
            <button className="secondary-button" disabled={isPending || !markdown.trim()} onClick={() => onRewrite("add_theory")} type="button">
              补理论
            </button>
            <button className="secondary-button" disabled={isPending || !markdown.trim()} onClick={() => onRewrite("add_evidence")} type="button">
              补证据
            </button>
          </div>
          {aiResult ? (
            <AgentArtifactPanel
              artifact={aiResult}
              primaryActionLabel="替换当前草稿"
              onPrimaryAction={onReplaceWithAi}
              onAccept={() => onFeedback(true)}
              onReject={() => onFeedback(false)}
            />
          ) : (
            <EmptyState title="还没有 AI 草稿" body="对当前写作内容发起润色、扩写、补理论或补证据后，这里会出现可替换的草稿。" />
          )}
        </Panel>
      </div>

      <Panel title="Markdown 草稿" eyebrow="Editor">
        <form className="form-grid" onSubmit={onExportDocx}>
          <label className="full-span">
            标题
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label className="full-span">
            草稿内容
            <textarea
              value={markdown}
              onChange={(event) => setMarkdown(event.target.value)}
              rows={22}
              placeholder="# 摘要&#10;&#10;在这里写作，或从 pipeline session 导入论文草稿。"
            />
          </label>
          <button className="primary-button" disabled={isPending || !markdown.trim()} type="submit">
            导出 DOCX
          </button>
        </form>
      </Panel>
    </div>
  );
}
