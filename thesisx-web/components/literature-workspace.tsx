"use client";

import { useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import {
  getLiterature,
  getProjects,
  runAgentRewrite,
  searchLiterature,
  structureLiteratureReference,
} from "../lib/api";
import { getActiveProjectId, setActiveProjectId } from "../lib/project-context";
import type { LiteratureReference, Project } from "../lib/types";
import { EmptyState, ErrorState, Panel } from "./ui";

export function LiteratureWorkspace() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<LiteratureReference[]>([]);
  const [selected, setSelected] = useState<LiteratureReference | null>(null);
  const [aiDigest, setAiDigest] = useState("");
  const [lastStructureMessage, setLastStructureMessage] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  async function load(nextQuery = "") {
    const data = nextQuery.trim() ? await searchLiterature(nextQuery.trim()) : await getLiterature();
    setItems(data);
    setSelected((current) => data.find((item) => item.id === current?.id) ?? data[0] ?? null);
  }

  useEffect(() => {
    Promise.all([getProjects(), getLiterature()])
      .then(([projectData, literatureData]) => {
        const activeProjectId = searchParams.get("project_id") || getActiveProjectId();
        setProjects(projectData);
        setProjectId(activeProjectId);
        setItems(literatureData);
        setSelected(literatureData[0] ?? null);
      })
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "无法加载文献。"),
      );
  }, [searchParams]);

  useEffect(() => {
    setActiveProjectId(projectId);
  }, [projectId]);

  function onGenerateDigest() {
    const sourceText = selected?.abstract || selected?.title || "";
    if (!sourceText.trim()) {
      setError("当前文献没有可供 AI 提炼的摘要内容。");
      return;
    }
    startTransition(async () => {
      try {
        const result = await runAgentRewrite({
          task_type: "knowledge",
          selected_text: sourceText,
          mode: "polish",
          project_id: projectId,
          query: selected?.title || "",
          extra_context: `${selected?.title || ""}\n${selected?.authors.join(", ") || ""}`,
        });
        setAiDigest(result.rewritten);
      } catch (rewriteError) {
        setError(rewriteError instanceof Error ? rewriteError.message : "无法生成文献提炼。");
      }
    });
  }

  function onStructureReference() {
    if (!selected) {
      setError("请先选择一条文献，再生成结构化节点。");
      return;
    }
    startTransition(async () => {
      try {
        const result = await structureLiteratureReference(selected.id, projectId || undefined);
        setLastStructureMessage(
          `已为《${selected.title}》生成 ${result.items.length} 个结构化节点，并写入知识库。`,
        );
      } catch (structureError) {
        setError(structureError instanceof Error ? structureError.message : "无法生成结构化节点。");
      }
    });
  }

  return (
    <div className="two-column wide-right">
      <Panel
        title="文献列表"
        eyebrow="Literature"
        actions={
          <div className="stack tight">
            <label>
              项目上下文
              <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
                <option value="">不绑定项目</option>
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
                load(query).catch((loadError) =>
                  setError(loadError instanceof Error ? loadError.message : "搜索失败。"),
                );
              }}
            >
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索标题、作者、摘要" />
              <button className="secondary-button" type="submit">
                搜索
              </button>
            </form>
          </div>
        }
      >
        {error ? <ErrorState message={error} /> : null}
        {items.length === 0 ? (
          <EmptyState title="没有匹配文献" body="可以先导入 BibTeX，或者先不带搜索词查看全部文献。" />
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
                  <p>{item.authors.join(", ") || "未知作者"}</p>
                </div>
                <span className="badge">{item.year || "n.d."}</span>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <Panel
        title="文献详情"
        eyebrow="Detail"
        actions={
          <div className="panel-actions">
            <button
              className="secondary-button"
              disabled={isPending || !selected}
              onClick={onGenerateDigest}
              type="button"
            >
              生成 AI 提炼
            </button>
            <button
              className="secondary-button"
              disabled={isPending || !selected}
              onClick={onStructureReference}
              type="button"
            >
              结构化入库
            </button>
          </div>
        }
      >
        {!selected ? (
          <EmptyState title="请选择一条文献" body="左侧选中文献后，这里会显示摘要、期刊和标签。" />
        ) : (
          <div className="stack tight">
            <div className="detail-stack">
              <div>
                <h4>{selected.title}</h4>
                <p>{selected.authors.join(", ") || "未知作者"}</p>
              </div>
              <div className="detail-grid">
                <div>
                  <span className="muted-label">年份</span>
                  <p>{selected.year || "未提供"}</p>
                </div>
                <div>
                  <span className="muted-label">期刊</span>
                  <p>{selected.journal || "未提供"}</p>
                </div>
                <div className="full-span">
                  <span className="muted-label">标签</span>
                  <p>{selected.tags.length ? selected.tags.join(", ") : "暂无标签"}</p>
                </div>
              </div>
              <div>
                <span className="muted-label">摘要</span>
                <p className="body-copy">{selected.abstract || "暂无摘要。"}</p>
              </div>
            </div>
            <div className="top-divider detail-stack">
              <span className="muted-label">AI 提炼</span>
              {aiDigest ? (
                <pre className="code-block">{aiDigest}</pre>
              ) : (
                <p className="body-copy">把当前摘要先压成一段更易转入知识库或写作上下文的精炼版本。</p>
              )}
            </div>
            <div className="top-divider detail-stack">
              <span className="muted-label">结构化摘要入库</span>
              {lastStructureMessage ? (
                <p className="body-copy">{lastStructureMessage}</p>
              ) : (
                <p className="body-copy">把当前文献拆成 overview、background、method、findings、evidence 节点，直接写入知识库。</p>
              )}
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}
