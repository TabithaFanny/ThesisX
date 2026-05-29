"use client";

import { FormEvent, useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import { AgentArtifactPanel } from "./agent-artifact-panel";
import {
  createKnowledgeItem,
  getAgentArtifact,
  getKnowledgeItems,
  getProjects,
  recordAgentFeedback,
  searchKnowledge,
} from "../lib/api";
import { getActiveProjectId, setActiveProjectId } from "../lib/project-context";
import type { AgentArtifact, KnowledgeItem, Project } from "../lib/types";
import { EmptyState, ErrorState, Panel } from "./ui";

export function KnowledgeWorkspace() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [selected, setSelected] = useState<KnowledgeItem | null>(null);
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [itemType, setItemType] = useState("note");
  const [aiDraft, setAiDraft] = useState<AgentArtifact | null>(null);
  const [aiDraftTitle, setAiDraftTitle] = useState("");
  const [aiDraftType, setAiDraftType] = useState("note");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  async function load(nextQuery: string, nextProjectId: string) {
    let data = nextQuery.trim()
      ? await searchKnowledge(nextQuery.trim())
      : await getKnowledgeItems(nextProjectId || undefined);
    if (nextProjectId) {
      data = data.filter((item) => item.project_id === nextProjectId);
    }
    setItems(data);
    setSelected((current) => data.find((item) => item.id === current?.id) ?? data[0] ?? null);
  }

  useEffect(() => {
    getProjects()
      .then((projectData) => {
        const activeProjectId = searchParams.get("project_id") || getActiveProjectId();
        const nextItemType = searchParams.get("item_type");
        const nextTitle = searchParams.get("title");
        setProjects(projectData);
        if (nextItemType) {
          setItemType(nextItemType);
        }
        if (nextTitle) {
          setTitle(nextTitle);
        }
        if (activeProjectId) {
          setProjectId(activeProjectId);
        } else {
          setProjectId("");
        }
      })
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "无法加载知识条目。"),
      );
  }, [searchParams]);

  useEffect(() => {
    setActiveProjectId(projectId);
    load(appliedQuery, projectId).catch((loadError) =>
      setError(loadError instanceof Error ? loadError.message : "无法加载知识条目。"),
    );
  }, [appliedQuery, projectId]);

  function onCreate(event: FormEvent) {
    event.preventDefault();
    startTransition(async () => {
      try {
        await createKnowledgeItem({
          item_type: itemType,
          title,
          content,
          tags: [],
          source_file: "",
          project_id: projectId || null,
          external_source: "manual",
        });
        setTitle("");
        setContent("");
        await load(appliedQuery, projectId);
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "无法创建知识条目。");
      }
    });
  }

  function getSourceText() {
    return selected?.content || content || "";
  }

  function buildDraftTitle(mode: "polish" | "expand" | "add_theory" | "add_evidence") {
    const baseTitle = selected?.title || title || "AI 知识草稿";
    if (mode === "add_theory") {
      return `${baseTitle} · 理论补强`;
    }
    if (mode === "add_evidence") {
      return `${baseTitle} · 证据补强`;
    }
    if (mode === "expand") {
      return `${baseTitle} · 扩写稿`;
    }
    return `${baseTitle} · 润色稿`;
  }

  function buildDraftType(mode: "polish" | "expand" | "add_theory" | "add_evidence") {
    if (mode === "add_theory") {
      return "theory";
    }
    if (mode === "add_evidence") {
      return "evidence";
    }
    return selected?.item_type || itemType || "note";
  }

  function onGenerateDraft(mode: "polish" | "expand" | "add_theory" | "add_evidence") {
    const sourceText = getSourceText();
    if (!sourceText.trim()) {
      setError("请先选择一个知识条目，或先在右侧输入内容，再发起 AI 加工。");
      return;
    }
    startTransition(async () => {
      try {
        const result = await getAgentArtifact({
          task_type: "knowledge",
          selected_text: sourceText,
          mode,
          project_id: projectId,
          query: selected?.title || title || "",
          extra_context: [
            `title=${selected?.title || title || ""}`,
            `item_type=${selected?.item_type || itemType || "note"}`,
            `project_id=${projectId || ""}`,
          ].join("\n"),
        });
        setAiDraft(result);
        setAiDraftTitle(buildDraftTitle(mode));
        setAiDraftType(buildDraftType(mode));
      } catch (rewriteError) {
        setError(rewriteError instanceof Error ? rewriteError.message : "无法生成 AI 草稿。");
      }
    });
  }

  function onLoadDraftIntoForm() {
    if (!aiDraft?.markdown.trim()) {
      setError("当前还没有可载入的 AI 草稿。");
      return;
    }
    setTitle(aiDraftTitle || title || "AI 知识草稿");
    setItemType(aiDraftType || itemType || "note");
    setContent(aiDraft.markdown);
  }

  function onFeedback(accepted: boolean) {
    if (!aiDraft) {
      return;
    }
    startTransition(async () => {
      try {
        await recordAgentFeedback({
          task_type: "knowledge",
          project_id: projectId,
          accepted,
          signal: accepted ? "知识草稿可入库" : "知识草稿还不够可用",
        });
      } catch (feedbackError) {
        setError(feedbackError instanceof Error ? feedbackError.message : "无法记录反馈。");
      }
    });
  }

  return (
    <div className="stack">
      {error ? <ErrorState message={error} /> : null}
      <div className="two-column">
        <Panel
          title="知识条目"
          eyebrow="Knowledge Base"
          actions={
            <div className="stack tight">
              <label>
                项目过滤
                <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
                  <option value="">全部项目</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </label>
              <form
                className="inline-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  setAppliedQuery(query);
                  load(query, projectId).catch((loadError) =>
                    setError(loadError instanceof Error ? loadError.message : "搜索失败。"),
                  );
                }}
              >
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索标题或内容" />
                <button className="secondary-button" type="submit">
                  搜索
                </button>
              </form>
            </div>
          }
        >
          {items.length === 0 ? (
            <EmptyState title="还没有知识条目" body="先创建一条 note、theory 或 evidence，RAG 才有数据可用。" />
          ) : (
            <ul className="entity-list selectable">
              {items.map((item) => (
                <li
                  key={item.id}
                  className={selected?.id === item.id ? "selected" : ""}
                  onClick={() => setSelected(item)}
                >
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.content.slice(0, 56) || "无正文摘要"}</p>
                  </div>
                  <span className="badge">{item.item_type}</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel
          title="新建 / 详情"
          eyebrow="Knowledge"
          actions={
            <div className="panel-actions">
              <button
                className="secondary-button"
                disabled={isPending}
                onClick={() => onGenerateDraft("polish")}
                type="button"
              >
                AI 润色
              </button>
              <button
                className="secondary-button"
                disabled={isPending}
                onClick={() => onGenerateDraft("expand")}
                type="button"
              >
                AI 扩写
              </button>
              <button
                className="secondary-button"
                disabled={isPending}
                onClick={() => onGenerateDraft("add_theory")}
                type="button"
              >
                转理论稿
              </button>
              <button
                className="secondary-button"
                disabled={isPending}
                onClick={() => onGenerateDraft("add_evidence")}
                type="button"
              >
                转证据稿
              </button>
            </div>
          }
        >
          <form className="form-grid" onSubmit={onCreate}>
            <label>
              类型
              <select value={itemType} onChange={(event) => setItemType(event.target.value)}>
                <option value="note">note</option>
                <option value="theory">theory</option>
                <option value="evidence">evidence</option>
                <option value="literature">literature</option>
              </select>
            </label>
            <label>
              归属项目
              <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
                <option value="">不绑定项目</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="full-span">
              标题
              <input value={title} onChange={(event) => setTitle(event.target.value)} required />
            </label>
            <label className="full-span">
              内容
              <textarea value={content} onChange={(event) => setContent(event.target.value)} rows={8} />
            </label>
            <button className="primary-button" disabled={isPending} type="submit">
              {isPending ? "保存中..." : "创建条目"}
            </button>
          </form>

          {selected ? (
            <div className="detail-stack top-divider">
              <h4>{selected.title}</h4>
              <p className="body-copy">{selected.project_id ? `项目: ${selected.project_id}` : "未绑定项目"}</p>
              <p className="body-copy">{selected.content || "暂无内容。"}</p>
            </div>
          ) : null}

          <div className="detail-stack top-divider">
            <div className="panel-header">
              <div>
                <span className="muted-label">AI 草稿</span>
                <h4>{aiDraftTitle || "等待生成"}</h4>
              </div>
              <div className="panel-actions">
                <button
                  className="secondary-button"
                  disabled={!aiDraft?.markdown.trim()}
                  onClick={onLoadDraftIntoForm}
                  type="button"
                >
                  载入到表单
                </button>
              </div>
            </div>
            {aiDraft ? (
              <AgentArtifactPanel
                artifact={aiDraft}
                acceptLabel="接受结果"
                rejectLabel="拒绝结果"
                onAccept={() => onFeedback(true)}
                onReject={() => onFeedback(false)}
              />
            ) : (
              <p className="body-copy">选中一个知识条目后，可以直接让 AI 做润色、扩写，或转换成 theory / evidence 草稿。</p>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}
