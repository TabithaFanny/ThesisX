export type ApiHealth = {
  status?: string | null;
  version?: string | null;
};

export type Project = {
  id: string;
  name: string;
  research_question?: string | null;
  discipline?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ResearchQuestion = {
  id: string;
  project_id: string;
  question: string;
  keywords: string[];
  discipline?: string | null;
  clarity_score?: number | null;
};

export type ResearchDirection = {
  id: string;
  project_id: string;
  direction: string;
  rationale?: string | null;
  status: string;
  created_at: string;
};

export type ResearchGoal = {
  id: string;
  project_id: string;
  goal: string;
  milestone?: string | null;
  deadline?: string | null;
  status: string;
  created_at: string;
};

export type KnowledgeItem = {
  id: string;
  item_type: string;
  title: string;
  content: string;
  source_file: string;
  tags: string[];
  project_id?: string | null;
  external_source: string;
  created_at: string;
  updated_at: string;
};

export type LiteratureReference = {
  id: string;
  title: string;
  authors: string[];
  year: string;
  journal?: string | null;
  doi?: string | null;
  abstract?: string | null;
  file_path?: string | null;
  zotero_key?: string | null;
  tags: string[];
  created_at: string;
};

export type RagResult = {
  chunk_id: string;
  source_title: string;
  source_id: string;
  text: string;
  score: number;
  item_type: string;
  start_char: number;
  end_char: number;
};

export type RagIndexStatus = {
  size: number;
  message: string;
};

export type PipelineSession = {
  session_id: string;
};

export type PipelineSessionDetail = {
  session_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  event_count: number;
  message_count: number;
  has_errors: boolean;
  output_files: Record<string, string>;
};

export type SessionPaper = {
  session_id: string;
  markdown: string;
};

export type OutlineSection = {
  id: string;
  level: number;
  title: string;
  order: number;
  content: string;
  section_type: string;
};

export type InsertPreview = {
  section_title: string;
  level: number;
  content: string;
  action: string;
  target_section: string;
};

export type AgentContextBundle = {
  task_type: string;
  project_id: string;
  session_id: string;
  project_summary: string;
  working_context: string;
  memory_context: string;
  output_contract: string;
  assembled_context: string;
  sources: string[];
};

export type AgentRewriteResult = {
  task_type: string;
  mode: string;
  original: string;
  rewritten: string;
  assembled_context: string;
  output_contract: string;
  sources: string[];
};

export type AgentArtifactStep = {
  id: string;
  title: string;
  rationale: string;
  target_surface: string;
  suggested_mode: string;
  priority: string;
};

export type AgentArtifactAction = {
  id: string;
  label: string;
  target_surface: string;
  intent: string;
  suggested_mode: string;
  priority: string;
};

export type AgentArtifactSection = {
  id: string;
  title: string;
  content: string;
  kind: string;
};

export type AgentArtifact = {
  task_type: string;
  artifact_type: string;
  summary: string;
  markdown: string;
  sections: AgentArtifactSection[];
  steps: AgentArtifactStep[];
  actions: AgentArtifactAction[];
  metadata: Record<string, string>;
  assembled_context: string;
  output_contract: string;
  sources: string[];
};

export type QualityDashboard = {
  writing_progress: number;
  claim_coverage: number;
  evidence_integrity: number;
  citation_completeness: number;
  overall_score: number;
  suggestions: string[];
  total_sections: number;
  sections_completed: number;
  total_claims: number;
  claims_covered: number;
  total_evidence_items: number;
  evidence_verified: number;
  total_citations: number;
  citations_complete: number;
  grade: string;
};

export type SettingsStatus = {
  db_exists: boolean;
  runs_dir_exists: boolean;
  version: string;
};

export type TheoryDetail = {
  id: string;
  name_zh: string;
  name_en: string;
  discipline: string[];
  core_concepts: string[];
  applicable_topics: string[];
  explanation: string;
  limitations: string[];
};

export type TheoryCandidate = TheoryDetail & {
  match_score: number;
};

export type EvidenceClaim = {
  id: string;
  claim_text: string;
  claim_type: string;
  source_id: string;
  discipline: string;
  extracted_by: string;
  created_at: string;
};

export type EvidenceItem = {
  id: string;
  claim_id: string;
  evidence_object_id: string;
  evidence_text: string;
  role: string;
  priority: number;
  coverage_status: string;
  page_ref: string;
  created_at: string;
};

export type ClaimCoverage = {
  claim_id: string;
  claim_text: string;
  claim_type: string;
  coverage: string;
  evidence_ids: string[];
  coverage_score: number;
  gap_reasons: string[];
  notes: string;
};

export type CitationExport = {
  format: string;
  content: string;
};

export type ImportSummary = {
  imported_count: number;
  items: KnowledgeItem[];
};

export type RewriteResponse = {
  original: string;
  rewritten: string;
  mode: string;
};

export type LiteratureStructureResponse = {
  reference_id: string;
  items: KnowledgeItem[];
};
