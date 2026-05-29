import type {
  AgentArtifact,
  ApiHealth,
  AgentContextBundle,
  AgentRewriteResult,
  CitationExport,
  ClaimCoverage,
  EvidenceClaim,
  EvidenceItem,
  KnowledgeItem,
  LiteratureReference,
  InsertPreview,
  OutlineSection,
  LiteratureStructureResponse,
  PipelineSession,
  PipelineSessionDetail,
  Project,
  QualityDashboard,
  RagIndexStatus,
  RagResult,
  ResearchDirection,
  ResearchGoal,
  ResearchQuestion,
  RewriteResponse,
  SessionPaper,
  SettingsStatus,
  TheoryCandidate,
  TheoryDetail,
} from "./types";

type HealthResult = ApiHealth & {
  ok: boolean;
  statusCode: number | null;
  statusText: string;
  version: string | null;
  payload: string;
};

const API_BASE_URL =
  process.env.THESISX_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export function getApiStatus() {
  return { baseUrl: API_BASE_URL };
}

export async function getApiHealth(): Promise<HealthResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      cache: "no-store",
    });
    const payload = await response.text();
    const parsed = safeParseJson(payload);
    return {
      ok: response.ok,
      statusCode: response.status,
      statusText: parsed?.status ?? response.statusText,
      version: parsed?.version ?? null,
      payload,
    };
  } catch (error) {
    return {
      ok: false,
      statusCode: null,
      statusText: error instanceof Error ? error.message : "Unknown error",
      version: null,
      payload: JSON.stringify(
        { error: error instanceof Error ? error.message : "Unknown error" },
        null,
        2,
      ),
    };
  }
}

function safeParseJson(payload: string): { status?: string; version?: string } | null {
  try {
    return JSON.parse(payload) as { status?: string; version?: string };
  } catch {
    return null;
  }
}

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(await formatError(response));
  }
  return (await response.json()) as T;
}

async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    throw new Error(await formatError(response));
  }
  return (await response.json()) as T;
}

async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(await formatError(response));
  }
  return (await response.json()) as T;
}

export function getProjects() {
  return apiGet<Project[]>("/api/projects");
}

export function getProject(projectId: string) {
  return apiGet<Project>(`/api/projects/${projectId}`);
}

export function createProject(body: {
  name: string;
  research_question?: string | null;
  discipline?: string | null;
}) {
  return apiPost<Project>("/api/projects", body);
}

export function getResearchQuestion(projectId: string) {
  return apiGet<ResearchQuestion>(`/api/projects/${projectId}/rq`);
}

export function createResearchQuestion(
  projectId: string,
  body: { question: string; keywords: string[]; discipline?: string | null },
) {
  return apiPost<ResearchQuestion>(`/api/projects/${projectId}/rq`, {
    project_id: projectId,
    ...body,
  });
}

export function getProjectDirections(projectId: string) {
  return apiGet<ResearchDirection[]>(`/api/projects/${projectId}/directions`);
}

export function createDirection(
  projectId: string,
  body: { direction: string; rationale?: string | null },
) {
  return apiPost<ResearchDirection>(`/api/projects/${projectId}/directions`, {
    project_id: projectId,
    ...body,
  });
}

export function getProjectGoals(projectId: string) {
  return apiGet<ResearchGoal[]>(`/api/projects/${projectId}/goals`);
}

export function createGoal(
  projectId: string,
  body: { goal: string; milestone?: string | null; deadline?: string | null },
) {
  return apiPost<ResearchGoal>(`/api/projects/${projectId}/goals`, {
    project_id: projectId,
    ...body,
  });
}

export function getProjectRuns(projectId: string) {
  return apiGet<string[]>(`/api/projects/${projectId}/runs`);
}

export function linkProjectRun(projectId: string, runId: string) {
  return apiPost<{ id: string; project_id: string; run_id: string; created_at: string }>(
    `/api/projects/${projectId}/runs`,
    {
      project_id: projectId,
      run_id: runId,
    },
  );
}

export function getKnowledgeItems(projectId?: string) {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return apiGet<KnowledgeItem[]>(`/api/knowledge${query}`);
}

export function searchKnowledge(query: string) {
  return apiGet<KnowledgeItem[]>(`/api/knowledge/search?q=${encodeURIComponent(query)}`);
}

export function createKnowledgeItem(body: {
  item_type: string;
  title: string;
  content: string;
  source_file: string;
  tags: string[];
  external_source: string;
  project_id?: string | null;
}) {
  return apiPost<KnowledgeItem>("/api/knowledge", body);
}

export function getLiterature() {
  return apiGet<LiteratureReference[]>("/api/literature");
}

export function searchLiterature(query: string) {
  return apiGet<LiteratureReference[]>(`/api/literature/search?q=${encodeURIComponent(query)}`);
}

export function structureLiteratureReference(referenceId: string, projectId?: string) {
  return apiPost<LiteratureStructureResponse>(`/api/literature/${referenceId}/structure`, {
    project_id: projectId || null,
  });
}

export function getRagIndexStatus(projectId?: string) {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return apiGet<RagIndexStatus>(`/api/rag/index/status${query}`);
}

export function buildRagIndex(projectId?: string) {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return apiPost<RagIndexStatus>(`/api/rag/index/build${query}`);
}

export function searchRag(body: {
  query: string;
  top_k?: number;
  item_type?: string;
  project_id?: string;
  object_id?: string;
}) {
  return apiPost<RagResult[]>("/api/rag/search", body);
}

export function getSessions() {
  return apiGet<string[]>("/api/pipeline/sessions");
}

export function getPipelineSessions() {
  return apiGet<string[]>("/api/pipeline/sessions");
}

export function createPipelineSession(body: {
  topic: string;
  run_mode: string;
  api_key?: string;
  base_url?: string;
  model?: string;
}) {
  return apiPost<PipelineSession>("/api/pipeline/sessions", {
    generation_type: "paper_draft",
    journal: "中文核心",
    runner_kind: "sequential",
    auto_polish: false,
    budget_cap_cny: 10,
    ...body,
  });
}

export function getPipelineSessionDetail(sessionId: string) {
  return apiGet<PipelineSessionDetail>(`/api/pipeline/sessions/${sessionId}`);
}

export function getPipelineSessionPaper(sessionId: string) {
  return apiGet<SessionPaper>(`/api/pipeline/sessions/${sessionId}/paper`);
}

export function rewriteEditor(body: {
  selected_text: string;
  mode: "polish" | "expand" | "add_theory" | "add_evidence";
  context?: string;
}) {
  return apiPost<RewriteResponse>("/api/editor/rewrite", body);
}

export function parseEditorHeadings(markdownText: string) {
  return apiPost<OutlineSection[]>("/api/editor/parse-headings", {
    markdown_text: markdownText,
  });
}

export function buildInsertPreview(body: {
  paper_text: string;
  editor_sections: OutlineSection[];
}) {
  return apiPost<InsertPreview[]>("/api/editor/insert-preview", body);
}

export function applyInsertPreview(body: {
  editor_content: string;
  previews: InsertPreview[];
  selected: string[];
}) {
  return apiPost<{ new_content: string }>("/api/editor/apply-preview", body);
}

export function getAgentContext(body: {
  task_type: string;
  project_id?: string;
  session_id?: string;
  query?: string;
}) {
  return apiPost<AgentContextBundle>("/api/agent/context", body);
}

export function runAgentRewrite(body: {
  task_type: string;
  selected_text: string;
  mode: "polish" | "expand" | "add_theory" | "add_evidence";
  project_id?: string;
  session_id?: string;
  query?: string;
  extra_context?: string;
}) {
  return apiPost<AgentRewriteResult>("/api/agent/rewrite", body);
}

export function getAgentArtifact(body: {
  task_type: string;
  selected_text?: string;
  mode?: string;
  project_id?: string;
  session_id?: string;
  query?: string;
  extra_context?: string;
}) {
  return apiPost<AgentArtifact>("/api/agent/artifact", body);
}

export function recordAgentFeedback(body: {
  task_type: string;
  project_id?: string;
  accepted: boolean;
  signal: string;
}) {
  return apiPost<{ success: boolean }>("/api/agent/feedback", body);
}

export function writePipelineContext(
  sessionId: string,
  body: {
    topic: string;
    run_mode: string;
    api_key?: string;
    base_url?: string;
    model?: string;
  },
) {
  return apiPost<{ success: boolean }>(`/api/pipeline/sessions/${sessionId}/context`, {
    generation_type: "paper_draft",
    journal: "中文核心",
    runner_kind: "sequential",
    auto_polish: false,
    budget_cap_cny: 10,
    session_id: sessionId,
    ...body,
  });
}

export function deletePipelineSession(sessionId: string) {
  return apiDelete<{ success: boolean }>(`/api/pipeline/sessions/${sessionId}`);
}

export async function streamPipelineSession(sessionId: string) {
  const response = await fetch(`${API_BASE_URL}/api/pipeline/sessions/${sessionId}/stream`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await formatError(response));
  }
  const text = await response.text();
  return text
    .trim()
    .split("\n\n")
    .map((block) => {
      const lines = block.split("\n");
      const event = lines.find((line) => line.startsWith("event:"))?.replace("event: ", "") ?? "message";
      const data = lines.find((line) => line.startsWith("data:"))?.replace("data: ", "") ?? "";
      return { event, data };
    });
}

export function getSettingsStatus() {
  return apiGet<SettingsStatus>("/api/settings/status");
}

export function getTheories() {
  return apiGet<TheoryDetail[]>("/api/theory");
}

export function getTheory(theoryId: string) {
  return apiGet<TheoryDetail>(`/api/theory/${theoryId}`);
}

export function matchTheory(body: { research_question: string; top_k?: number }) {
  return apiPost<TheoryCandidate[]>("/api/theory/match", body);
}

export function getEvidenceClaims(projectId: string) {
  return apiGet<EvidenceClaim[]>(`/api/evidence/projects/${projectId}/claims`);
}

export function createEvidenceClaim(
  projectId: string,
  body: { claim_text: string; claim_type?: string; research_question_id?: string },
) {
  return apiPost<EvidenceClaim>(`/api/evidence/projects/${projectId}/claims`, body);
}

export function deleteEvidenceClaim(projectId: string, claimId: string) {
  return apiDelete<{ success: boolean }>(
    `/api/evidence/projects/${projectId}/claims/${claimId}`,
  );
}

export function getClaimEvidence(projectId: string, claimId: string) {
  return apiGet<EvidenceItem[]>(
    `/api/evidence/projects/${projectId}/claims/${claimId}/evidence`,
  );
}

export function bindClaimEvidence(
  projectId: string,
  claimId: string,
  body: {
    claim_id: string;
    evidence_object_id: string;
    evidence_text: string;
    role?: string;
    priority?: number;
    page_ref?: string;
  },
) {
  return apiPost<EvidenceItem>(
    `/api/evidence/projects/${projectId}/claims/${claimId}/evidence`,
    body,
  );
}

export function unbindClaimEvidence(projectId: string, claimId: string, evidenceId: string) {
  return apiDelete<{ success: boolean }>(
    `/api/evidence/projects/${projectId}/claims/${claimId}/evidence/${evidenceId}`,
  );
}

export function getEvidenceCoverage(projectId: string) {
  return apiGet<ClaimCoverage[]>(`/api/evidence/projects/${projectId}/coverage`);
}

export function getCitationExport(format: "bibtex" | "ris" | "csl_json") {
  return apiGet<CitationExport>(`/api/export/citations?format=${encodeURIComponent(format)}`);
}

export async function exportDocx(body: { markdown: string; title: string }) {
  const response = await fetch(`${API_BASE_URL}/api/export/docx`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await formatError(response));
  }
  return response.blob();
}

export async function exportSessionArchive(sessionId: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/export/session/archive?session_id=${encodeURIComponent(sessionId)}`,
    {
      method: "POST",
    },
  );
  if (!response.ok) {
    throw new Error(await formatError(response));
  }
  return response.blob();
}

export function scanObsidian(vaultPath: string, maxFiles: number) {
  const params = new URLSearchParams({
    vault_path: vaultPath,
    max_files: String(maxFiles),
  });
  return apiPost<KnowledgeItem[]>(`/api/settings/obsidian/scan?${params.toString()}`);
}

export function importZotero(filePath: string, format: "bibtex" | "ris") {
  const params = new URLSearchParams({
    file_path: filePath,
    format,
  });
  return apiPost<KnowledgeItem[]>(`/api/settings/zotero/import?${params.toString()}`);
}

export function getQualityDashboard(projectId = "default") {
  return apiGet<QualityDashboard>(`/api/quality/dashboard?project_id=${encodeURIComponent(projectId)}`);
}

export function getQualityScore(projectId = "default") {
  return apiGet<{ overall_score: number; grade: string }>(
    `/api/quality/score?project_id=${encodeURIComponent(projectId)}`,
  );
}

async function formatError(response: Response) {
  const text = await response.text();
  try {
    const parsed = JSON.parse(text) as { detail?: { message?: string } | string };
    if (typeof parsed.detail === "string") {
      return parsed.detail;
    }
    if (parsed.detail && "message" in parsed.detail && parsed.detail.message) {
      return parsed.detail.message;
    }
  } catch {
    return text || `HTTP ${response.status}`;
  }
  return text || `HTTP ${response.status}`;
}
