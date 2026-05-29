"use client";

import { FormEvent, useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import { AgentArtifactPanel } from "./agent-artifact-panel";
import { getAgentArtifact, getProjects, getResearchQuestion, getTheories, matchTheory, recordAgentFeedback } from "../lib/api";
import { getActiveProjectId, setActiveProjectId } from "../lib/project-context";
import type { AgentArtifact, Project, ResearchQuestion, TheoryCandidate, TheoryDetail } from "../lib/types";
import { EmptyState, ErrorState, Panel, StatCard } from "./ui";

export function TheoryWorkspace() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [rq, setRq] = useState<ResearchQuestion | null>(null);
  const [theories, setTheories] = useState<TheoryDetail[]>([]);
  const [selected, setSelected] = useState<TheoryDetail | null>(null);
  const [matches, setMatches] = useState<TheoryCandidate[]>([]);
  const [query, setQuery] = useState("");
  const [aiDraft, setAiDraft] = useState<AgentArtifact | null>(null);
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    let active = true;
    Promise.all([getProjects(), getTheories()])
      .then(async ([projectData, theoryData]) => {
        const nextProjectId = searchParams.get("project_id") || getActiveProjectId();
        if (!active) {
          return;
        }
        setProjects(projectData);
        setTheories(theoryData);
        setSelected(theoryData[0] ?? null);
        if (nextProjectId) {
          setProjectId(nextProjectId);
          try {
            const researchQuestion = await getResearchQuestion(nextProjectId);
            if (active) {
              setRq(researchQuestion);
              setQuery(researchQuestion.question);
            }
          } catch {
            if (active) {
              setRq(null);
            }
          }
        }
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "无法加载理论工作区。");
        }
      });
    return () => {
      active = false;
    };
  }, [searchParams]);

  useEffect(() => {
    setActiveProjectId(projectId);
  }, [projectId]);

  function onMatch(event: FormEvent) {
    event.preventDefault();
    startTransition(async () => {
      try {
        const data = await matchTheory({ research_question: query, top_k: 5 });
        setMatches(data);
      } catch (matchError) {
        setError(matchError instanceof Error ? matchError.message : "理论匹配失败。");
      }
    });
  }

  function onGenerateTheoryDraft() {
    if (!query.trim()) {
      setError("请先输入研究问题，再生成理论分析草稿。");
      return;
    }
    startTransition(async () => {
      try {
        const result = await getAgentArtifact({
          task_type: "theory",
          selected_text: query,
          mode: "add_theory",
          project_id: projectId,
          query,
          extra_context: selected ? `${selected.name_zh} / ${selected.name_en}` : rq?.question || "",
        });
        setAiDraft(result);
      } catch (rewriteError) {
        setError(rewriteError instanceof Error ? rewriteError.message : "无法生成理论分析草稿。");
      }
    });
  }

  function onFeedback(accepted: boolean) {
    if (!aiDraft) {
      return;
    }
    startTransition(async () => {
      try {
        await recordAgentFeedback({
          task_type: "theory",
          project_id: projectId,
          accepted,
          signal: accepted ? "理论分析结构有帮助" : "理论分析不够贴题",
        });
      } catch (feedbackError) {
        setError(feedbackError instanceof Error ? feedbackError.message : "无法记录反馈。");
      }
    });
  }

  return (
    <div className="stack">
      {error ? <ErrorState message={error} /> : null}
      <div className="stats-grid">
        <StatCard label="理论库" value={theories.length} />
        <StatCard label="当前项目" value={projectId || "未指定"} />
        <StatCard label="研究问题" value={rq ? "已加载" : "未加载"} />
        <StatCard label="匹配结果" value={matches.length} />
      </div>

      <div className="two-column">
        <Panel title="理论匹配" eyebrow="Theory">
          <form className="compact-form" onSubmit={onMatch}>
            <label className="full-span">
              研究问题
              <textarea value={query} onChange={(event) => setQuery(event.target.value)} rows={4} />
            </label>
            <button className="primary-button" disabled={isPending || !query.trim()} type="submit">
              {isPending ? "匹配中..." : "匹配理论"}
            </button>
            <button
              className="secondary-button"
              disabled={isPending || !query.trim()}
              onClick={onGenerateTheoryDraft}
              type="button"
            >
              生成理论分析草稿
            </button>
          </form>
          {matches.length === 0 ? (
            <EmptyState title="还没有匹配结果" body="输入研究问题后，系统会给出最相关的理论候选。" />
          ) : (
            <ul className="entity-list">
              {matches.map((item) => (
                <li key={item.id} onClick={() => setSelected(item)} className="selectable-row">
                  <div>
                    <strong>{item.name_zh}</strong>
                    <p>{item.name_en}</p>
                  </div>
                  <span className="badge">{item.match_score.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="理论详情" eyebrow="Library">
          {selected ? (
            <div className="stack tight">
              <div className="detail-stack">
                <h4>{selected.name_zh}</h4>
                <p className="body-copy">{selected.name_en}</p>
                <p className="body-copy">{selected.explanation}</p>
                <div className="detail-grid">
                  <div className="full-span">
                    <span className="muted-label">适用主题</span>
                    <p>{selected.applicable_topics.join(" / ")}</p>
                  </div>
                  <div className="full-span">
                    <span className="muted-label">核心概念</span>
                    <p>{selected.core_concepts.join(" / ")}</p>
                  </div>
                  <div className="full-span">
                    <span className="muted-label">局限</span>
                    <p>{selected.limitations.join(" / ")}</p>
                  </div>
                </div>
              </div>
              <div className="top-divider detail-stack">
                <span className="muted-label">AI 理论草稿</span>
                {aiDraft ? (
                  <AgentArtifactPanel
                    artifact={aiDraft}
                    onAccept={() => onFeedback(true)}
                    onReject={() => onFeedback(false)}
                  />
                ) : (
                  <p className="body-copy">基于当前研究问题和理论条目生成一段可继续加工的理论分析草稿。</p>
                )}
              </div>
            </div>
          ) : (
            <EmptyState title="选择一个理论" body="从左侧匹配结果或理论库中选一个条目查看详情。" />
          )}
        </Panel>
      </div>
    </div>
  );
}
