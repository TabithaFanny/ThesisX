"use client";

import { FormEvent, useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import { buildRagIndex, getProjects, getRagIndexStatus, searchRag } from "../lib/api";
import { getActiveProjectId, setActiveProjectId } from "../lib/project-context";
import type { Project, RagIndexStatus, RagResult } from "../lib/types";
import { EmptyState, ErrorState, Panel } from "./ui";

export function RagWorkspace() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [status, setStatus] = useState<RagIndexStatus | null>(null);
  const [results, setResults] = useState<RagResult[]>([]);
  const [query, setQuery] = useState("");
  const [projectId, setProjectId] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    getProjects()
      .then((projectData) => {
        const activeProjectId = searchParams.get("project_id") || getActiveProjectId();
        setProjects(projectData);
        if (activeProjectId) {
          setProjectId(activeProjectId);
        } else {
          setProjectId("");
        }
      })
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "无法读取项目列表。"),
      );
  }, [searchParams]);

  useEffect(() => {
    setActiveProjectId(projectId);
    getRagIndexStatus(projectId || undefined)
      .then((indexStatus) => setStatus(indexStatus))
      .catch((loadError) =>
      setError(loadError instanceof Error ? loadError.message : "无法读取项目索引状态。"),
    );
  }, [projectId]);

  function onBuild() {
    startTransition(async () => {
      try {
        await buildRagIndex(projectId || undefined);
        setStatus(await getRagIndexStatus(projectId || undefined));
      } catch (buildError) {
        setError(buildError instanceof Error ? buildError.message : "无法重建索引。");
      }
    });
  }

  function onSearch(event: FormEvent) {
    event.preventDefault();
    startTransition(async () => {
      try {
        const data = await searchRag({ query, project_id: projectId || undefined, top_k: 8 });
        setResults(data);
        setStatus(await getRagIndexStatus(projectId || undefined));
      } catch (searchError) {
        setError(searchError instanceof Error ? searchError.message : "检索失败。");
      }
    });
  }

  return (
    <div className="stack">
      {error ? <ErrorState message={error} /> : null}
      <Panel
        title="索引状态"
        eyebrow="RAG"
        actions={
          <button className="primary-button" disabled={isPending} onClick={onBuild} type="button">
            {isPending ? "处理中..." : "Build / Rebuild"}
          </button>
        }
      >
        <div className="detail-grid">
          <div>
            <span className="muted-label">Chunk 数量</span>
            <p>{status?.size ?? 0}</p>
          </div>
          <div>
            <span className="muted-label">状态信息</span>
            <p>{status?.message ?? "等待加载"}</p>
          </div>
          <label className="full-span">
            项目过滤（可选）
            <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
              <option value="">全部项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </Panel>

      <Panel title="检索" eyebrow="Search">
        <form className="inline-form wide" onSubmit={onSearch}>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="输入自然语言问题或关键词" />
          <button className="primary-button" disabled={isPending || !query.trim()} type="submit">
            搜索
          </button>
        </form>
        {results.length === 0 ? (
          <EmptyState title="暂无检索结果" body="先 build 索引，再输入检索词；结果会显示来源和片段。" />
        ) : (
          <ul className="result-list">
            {results.map((result) => (
              <li key={result.chunk_id}>
                <div className="result-topline">
                  <strong>{result.source_title}</strong>
                  <span>{result.score.toFixed(2)}</span>
                </div>
                <p>{result.text}</p>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
