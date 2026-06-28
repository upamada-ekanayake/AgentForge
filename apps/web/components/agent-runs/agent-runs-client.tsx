"use client";

import { Fragment, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileJson,
  GitBranch,
  RefreshCw,
  XCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { getAgentRun, getAgentRuns } from "@/lib/api";
import type { AgentRun, AgentRunDetail } from "@/types";

type StageStatus = "succeeded" | "running" | "failed" | "skipped";

type VisualizerStage = {
  id: string;
  label: string;
  status: StageStatus;
  agentRunId?: string | null;
  summary: string;
  details: Record<string, unknown>;
};

const MANUAL_STAGES = [
  {
    id: "planner",
    label: "Planner",
    runIdKey: "planner_agent_run_id",
  },
  {
    id: "retriever",
    label: "Retriever",
    runIdKey: "retriever_agent_run_id",
  },
  {
    id: "evidence_analyzer",
    label: "Evidence Analyzer",
    runIdKey: "evidence_analyzer_agent_run_id",
  },
  {
    id: "context_builder",
    label: "Context Builder",
    runIdKey: "context_builder_agent_run_id",
  },
  {
    id: "match_report_generator",
    label: "Match Report",
    runIdKey: "match_report_agent_run_id",
  },
] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" ? value : null;
}

function getNestedRecord(
  source: Record<string, unknown>,
  key: string,
): Record<string, unknown> | null {
  const value = source[key];
  return isRecord(value) ? value : null;
}

function formatDate(value: string | null) {
  if (!value) {
    return "Not recorded";
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatDuration(startedAt: string | null, completedAt: string | null) {
  if (!startedAt || !completedAt) {
    return "Pending";
  }

  const durationMs = new Date(completedAt).getTime() - new Date(startedAt).getTime();
  if (Number.isNaN(durationMs) || durationMs < 0) {
    return "Unknown";
  }
  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }

  return `${(durationMs / 1000).toFixed(1)} s`;
}

function formatRunType(runType: string) {
  return runType
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getStatusTone(status: string): "success" | "warning" | "muted" {
  if (status === "succeeded") {
    return "success";
  }
  if (status === "failed" || status === "running") {
    return "warning";
  }
  return "muted";
}

function StageIcon({ status }: { status: StageStatus }) {
  const className = "h-4 w-4";

  if (status === "succeeded") {
    return <CheckCircle2 className={className} aria-hidden="true" />;
  }
  if (status === "failed") {
    return <XCircle className={className} aria-hidden="true" />;
  }
  if (status === "running") {
    return <Clock3 className={className} aria-hidden="true" />;
  }
  return <AlertTriangle className={className} aria-hidden="true" />;
}

function summarizeManualStage(
  stageId: string,
  output: Record<string, unknown>,
): string {
  if (stageId === "planner") {
    const plan = getNestedRecord(output, "plan");
    const taskType = asString(plan?.task_type);
    return taskType ? `Task: ${taskType}` : "Plan generated";
  }

  if (stageId === "retriever") {
    const retrieval = getNestedRecord(output, "retrieval_summary");
    const chunkCount = asNumber(retrieval?.cv_chunk_count);
    const topScore = asNumber(retrieval?.top_score);
    return `Chunks: ${chunkCount ?? 0}, top score: ${
      topScore === null ? "n/a" : topScore.toFixed(3)
    }`;
  }

  if (stageId === "evidence_analyzer") {
    const evidence = getNestedRecord(output, "evidence_summary");
    const kept = asNumber(evidence?.kept_chunk_count);
    const discarded = asNumber(evidence?.discarded_chunk_count);
    return `Kept ${kept ?? 0}, discarded ${discarded ?? 0}`;
  }

  if (stageId === "context_builder") {
    const context = getNestedRecord(output, "context_summary");
    const sourceCount = asNumber(context?.source_chunk_count);
    return `Sources: ${sourceCount ?? 0}`;
  }

  const report = getNestedRecord(output, "report");
  const score = asNumber(report?.match_score);
  return score === null ? "Report not generated" : `Match score: ${score.toFixed(1)}%`;
}

function deriveStages(run: AgentRunDetail | undefined): VisualizerStage[] {
  if (!run?.output_payload) {
    return [];
  }

  const output = run.output_payload;
  const completedStages = output.completed_stages;

  if (Array.isArray(completedStages)) {
    const completed = new Set(completedStages.filter((stage): stage is string => typeof stage === "string"));
    const graphStages = [
      "planner",
      "retriever",
      "evidence_analyzer",
      "context_builder",
      "match_report_generator",
    ];

    return graphStages.map((stage) => ({
      id: stage,
      label: formatRunType(stage),
      status: completed.has(stage) ? "succeeded" : "skipped",
      summary: completed.has(stage) ? "Completed by LangGraph" : "Not reached",
      details: {
        stage,
        completed: completed.has(stage),
        state_value: output[stage] ?? null,
      },
    }));
  }

  if (run.run_type === "internship_match_pipeline") {
    const stoppedReason = asString(output.stopped_reason);

    return MANUAL_STAGES.map((stage) => {
      const agentRunId = asString(output[stage.runIdKey]);
      const status: StageStatus = agentRunId
        ? "succeeded"
        : stoppedReason
          ? "skipped"
          : "running";

      return {
        id: stage.id,
        label: stage.label,
        status,
        agentRunId,
        summary: summarizeManualStage(stage.id, output),
        details: {
          agent_run_id: agentRunId,
          stopped_reason: stoppedReason,
          parent_output: output,
        },
      };
    });
  }

  return [
    {
      id: run.run_type,
      label: formatRunType(run.run_type),
      status: run.status === "failed" ? "failed" : run.status === "running" ? "running" : "succeeded",
      agentRunId: run.id,
      summary: "Single agent run",
      details: {
        input_payload: run.input_payload,
        output_payload: run.output_payload,
      },
    },
  ];
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong.";
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="max-h-[28rem] overflow-auto rounded-lg border border-border bg-muted p-4 text-xs leading-5 text-muted-foreground">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function RunListItem({
  run,
  isSelected,
  onSelect,
}: {
  run: AgentRun;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-lg border p-4 text-left transition-colors ${
        isSelected
          ? "border-primary/40 bg-primary/5"
          : "border-border bg-background hover:border-primary/30"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{formatRunType(run.run_type)}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {formatDate(run.created_at)}
          </p>
        </div>
        <Badge tone={getStatusTone(run.status)}>{run.status}</Badge>
      </div>
      <p className="mt-3 font-mono text-xs text-muted-foreground">
        {run.id.slice(0, 8)}
      </p>
    </button>
  );
}

function StageButton({
  stage,
  isSelected,
  onSelect,
}: {
  stage: VisualizerStage;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`flex w-full items-start gap-4 rounded-lg border p-4 text-left transition-colors ${
        isSelected
          ? "border-primary/40 bg-primary/5"
          : "border-border bg-background hover:border-primary/30"
      }`}
    >
      <span
        className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${
          stage.status === "succeeded"
            ? "border-emerald-200 bg-emerald-50 text-emerald-700"
            : stage.status === "failed"
              ? "border-red-200 bg-red-50 text-red-700"
              : "border-border bg-muted text-muted-foreground"
        }`}
      >
        <StageIcon status={stage.status} />
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-semibold">{stage.label}</span>
        <span className="mt-1 block text-xs leading-5 text-muted-foreground">
          {stage.summary}
        </span>
        {stage.agentRunId ? (
          <span className="mt-2 block font-mono text-xs text-muted-foreground">
            run {stage.agentRunId.slice(0, 8)}
          </span>
        ) : null}
      </span>
    </button>
  );
}

function WorkflowNodeGraph({
  stages,
  selectedStageId,
  onSelectStage,
}: {
  stages: VisualizerStage[];
  selectedStageId: string | null;
  onSelectStage: (stageId: string) => void;
}) {
  if (stages.length === 0) {
    return (
      <p className="text-sm leading-6 text-muted-foreground">
        This run has no graph-ready output payload yet.
      </p>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-stretch lg:gap-2">
        {stages.map((stage, index) => {
          const isSelected = stage.id === selectedStageId;
          const isComplete = stage.status === "succeeded";
          const isFailed = stage.status === "failed";

          return (
            <Fragment key={stage.id}>
              <button
                type="button"
                onClick={() => onSelectStage(stage.id)}
                className={`min-h-36 flex-1 rounded-lg border p-4 text-left transition-colors ${
                  isSelected
                    ? "border-primary/50 bg-primary/10 shadow-sm"
                    : "border-border bg-surface hover:border-primary/30"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <span
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${
                      isComplete
                        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                        : isFailed
                          ? "border-red-200 bg-red-50 text-red-700"
                          : "border-border bg-muted text-muted-foreground"
                    }`}
                  >
                    <StageIcon status={stage.status} />
                  </span>
                  <Badge tone={getStatusTone(stage.status)}>
                    {stage.status}
                  </Badge>
                </div>

                <div className="mt-4">
                  <p className="text-sm font-semibold">{stage.label}</p>
                  <p className="mt-2 text-xs leading-5 text-muted-foreground">
                    {stage.summary}
                  </p>
                  {stage.agentRunId ? (
                    <p className="mt-3 font-mono text-xs text-muted-foreground">
                      {stage.agentRunId.slice(0, 8)}
                    </p>
                  ) : null}
                </div>
              </button>

              {index < stages.length - 1 ? (
                <div
                  className="flex items-center justify-center text-muted-foreground lg:w-8"
                  aria-hidden="true"
                >
                  <div className="h-5 w-px bg-border lg:hidden" />
                  <ArrowRight className="hidden h-5 w-5 lg:block" />
                </div>
              ) : null}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}

export function AgentRunsClient() {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedStageId, setSelectedStageId] = useState<string | null>(null);

  const runsQuery = useQuery({
    queryKey: ["agent-runs"],
    queryFn: getAgentRuns,
  });

  const runs = useMemo(() => runsQuery.data ?? [], [runsQuery.data]);

  useEffect(() => {
    if (!selectedRunId && runs.length > 0) {
      setSelectedRunId(runs[0].id);
    }
  }, [runs, selectedRunId]);

  const runDetailQuery = useQuery({
    queryKey: ["agent-run", selectedRunId],
    queryFn: () => getAgentRun(selectedRunId ?? ""),
    enabled: Boolean(selectedRunId),
  });

  const stages = useMemo(
    () => deriveStages(runDetailQuery.data),
    [runDetailQuery.data],
  );

  useEffect(() => {
    if (stages.length > 0 && !stages.some((stage) => stage.id === selectedStageId)) {
      setSelectedStageId(stages[0].id);
    }
  }, [selectedStageId, stages]);

  const selectedStage = stages.find((stage) => stage.id === selectedStageId) ?? null;
  const childRunId =
    selectedStage?.agentRunId && selectedStage.agentRunId !== selectedRunId
      ? selectedStage.agentRunId
      : null;

  const childRunQuery = useQuery({
    queryKey: ["agent-run", childRunId],
    queryFn: () => getAgentRun(childRunId ?? ""),
    enabled: Boolean(childRunId),
  });

  const selectedRun = runDetailQuery.data;
  const detailPayload = childRunQuery.data
    ? {
        input_payload: childRunQuery.data.input_payload,
        output_payload: childRunQuery.data.output_payload,
      }
    : selectedStage?.details;

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-4 border-b border-border pb-8 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-normal">
            Agent Execution Visualizer
          </h1>
          <p className="mt-3 max-w-3xl text-base leading-7 text-muted-foreground">
            Inspect stored agent runs, pipeline stages, inputs, outputs, warnings,
            and execution timing from the AgentForge backend.
          </p>
        </div>
        <button
          type="button"
          onClick={() => runsQuery.refetch()}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-border bg-surface px-4 text-sm font-medium transition-colors hover:bg-muted"
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          Refresh
        </button>
      </section>

      {runsQuery.error ? (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent>
            <p className="text-sm font-medium text-amber-800">
              Could not load agent runs.
            </p>
            <p className="mt-1 text-sm text-amber-700">
              {getErrorMessage(runsQuery.error)}
            </p>
          </CardContent>
        </Card>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[18rem_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" aria-hidden="true" />
              <h2 className="text-lg font-semibold tracking-normal">
                Recent Runs
              </h2>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {runsQuery.isLoading ? (
              <>
                <div className="h-24 animate-pulse rounded-lg bg-muted" />
                <div className="h-24 animate-pulse rounded-lg bg-muted" />
              </>
            ) : runsQuery.error ? (
              <p className="text-sm leading-6 text-muted-foreground">
                Agent run history is unavailable while the backend cannot be
                reached.
              </p>
            ) : runs.length === 0 ? (
              <p className="text-sm leading-6 text-muted-foreground">
                No agent runs yet. Run an internship match or ranking workflow
                to populate this view.
              </p>
            ) : (
              runs.map((run) => (
                <RunListItem
                  key={run.id}
                  run={run}
                  isSelected={run.id === selectedRunId}
                  onSelect={() => {
                    setSelectedRunId(run.id);
                    setSelectedStageId(null);
                  }}
                />
              ))
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <GitBranch
                      className="h-5 w-5 text-primary"
                      aria-hidden="true"
                    />
                    <h2 className="text-lg font-semibold tracking-normal">
                      Execution Graph
                    </h2>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {selectedRun
                      ? `${formatRunType(selectedRun.run_type)} completed in ${formatDuration(
                          selectedRun.started_at,
                          selectedRun.completed_at,
                        )}`
                      : "Select a run to inspect its execution path."}
                  </p>
                </div>
                {selectedRun ? (
                  <Badge tone={getStatusTone(selectedRun.status)}>
                    {selectedRun.status}
                  </Badge>
                ) : null}
              </div>
            </CardHeader>
            <CardContent>
              {runDetailQuery.isLoading ? (
                <div className="h-64 animate-pulse rounded-lg bg-muted" />
              ) : runDetailQuery.error ? (
                <p className="text-sm leading-6 text-muted-foreground">
                  Could not load the selected run details.
                </p>
              ) : !selectedRunId ? (
                <p className="text-sm leading-6 text-muted-foreground">
                  Select a run to inspect its execution graph.
                </p>
              ) : stages.length === 0 ? (
                <p className="text-sm leading-6 text-muted-foreground">
                  This run has no output payload yet.
                </p>
              ) : (
                <div className="space-y-6">
                  <WorkflowNodeGraph
                    stages={stages}
                    selectedStageId={selectedStageId}
                    onSelectStage={setSelectedStageId}
                  />

                  <div>
                    <div className="mb-3 flex items-center justify-between gap-4">
                      <h3 className="text-sm font-semibold tracking-normal">
                        Timeline Fallback
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        Compact cards mirror the graph for narrow reviews.
                      </p>
                    </div>
                    <div className="grid gap-3 md:grid-cols-2">
                      {stages.map((stage) => (
                        <StageButton
                          key={stage.id}
                          stage={stage}
                          isSelected={stage.id === selectedStageId}
                          onSelect={() => setSelectedStageId(stage.id)}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <section className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <FileJson className="h-5 w-5 text-primary" aria-hidden="true" />
                  <h2 className="text-lg font-semibold tracking-normal">
                    Selected Stage
                  </h2>
                </div>
              </CardHeader>
              <CardContent>
                {selectedStage ? (
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm font-semibold">
                        {selectedStage.label}
                      </p>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">
                        {selectedStage.summary}
                      </p>
                    </div>
                    {childRunQuery.isLoading ? (
                      <div className="h-48 animate-pulse rounded-lg bg-muted" />
                    ) : (
                      <JsonBlock value={detailPayload} />
                    )}
                  </div>
                ) : (
                  <p className="text-sm leading-6 text-muted-foreground">
                    Select a timeline stage to inspect payload details.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold tracking-normal">
                  Parent Run Payload
                </h2>
              </CardHeader>
              <CardContent>
                {selectedRun ? (
                  <JsonBlock
                    value={{
                      input_payload: selectedRun.input_payload,
                      output_payload: selectedRun.output_payload,
                    }}
                  />
                ) : (
                  <p className="text-sm leading-6 text-muted-foreground">
                    Select a run to inspect the parent input and output.
                  </p>
                )}
              </CardContent>
            </Card>
          </section>
        </div>
      </section>
    </div>
  );
}
