export type ApiHealthResponse = {
  status: string;
  database: "connected" | "disconnected";
  service: string;
};

export type Workspace = {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
};

export type InternshipPost = {
  id: string;
  workspace_id: string;
  created_by_id: string;
  title: string;
  company_name: string;
  location: string | null;
  description: string;
  requirements: string | null;
  source_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ApplicationStatus =
  | "draft"
  | "matched"
  | "applied"
  | "interviewing"
  | "offered"
  | "rejected"
  | "withdrawn";

export type Application = {
  id: string;
  workspace_id: string;
  user_id: string;
  internship_post_id: string;
  document_id: string | null;
  status: ApplicationStatus;
  match_score: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentStatus = "uploaded" | "processing" | "ready" | "failed";

export type Document = {
  id: string;
  workspace_id: string;
  user_id: string;
  filename: string;
  content_type: string | null;
  storage_path: string;
  size_bytes: number | null;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
};

export type PlannerTaskType =
  | "compare_cv_to_internship"
  | "generate_cover_letter"
  | "prepare_interview_questions"
  | "unknown";

export type PlannerOutput = {
  task_type: PlannerTaskType;
  confidence: number;
  required_context: string[];
  steps: string[];
  output_format:
    | "internship_match_report"
    | "cover_letter_draft"
    | "interview_prep_guide"
    | null;
  needs_clarification: boolean;
  clarifying_question: string | null;
};

export type RetrievalSummary = {
  cv_chunk_count: number;
  top_score: number | null;
  internship_post_id: string;
  internship_title: string;
  internship_company: string;
};

export type RetrievalQuality = {
  top_score: number | null;
  average_score: number | null;
  quality_level: "strong" | "medium" | "weak";
  warning: string | null;
};

export type ContextSummary = {
  source_chunk_count: number;
  source_chunk_ids: string[];
  context_preview: string;
};

export type EvidenceSummary = {
  kept_chunk_count: number;
  discarded_chunk_count: number;
  warnings: string[];
};

export type SkillMatch = {
  skill: string;
  evidence: string;
  category: string | null;
  match_type: "direct" | "related";
  confidence: number;
};

export type SkillGap = {
  skill: string;
  recommendation: string;
  category: string | null;
};

export type MatchReport = {
  match_score: number;
  summary: string;
  matched_skills: SkillMatch[];
  missing_skills: SkillGap[];
  recommendations: string[];
  source_chunk_ids: string[];
};

export type RetrievedChunk = {
  chunk_id: string;
  document_id: string;
  workspace_id: string;
  user_id: string;
  chunk_index: number;
  content: string;
  score: number;
  qdrant_point_id: string;
};

export type RetrievedInternshipPost = InternshipPost;

export type RetrieverOutput = {
  cv_chunks: RetrievedChunk[];
  internship_post: RetrievedInternshipPost;
};

export type AnalyzedEvidenceChunk = RetrievedChunk & {
  decision: string;
  reason: string;
};

export type EvidenceAnalyzerOutput = {
  kept_chunks: AnalyzedEvidenceChunk[];
  discarded_chunks: AnalyzedEvidenceChunk[];
  retrieval_quality: RetrievalQuality;
  warnings: string[];
};

export type InternshipSummary = {
  title: string;
  company_name: string;
  location: string | null;
  description: string;
  requirements: string | null;
};

export type ContextBuilderOutput = {
  task_type: PlannerTaskType;
  context_text: string;
  cv_evidence: string[];
  internship_summary: InternshipSummary;
  source_chunk_ids: string[];
};

export type InternshipMatchPipelineInput = {
  user_query: string;
  workspace_id: string;
  user_id: string;
  document_id: string;
  internship_post_id: string;
};

export type InternshipMatchPipelineOutput = {
  planner_agent_run_id: string | null;
  retriever_agent_run_id: string | null;
  evidence_analyzer_agent_run_id: string | null;
  context_builder_agent_run_id: string | null;
  match_report_agent_run_id: string | null;
  plan: PlannerOutput;
  retrieval_summary: RetrievalSummary | null;
  retrieval_quality: RetrievalQuality | null;
  evidence_summary: EvidenceSummary | null;
  context_summary: ContextSummary | null;
  report: MatchReport | null;
  needs_clarification: boolean;
  clarifying_question: string | null;
  stopped_reason: string | null;
};

export type InternshipMatchPipelineResponse = {
  agent_run_id: string;
  pipeline: InternshipMatchPipelineOutput;
};

export type PipelineNotice = {
  stage: string;
  message: string;
  code: string | null;
  created_at: string;
};

export type InternshipMatchGraphState = {
  user_query: string;
  workspace_id: string;
  user_id: string;
  document_id: string;
  internship_post_id: string;
  plan: PlannerOutput | null;
  retrieval: RetrieverOutput | null;
  evidence: EvidenceAnalyzerOutput | null;
  context: ContextBuilderOutput | null;
  deterministic_report: MatchReport | null;
  llm_reasoning: unknown | null;
  validation: unknown | null;
  warnings: PipelineNotice[];
  errors: PipelineNotice[];
  current_stage: string | null;
  completed_stages: string[];
};

export type InternshipMatchGraphResponse = {
  agent_run_id: string;
  final_state: InternshipMatchGraphState;
  completed_stages: string[];
  warnings: PipelineNotice[];
  errors: PipelineNotice[];
  deterministic_report: MatchReport | null;
};

export type InternshipRankPipelineInput = {
  workspace_id: string;
  user_id: string;
  document_id: string;
  query?: string | null;
};

export type RankedInternshipResult = {
  rank: number;
  internship_post_id: string;
  title: string;
  company_name: string;
  match_score: number;
  matched_skills: SkillMatch[];
  missing_skills: SkillGap[];
  retrieval_quality: RetrievalQuality;
  recommendations: string[];
};

export type InternshipRankPipelineOutput = {
  query: string;
  total_ranked: number;
  results: RankedInternshipResult[];
};

export type InternshipRankPipelineResponse = {
  agent_run_id: string;
  ranking: InternshipRankPipelineOutput;
};
