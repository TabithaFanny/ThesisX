"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState, useTransition } from "react";

import { createProject, getProjects } from "../lib/api";
import { setActiveProjectId } from "../lib/project-context";
import type { Project } from "../lib/types";
import { EmptyState, ErrorState, Panel } from "./ui";

export function ProjectsWorkspace() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [question, setQuestion] = useState("");
  const [discipline, setDiscipline] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  async function reload() {
    const data = await getProjects();
    setProjects(data);
  }

  useEffect(() => {
    reload().catch((loadError) =>
      setError(loadError instanceof Error ? loadError.message : "无法加载项目列表。"),
    );
  }, []);

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    startTransition(async () => {
      try {
        await createProject({
          name,
          research_question: question || null,
          discipline: discipline || null,
        });
        setName("");
        setQuestion("");
        setDiscipline("");
        await reload();
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "无法创建项目。");
      }
    });
  }

  return (
    <div className="stack">
      {error ? <ErrorState message={error} /> : null}
      <div className="two-column">
        <Panel title="新建项目" eyebrow="Projects">
          <form className="form-grid" onSubmit={onSubmit}>
            <label>
              项目名称
              <input value={name} onChange={(event) => setName(event.target.value)} required />
            </label>
            <label>
              学科
              <input value={discipline} onChange={(event) => setDiscipline(event.target.value)} />
            </label>
            <label className="full-span">
              研究问题
              <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={4} />
            </label>
            <button className="primary-button" disabled={isPending} type="submit">
              {isPending ? "创建中..." : "创建项目"}
            </button>
          </form>
        </Panel>

        <Panel title="项目列表" eyebrow="Workspace">
          {projects.length === 0 ? (
            <EmptyState title="还没有项目" body="创建第一个项目后，Workspace、文献、RAG 都会围绕它工作。" />
          ) : (
            <ul className="entity-list">
              {projects.map((project) => (
                <li key={project.id}>
                  <div>
                    <Link
                      className="entity-link"
                      href={`/projects/${project.id}`}
                      onClick={() => setActiveProjectId(project.id)}
                    >
                      {project.name}
                    </Link>
                    <p>{project.discipline || "未指定学科"}</p>
                  </div>
                  <span className="badge">{project.status}</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  );
}
