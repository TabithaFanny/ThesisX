"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import { AgentArtifactPanel } from "./agent-artifact-panel";
import {
  bindClaimEvidence,
  createEvidenceClaim,
  deleteEvidenceClaim,
  getAgentArtifact,
  getClaimEvidence,
  getEvidenceClaims,
  getEvidenceCoverage,
  getKnowledgeItems,
  getProjects,
  recordAgentFeedback,
} from "../lib/api";
import { getActiveProjectId, setActiveProjectId } from "../lib/project-context";
import type {
  ClaimCoverage,
  EvidenceClaim,
  EvidenceItem,
  KnowledgeItem,
  Project,
  AgentArtifact,
} from "../lib/types";
import { EmptyState, ErrorState, Panel, StatCard } from "./ui";

type EvidenceWorkspaceData = {
  claims: EvidenceClaim[];
  coverage: ClaimCoverage[];
  knowledgeItems: KnowledgeItem[];
};

async function fetchEvidenceWorkspaceData(projectId: string): Promise<EvidenceWorkspaceData> {
  const [claimData, coverageData, itemData] = await Promise.all([
    getEvidenceClaims(projectId),
    getEvidenceCoverage(projectId),
    getKnowledgeItems(projectId),
  ]);
  return {
    claims: claimData,
    coverage: coverageData,
    knowledgeItems: itemData.filter((item) => item.item_type === "evidence" || item.item_type === "literature"),
  };
}

export function EvidenceWorkspace() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [claims, setClaims] = useState<EvidenceClaim[]>([]);
  const [coverage, setCoverage] = useState<ClaimCoverage[]>([]);
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
  const [selectedClaim, setSelectedClaim] = useState<EvidenceClaim | null>(null);
  const [evidenceItems, setEvidenceItems] = useState<EvidenceItem[]>([]);
  const [claimText, setClaimText] = useState("");
  const [claimType, setClaimType] = useState("fact");
  const [selectedEvidenceObjectId, setSelectedEvidenceObjectId] = useState("");
  const [evidenceText, setEvidenceText] = useState("");
  const [aiEvidenceDraft, setAiEvidenceDraft] = useState<AgentArtifact | null>(null);
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();
  const selectedClaimId = selectedClaim?.id ?? "";

  async function loadWorkspace(nextProjectId: string, preferredClaimId?: string) {
    if (!nextProjectId) {
      setClaims([]);
      setCoverage([]);
      setKnowledgeItems([]);
      setSelectedClaim(null);
      setEvidenceItems([]);
      return;
    }
    const data = await fetchEvidenceWorkspaceData(nextProjectId);
    setClaims(data.claims);
    setCoverage(data.coverage);
    setKnowledgeItems(data.knowledgeItems);
    const nextClaim = data.claims.find((item) => item.id === preferredClaimId) ?? data.claims[0] ?? null;
    setSelectedClaim(nextClaim);
    if (nextClaim) {
      setEvidenceItems(await getClaimEvidence(nextProjectId, nextClaim.id));
    } else {
      setEvidenceItems([]);
    }
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
          setError(loadError instanceof Error ? loadError.message : "无法加载项目。");
        }
      });
    return () => {
      active = false;
    };
  }, [searchParams]);

  useEffect(() => {
    setActiveProjectId(projectId);
    if (!projectId) {
      setClaims([]);
      setCoverage([]);
      setKnowledgeItems([]);
      setSelectedClaim(null);
      setEvidenceItems([]);
      return;
    }
    fetchEvidenceWorkspaceData(projectId)
      .then((data) => {
        setClaims(data.claims);
        setCoverage(data.coverage);
        setKnowledgeItems(data.knowledgeItems);
        setSelectedClaim(data.claims[0] ?? null);
      })
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "无法加载证据工作区。"),
      );
  }, [projectId]);

  useEffect(() => {
    if (!projectId || !selectedClaimId) {
      setEvidenceItems([]);
      return;
    }
    getClaimEvidence(projectId, selectedClaimId)
      .then((data) => setEvidenceItems(data))
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "无法加载证据项。"),
      );
  }, [projectId, selectedClaimId]);

  function onCreateClaim(event: FormEvent) {
    event.preventDefault();
    if (!projectId) {
      setError("请先选择一个项目，再创建 Claim。");
      return;
    }
    startTransition(async () => {
      try {
        await createEvidenceClaim(projectId, {
          claim_text: claimText,
          claim_type: claimType,
          research_question_id: "",
        });
        setClaimText("");
        await loadWorkspace(projectId, selectedClaim?.id);
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "无法创建 Claim。");
      }
    });
  }

  function onBindEvidence(event: FormEvent) {
    event.preventDefault();
    if (!projectId || !selectedClaim) {
      setError("请先选择项目和 Claim。");
      return;
    }
    startTransition(async () => {
      try {
        await bindClaimEvidence(projectId, selectedClaim.id, {
          claim_id: selectedClaim.id,
          evidence_object_id: selectedEvidenceObjectId,
          evidence_text: evidenceText,
          role: "evidence",
          priority: 1,
          page_ref: "",
        });
        setSelectedEvidenceObjectId("");
        setEvidenceText("");
        await loadWorkspace(projectId, selectedClaim.id);
      } catch (bindError) {
        setError(bindError instanceof Error ? bindError.message : "无法绑定证据。");
      }
    });
  }

  function onDeleteClaim(claimId: string) {
    if (!projectId) {
      return;
    }
    startTransition(async () => {
      try {
        await deleteEvidenceClaim(projectId, claimId);
        await loadWorkspace(projectId, selectedClaim?.id === claimId ? undefined : selectedClaim?.id);
      } catch (deleteError) {
        setError(deleteError instanceof Error ? deleteError.message : "无法删除 Claim。");
      }
    });
  }

  function onGenerateEvidenceDraft() {
    if (!selectedClaim) {
      setError("请先选择一个 Claim，再生成证据草稿。");
      return;
    }
    startTransition(async () => {
      try {
        const result = await getAgentArtifact({
          task_type: "evidence",
          selected_text: selectedClaim.claim_text,
          mode: "add_evidence",
          project_id: projectId,
          query: selectedClaim.claim_text,
          extra_context: `claim_id=${selectedClaim.id}`,
        });
        setAiEvidenceDraft(result);
      } catch (rewriteError) {
        setError(rewriteError instanceof Error ? rewriteError.message : "无法生成证据草稿。");
      }
    });
  }

  function onFeedback(accepted: boolean) {
    if (!aiEvidenceDraft) {
      return;
    }
    startTransition(async () => {
      try {
        await recordAgentFeedback({
          task_type: "evidence",
          project_id: projectId,
          accepted,
          signal: accepted ? "证据稿能指导绑定工作" : "证据稿太泛，不能直接用",
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
        <StatCard label="当前项目" value={projectId || "未指定"} />
        <StatCard label="Claims" value={claims.length} />
        <StatCard label="Evidence" value={evidenceItems.length} />
        <StatCard
          label="已覆盖"
          value={coverage.filter((item) => item.coverage === "covered").length}
          hint="coverage=covered 的 Claim 数"
        />
      </div>

      <div className="two-column">
        <Panel title="Claim 列表" eyebrow="Evidence">
          <label className="full-span">
            项目
            <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
              <option value="">选择项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          {claims.length === 0 ? (
            <EmptyState title="还没有 Claim" body="先根据当前项目的研究问题写出关键论断，再绑定证据。" />
          ) : (
            <ul className="entity-list">
              {claims.map((claim) => {
                const claimCoverage = coverage.find((item) => item.claim_id === claim.id);
                return (
                  <li key={claim.id}>
                    <button
                      className={`list-button${selectedClaim?.id === claim.id ? " active" : ""}`}
                      onClick={() => setSelectedClaim(claim)}
                      type="button"
                    >
                      <strong>{claim.claim_text}</strong>
                      <p>{claimCoverage ? `${claimCoverage.coverage} / ${claimCoverage.coverage_score.toFixed(2)}` : claim.claim_type}</p>
                    </button>
                    <button className="secondary-button" onClick={() => onDeleteClaim(claim.id)} type="button">
                      删除
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
          <form className="compact-form top-divider" onSubmit={onCreateClaim}>
            <input value={claimText} onChange={(event) => setClaimText(event.target.value)} placeholder="新增一条需要论证的 Claim" />
            <select value={claimType} onChange={(event) => setClaimType(event.target.value)}>
              <option value="fact">fact</option>
              <option value="argument">argument</option>
              <option value="method">method</option>
            </select>
            <button className="primary-button" disabled={isPending || !claimText.trim()} type="submit">
              添加 Claim
            </button>
          </form>
        </Panel>

        <Panel
          title="证据绑定"
          eyebrow="Coverage"
          actions={
            selectedClaim ? (
              <button
                className="secondary-button"
                disabled={isPending}
                onClick={onGenerateEvidenceDraft}
                type="button"
              >
                生成 AI 证据草稿
              </button>
            ) : null
          }
        >
          {!selectedClaim ? (
            <EmptyState title="先选择一个 Claim" body="右侧会显示这个 Claim 已绑定的证据，以及继续补证据的入口。" />
          ) : (
            <div className="stack tight">
              <div className="detail-stack">
                <h4>{selectedClaim.claim_text}</h4>
                <p className="body-copy">类型：{selectedClaim.claim_type}</p>
              </div>
              <form className="compact-form" onSubmit={onBindEvidence}>
                <label className="full-span">
                  证据来源
                  <select value={selectedEvidenceObjectId} onChange={(event) => setSelectedEvidenceObjectId(event.target.value)}>
                    <option value="">选择 evidence / literature 条目</option>
                    {knowledgeItems.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.title}
                      </option>
                    ))}
                  </select>
                </label>
                <textarea value={evidenceText} onChange={(event) => setEvidenceText(event.target.value)} rows={5} placeholder="摘录支持这条 Claim 的具体证据" />
                <button
                  className="primary-button"
                  disabled={isPending || !selectedEvidenceObjectId || !evidenceText.trim()}
                  type="submit"
                >
                  绑定证据
                </button>
              </form>
              {knowledgeItems.length === 0 ? (
                <Link className="secondary-link" href={`/knowledge?project_id=${projectId}&item_type=evidence`}>
                  当前项目还没有 evidence 条目，先去补知识
                </Link>
              ) : null}
              {evidenceItems.length === 0 ? (
                <EmptyState title="还没有证据项" body="选一个知识条目，摘录关键内容后绑定到当前 Claim。" />
              ) : (
                <ul className="result-list">
                  {evidenceItems.map((item) => (
                    <li key={item.id}>
                      <div className="result-topline">
                        <strong>{item.role}</strong>
                        <span>{item.coverage_status}</span>
                      </div>
                      <p>{item.evidence_text}</p>
                    </li>
                  ))}
                </ul>
              )}
              <div className="top-divider detail-stack">
                <span className="muted-label">AI 证据草稿</span>
                {aiEvidenceDraft ? (
                  <AgentArtifactPanel
                    artifact={aiEvidenceDraft}
                    acceptLabel="接受结果"
                    rejectLabel="拒绝结果"
                    onAccept={() => onFeedback(true)}
                    onReject={() => onFeedback(false)}
                  />
                ) : (
                  <p className="body-copy">为当前 Claim 先生成一段“还需要补哪类证据”的工作草稿。</p>
                )}
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
