"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  Loader2,
  Search,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  getDocuments,
  getInternshipPosts,
  getWorkspaces,
  runInternshipMatchGraphPipeline,
  runInternshipMatchPipeline,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import type {
  InternshipMatchGraphResponse,
  InternshipMatchPipelineResponse,
  InternshipMatchPipelineOutput,
  InternshipPost,
  PlannerOutput,
} from "@/types";

const DEFAULT_QUERY =
  "Compare my CV with this backend internship and tell me what I should improve.";

type ExecutionMode = "manual" | "langgraph";

type NormalizedMatchResult = {
  agentRunId: string;
  mode: ExecutionMode;
  pipeline: InternshipMatchPipelineOutput;
  completedStages: string[];
};

type MatchMutationInput = {
  mode: ExecutionMode;
  input: Parameters<typeof runInternshipMatchPipeline>[0];
};

const EXECUTION_MODE_LABELS: Record<ExecutionMode, string> = {
  manual: "Manual Pipeline",
  langgraph: "LangGraph Pipeline",
};

const FALLBACK_PLAN: PlannerOutput = {
  task_type: "unknown",
  confidence: 0,
  required_context: [],
  steps: [],
  output_format: null,
  needs_clarification: true,
  clarifying_question:
    "The planner did not return a plan for this workflow run.",
};

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong.";
}

function formatScore(score: number | null) {
  if (score === null) {
    return "n/a";
  }

  return score.toFixed(3);
}

function getRetrievalQualityTone(
  qualityLevel: "strong" | "medium" | "weak",
) {
  if (qualityLevel === "strong") {
    return "success";
  }

  if (qualityLevel === "medium") {
    return "default";
  }

  return "warning";
}

function previewText(text: string, maxLength = 500) {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (normalized.length <= maxLength) {
    return normalized;
  }

  return `${normalized.slice(0, maxLength).trimEnd()}...`;
}

function getTopScore(scores: number[]) {
  if (scores.length === 0) {
    return null;
  }

  return Math.max(...scores);
}

function normalizeManualResult(
  response: InternshipMatchPipelineResponse,
): NormalizedMatchResult {
  return {
    agentRunId: response.agent_run_id,
    mode: "manual",
    pipeline: response.pipeline,
    completedStages: [],
  };
}

function normalizeGraphResult(
  response: InternshipMatchGraphResponse,
): NormalizedMatchResult {
  const state = response.final_state;
  const retrievalScores =
    state.retrieval?.cv_chunks.map((chunk) => chunk.score) ?? [];
  const needsClarification = state.plan?.needs_clarification ?? false;
  const noReliableEvidence = response.errors.some(
    (error) => error.code === "no_reliable_evidence",
  );
  const evidenceWarnings = [
    ...(state.evidence?.warnings ?? []),
    ...response.warnings.map((warning) => warning.message),
  ];

  return {
    agentRunId: response.agent_run_id,
    mode: "langgraph",
    completedStages: response.completed_stages,
    pipeline: {
      planner_agent_run_id: null,
      retriever_agent_run_id: null,
      evidence_analyzer_agent_run_id: null,
      context_builder_agent_run_id: null,
      match_report_agent_run_id: null,
      plan: state.plan ?? FALLBACK_PLAN,
      retrieval_summary: state.retrieval
        ? {
            cv_chunk_count: state.retrieval.cv_chunks.length,
            top_score: getTopScore(retrievalScores),
            internship_post_id: state.retrieval.internship_post.id,
            internship_title: state.retrieval.internship_post.title,
            internship_company: state.retrieval.internship_post.company_name,
          }
        : null,
      retrieval_quality: state.evidence?.retrieval_quality ?? null,
      evidence_summary: state.evidence
        ? {
            kept_chunk_count: state.evidence.kept_chunks.length,
            discarded_chunk_count: state.evidence.discarded_chunks.length,
            warnings: Array.from(new Set(evidenceWarnings)),
          }
        : null,
      context_summary: state.context
        ? {
            source_chunk_count: state.context.source_chunk_ids.length,
            source_chunk_ids: state.context.source_chunk_ids,
            context_preview: previewText(state.context.context_text),
          }
        : null,
      report: response.deterministic_report ?? state.deterministic_report,
      needs_clarification: needsClarification,
      clarifying_question: state.plan?.clarifying_question ?? null,
      stopped_reason: needsClarification
        ? "planner_needs_clarification"
        : noReliableEvidence
          ? "no_reliable_evidence"
          : null,
    },
  };
}

function SelectField({
  id,
  label,
  value,
  onChange,
  disabled,
  children,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  children: ReactNode;
}) {
  return (
    <label htmlFor={id} className="block">
      <span className="text-sm font-medium">{label}</span>
      <select
        id={id}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 h-11 w-full rounded-lg border border-border bg-surface px-3 text-sm outline-none transition-colors focus:border-primary disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
      >
        {children}
      </select>
    </label>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/35 p-4 text-sm text-muted-foreground">
      {message}
    </div>
  );
}

function MatchScore({ score }: { score: number }) {
  return (
    <div>
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            Match Score
          </p>
          <p className="mt-1 text-4xl font-semibold tracking-normal">
            {score.toFixed(0)}%
          </p>
        </div>
        <Sparkles className="h-8 w-8 text-primary" aria-hidden="true" />
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
    </div>
  );
}

function ResultPanel({
  result,
}: {
  result: NormalizedMatchResult | undefined;
}) {
  if (!result) {
    return (
      <Card>
        <CardContent>
          <EmptyState message="Run the workflow to see planner, retrieval, and match report results." />
        </CardContent>
      </Card>
    );
  }

  const { pipeline } = result;
  const executionLabel = EXECUTION_MODE_LABELS[result.mode];

  if (pipeline.needs_clarification) {
    return (
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-center gap-2 text-amber-900">
              <AlertCircle className="h-5 w-5" aria-hidden="true" />
              <h2 className="text-lg font-semibold tracking-normal">
                Clarification Needed
              </h2>
            </div>
            <Badge tone={result.mode === "langgraph" ? "default" : "muted"}>
              {executionLabel}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-amber-800">
            {pipeline.clarifying_question}
          </p>
          <p className="mt-4 text-xs text-amber-700">
            Workflow run: {result.agentRunId}
          </p>
        </CardContent>
      </Card>
    );
  }

  const stoppedForEvidence = pipeline.stopped_reason === "no_reliable_evidence";

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold tracking-normal">
                Planner Result
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {pipeline.plan.task_type.replaceAll("_", " ")}
              </p>
            </div>
            <Badge tone="success">
              {(pipeline.plan.confidence * 100).toFixed(0)}% confidence
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Badge tone={result.mode === "langgraph" ? "default" : "muted"}>
                {executionLabel}
              </Badge>
              {pipeline.plan.steps.map((step) => (
                <Badge key={step} tone="muted">
                  {step.replaceAll("_", " ")}
                </Badge>
              ))}
            </div>

            {result.mode === "langgraph" ? (
              <div>
                <h3 className="text-sm font-semibold">Completed Stages</h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {result.completedStages.length > 0 ? (
                    result.completedStages.map((stage) => (
                      <Badge key={stage} tone="success">
                        {stage.replaceAll("_", " ")}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      No completed stages returned.
                    </span>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <section className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold tracking-normal">
              Retrieval Summary
            </h2>
          </CardHeader>
          <CardContent>
            {pipeline.retrieval_summary ? (
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between gap-4">
                  <span className="text-muted-foreground">CV chunks</span>
                  <span className="font-medium">
                    {pipeline.retrieval_summary.cv_chunk_count}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span className="text-muted-foreground">Top score</span>
                  <span className="font-medium">
                    {formatScore(pipeline.retrieval_summary.top_score)}
                  </span>
                </div>
                {pipeline.retrieval_quality ? (
                  <>
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">
                        Average score
                      </span>
                      <span className="font-medium">
                        {formatScore(pipeline.retrieval_quality.average_score)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">Quality</span>
                      <Badge
                        tone={getRetrievalQualityTone(
                          pipeline.retrieval_quality.quality_level,
                        )}
                      >
                        {pipeline.retrieval_quality.quality_level}
                      </Badge>
                    </div>
                    {pipeline.retrieval_quality.warning ? (
                      <div className="flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-800">
                        <AlertCircle
                          className="mt-0.5 h-4 w-4 shrink-0"
                          aria-hidden="true"
                        />
                        <p className="text-sm leading-6">
                          {pipeline.retrieval_quality.warning}
                        </p>
                      </div>
                    ) : null}
                  </>
                ) : null}
                <div className="rounded-lg border border-border bg-muted/35 p-3">
                  <p className="font-medium">
                    {pipeline.retrieval_summary.internship_title}
                  </p>
                  <p className="mt-1 text-muted-foreground">
                    {pipeline.retrieval_summary.internship_company}
                  </p>
                </div>
              </div>
            ) : (
              <EmptyState message="No retrieval summary returned." />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold tracking-normal">
              Evidence Summary
            </h2>
          </CardHeader>
          <CardContent>
            {pipeline.evidence_summary ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-4 text-sm">
                  <span className="text-muted-foreground">Kept evidence</span>
                  <span className="font-medium">
                    {pipeline.evidence_summary.kept_chunk_count}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4 text-sm">
                  <span className="text-muted-foreground">
                    Discarded evidence
                  </span>
                  <span className="font-medium">
                    {pipeline.evidence_summary.discarded_chunk_count}
                  </span>
                </div>
                {pipeline.evidence_summary.warnings.length > 0 ? (
                  <div className="space-y-2">
                    {pipeline.evidence_summary.warnings.map((warning) => (
                      <div
                        key={warning}
                        className="flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-800"
                      >
                        <AlertCircle
                          className="mt-0.5 h-4 w-4 shrink-0"
                          aria-hidden="true"
                        />
                        <p className="text-sm leading-6">{warning}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm leading-6 text-muted-foreground">
                    Analyzer retained reliable CV evidence for the report.
                  </p>
                )}
              </div>
            ) : (
              <EmptyState message="No evidence summary returned." />
            )}
          </CardContent>
        </Card>
      </section>

      {pipeline.context_summary ? (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold tracking-normal">
              Context Summary
            </h2>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Source chunks</span>
                <span className="font-medium">
                  {pipeline.context_summary.source_chunk_count}
                </span>
              </div>
              <p className="line-clamp-2 text-sm leading-6 text-muted-foreground">
                {pipeline.context_summary.context_preview}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {stoppedForEvidence ? (
        <Card className="border-amber-200 bg-amber-50">
          <CardHeader>
            <div className="flex items-center gap-2 text-amber-900">
              <AlertCircle className="h-5 w-5" aria-hidden="true" />
              <h2 className="text-lg font-semibold tracking-normal">
                No Reliable Evidence
              </h2>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-6 text-amber-800">
              The pipeline stopped before context building because no retrieved
              CV chunks passed the evidence threshold.
            </p>
            <p className="mt-4 text-xs text-amber-700">
              Evidence analyzer run: {pipeline.evidence_analyzer_agent_run_id}
            </p>
          </CardContent>
        </Card>
      ) : null}

      {pipeline.report ? (
        <Card>
          <CardHeader>
            <MatchScore score={pipeline.report.match_score} />
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-6 text-muted-foreground">
              {pipeline.report.summary}
            </p>

            <div className="mt-6 grid gap-5 lg:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold">Matched Skills</h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {pipeline.report.matched_skills.length > 0 ? (
                    pipeline.report.matched_skills.map((skill) => (
                      <Badge key={skill.skill} tone="success">
                        {skill.skill}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      No matched skills found.
                    </span>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold">Missing Skills</h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {pipeline.report.missing_skills.length > 0 ? (
                    pipeline.report.missing_skills.map((skill) => (
                      <Badge key={skill.skill} tone="warning">
                        {skill.skill}
                      </Badge>
                    ))
                  ) : (
                    <Badge tone="success">None</Badge>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-6">
              <h3 className="text-sm font-semibold">Recommendations</h3>
              <ul className="mt-3 space-y-2">
                {pipeline.report.recommendations.map((recommendation) => (
                  <li
                    key={recommendation}
                    className="flex gap-2 text-sm leading-6 text-muted-foreground"
                  >
                    <CheckCircle2
                      className="mt-1 h-4 w-4 shrink-0 text-emerald-600"
                      aria-hidden="true"
                    />
                    {recommendation}
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

export function InternshipMatchClient() {
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [selectedInternshipId, setSelectedInternshipId] = useState("");
  const [userQuery, setUserQuery] = useState(DEFAULT_QUERY);
  const [executionMode, setExecutionMode] = useState<ExecutionMode>("manual");

  const workspacesQuery = useQuery({
    queryKey: ["workspaces"],
    queryFn: getWorkspaces,
  });
  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
  });
  const internshipsQuery = useQuery({
    queryKey: ["internships"],
    queryFn: getInternshipPosts,
  });

  const workspaces = useMemo(
    () => workspacesQuery.data ?? [],
    [workspacesQuery.data],
  );
  const selectedWorkspace = workspaces.find(
    (workspace) => workspace.id === selectedWorkspaceId,
  );
  const documents = useMemo(
    () =>
      (documentsQuery.data ?? []).filter(
        (document) =>
          document.workspace_id === selectedWorkspaceId &&
          document.status === "ready",
      ),
    [documentsQuery.data, selectedWorkspaceId],
  );
  const internships = useMemo(
    () =>
      (internshipsQuery.data ?? []).filter(
        (internship) => internship.workspace_id === selectedWorkspaceId,
      ),
    [internshipsQuery.data, selectedWorkspaceId],
  );

  useEffect(() => {
    if (!selectedWorkspaceId && workspaces[0]) {
      setSelectedWorkspaceId(workspaces[0].id);
    }
  }, [selectedWorkspaceId, workspaces]);

  useEffect(() => {
    if (!documents.some((document) => document.id === selectedDocumentId)) {
      setSelectedDocumentId(documents[0]?.id ?? "");
    }
  }, [documents, selectedDocumentId]);

  useEffect(() => {
    if (
      !internships.some(
        (internship) => internship.id === selectedInternshipId,
      )
    ) {
      setSelectedInternshipId(internships[0]?.id ?? "");
    }
  }, [internships, selectedInternshipId]);

  const pipelineMutation = useMutation({
    mutationFn: async ({ mode, input }: MatchMutationInput) => {
      if (mode === "langgraph") {
        return normalizeGraphResult(await runInternshipMatchGraphPipeline(input));
      }

      return normalizeManualResult(await runInternshipMatchPipeline(input));
    },
  });

  const isLoadingData =
    workspacesQuery.isLoading ||
    documentsQuery.isLoading ||
    internshipsQuery.isLoading;
  const dataError =
    workspacesQuery.error ?? documentsQuery.error ?? internshipsQuery.error;
  const canRun =
    Boolean(selectedWorkspace?.owner_id) &&
    Boolean(selectedDocumentId) &&
    Boolean(selectedInternshipId) &&
    userQuery.trim().length > 0 &&
    !pipelineMutation.isPending;

  function runWorkflow() {
    if (!canRun || !selectedWorkspace) {
      return;
    }

    pipelineMutation.mutate({
      mode: executionMode,
      input: {
        user_query: userQuery.trim(),
        workspace_id: selectedWorkspace.id,
        user_id: selectedWorkspace.owner_id,
        document_id: selectedDocumentId,
        internship_post_id: selectedInternshipId,
      },
    });
  }

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-4 border-b border-border pb-8 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-normal">
            Internship Match
          </h1>
          <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">
            Run the complete AgentForge pipeline against a CV and internship.
          </p>
        </div>
        <Badge tone={executionMode === "langgraph" ? "default" : "muted"}>
          {EXECUTION_MODE_LABELS[executionMode]}
        </Badge>
      </section>

      {dataError ? (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent>
            <p className="text-sm font-medium text-amber-800">
              Could not load workflow data.
            </p>
            <p className="mt-1 text-sm text-amber-700">
              {getErrorMessage(dataError)}
            </p>
          </CardContent>
        </Card>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-muted text-primary">
                <BrainCircuit className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <h2 className="text-lg font-semibold tracking-normal">
                  Workflow Input
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Select context and run the pipeline.
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoadingData ? (
              <div className="space-y-3">
                <div className="h-11 animate-pulse rounded-lg bg-muted" />
                <div className="h-11 animate-pulse rounded-lg bg-muted" />
                <div className="h-11 animate-pulse rounded-lg bg-muted" />
              </div>
            ) : (
              <div className="space-y-5">
                <SelectField
                  id="workspace"
                  label="Workspace"
                  value={selectedWorkspaceId}
                  onChange={setSelectedWorkspaceId}
                >
                  {workspaces.length === 0 ? (
                    <option value="">No workspaces</option>
                  ) : null}
                  {workspaces.map((workspace) => (
                    <option key={workspace.id} value={workspace.id}>
                      {workspace.name}
                    </option>
                  ))}
                </SelectField>

                <SelectField
                  id="document"
                  label="CV Document"
                  value={selectedDocumentId}
                  onChange={setSelectedDocumentId}
                  disabled={!selectedWorkspaceId || documents.length === 0}
                >
                  {documents.length === 0 ? (
                    <option value="">No ready documents</option>
                  ) : null}
                  {documents.map((document) => (
                    <option key={document.id} value={document.id}>
                      {document.filename}
                    </option>
                  ))}
                </SelectField>

                <SelectField
                  id="internship"
                  label="Internship Post"
                  value={selectedInternshipId}
                  onChange={setSelectedInternshipId}
                  disabled={!selectedWorkspaceId || internships.length === 0}
                >
                  {internships.length === 0 ? (
                    <option value="">No internships</option>
                  ) : null}
                  {internships.map((internship) => (
                    <option key={internship.id} value={internship.id}>
                      {formatInternshipLabel(internship)}
                    </option>
                  ))}
                </SelectField>

                <div>
                  <span className="text-sm font-medium">Execution Mode</span>
                  <div className="mt-2 grid grid-cols-2 gap-2 rounded-lg border border-border bg-muted/35 p-1">
                    {(["manual", "langgraph"] as const).map((mode) => (
                      <button
                        key={mode}
                        type="button"
                        onClick={() => setExecutionMode(mode)}
                        className={cn(
                          "inline-flex min-h-10 items-center justify-center rounded-md px-3 text-sm font-medium transition-colors",
                          executionMode === mode
                            ? "bg-surface text-foreground shadow-sm"
                            : "text-muted-foreground hover:text-foreground",
                        )}
                      >
                        {EXECUTION_MODE_LABELS[mode]}
                      </button>
                    ))}
                  </div>
                </div>

                <label htmlFor="query" className="block">
                  <span className="text-sm font-medium">User Query</span>
                  <textarea
                    id="query"
                    value={userQuery}
                    onChange={(event) => setUserQuery(event.target.value)}
                    rows={4}
                    className="mt-2 w-full resize-none rounded-lg border border-border bg-surface px-3 py-3 text-sm leading-6 outline-none transition-colors focus:border-primary"
                  />
                </label>

                {documents.length === 0 ? (
                  <EmptyState message="Upload and index a ready CV document before running the pipeline." />
                ) : null}

                <button
                  type="button"
                  disabled={!canRun}
                  onClick={runWorkflow}
                  className={cn(
                    "inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                  )}
                >
                  {pipelineMutation.isPending ? (
                    <Loader2
                      className="h-4 w-4 animate-spin"
                      aria-hidden="true"
                    />
                  ) : (
                    <Search className="h-4 w-4" aria-hidden="true" />
                  )}
                  Run {EXECUTION_MODE_LABELS[executionMode]}
                </button>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-5">
          {pipelineMutation.error ? (
            <Card className="border-amber-200 bg-amber-50">
              <CardContent>
                <div className="flex gap-2 text-sm text-amber-800">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{getErrorMessage(pipelineMutation.error)}</span>
                </div>
              </CardContent>
            </Card>
          ) : null}

          <ResultPanel result={pipelineMutation.data} />
        </div>
      </section>
    </div>
  );
}

function formatInternshipLabel(internship: InternshipPost) {
  const location = internship.location ? ` - ${internship.location}` : "";
  return `${internship.title} at ${internship.company_name}${location}`;
}
