"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { getProjects } from "../lib/api";
import { getActiveProjectId, setActiveProjectId } from "../lib/project-context";
import type { Project } from "../lib/types";

const NAV_ITEMS = [
  { href: "/", label: "Workspace" },
  { href: "/projects", label: "项目" },
  { href: "/knowledge", label: "知识库" },
  { href: "/theory", label: "理论" },
  { href: "/evidence", label: "证据" },
  { href: "/literature", label: "文献" },
  { href: "/rag", label: "RAG" },
  { href: "/pipeline", label: "AI 助手" },
  { href: "/writing", label: "写作" },
  { href: "/history", label: "运行记录" },
  { href: "/quality", label: "质量" },
  { href: "/export", label: "导出" },
  { href: "/settings", label: "设置" },
];

export function AppShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectIdState] = useState("");

  useEffect(() => {
    let active = true;
    getProjects()
      .then((data) => {
        if (!active) {
          return;
        }
        setProjects(data);
        setActiveProjectIdState(getActiveProjectId());
      })
      .catch(() => {
        if (active) {
          setProjects([]);
        }
      });
    return () => {
      active = false;
    };
  }, [pathname]);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">ThesisX</p>
          <h1>Web Workspace</h1>
          <p className="sidebar-copy">本地优先论文 AI 工作台</p>
        </div>
        <div className="sidebar-project-switcher">
          <label>
            当前项目
            <select
              value={activeProjectId}
              onChange={(event) => {
                const nextId = event.target.value;
                setActiveProjectId(nextId);
                setActiveProjectIdState(nextId);
              }}
            >
              <option value="">未指定</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          {activeProjectId ? (
            <Link className="secondary-link" href={`/projects/${activeProjectId}`}>
              打开当前项目
            </Link>
          ) : null}
        </div>
        <nav className="nav">
          {NAV_ITEMS.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link key={item.href} className={active ? "active" : ""} href={item.href}>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <section className="content">
        <header className="page-header">
          <div>
            <p className="eyebrow">ThesisX V5.0</p>
            <h2>{title}</h2>
            {subtitle ? <p className="lead">{subtitle}</p> : null}
          </div>
        </header>
        {children}
      </section>
    </main>
  );
}
