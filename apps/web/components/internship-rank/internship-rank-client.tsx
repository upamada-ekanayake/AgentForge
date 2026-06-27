"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  Loader2,
  Trophy,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  getDocuments,
  getWorkspaces,
  runInternshipRankPipeline,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import type {
  RankedInternshipResult,
  RetrievalQuality as RetrievalQualityType,
} from "@/types";

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

function getQualityTone(qualityLevel: RetrievalQualityType["quality_level"]) {
  if (qualityLevel === "strong") {
    return "success";
  }

  if (qualityLevel === "medium") {
    return "default";
  }

  return "warning";
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

function QualityBadge({ quality }: { quality: RetrievalQualityType }) {
  return (
    <Badge tone={getQualityTone(quality.quality_level)}>
      {quality.quality_level}
    </Badge>
  );
}

function RankedInternshipCard({ result }: { result: RankedInternshipResult }) {
  return (
    <Card className="transition-colors hover:border-primary/35">
      <CardHeader>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border bg-muted text-sm font-semibold text-primary">
              #{result.rank}
            </div>
            <div>
              <h2 className="text-lg font-semibold tracking-normal">
                {result.title}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {result.company_name}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="default">{result.match_score.toFixed(0)}% match</Badge>
            <QualityBadge quality={result.retrieval_quality} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 lg:grid-cols-[0.75fr_1.25fr]">
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">Top evidence</span>
              <span className="font-medium">
                {formatScore(result.retrieval_quality.top_score)}
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">Average evidence</span>
              <span className="font-medium">
                {formatScore(result.retrieval_quality.average_score)}
              </span>
            </div>
            {result.retrieval_quality.warning ? (
              <div className="flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-800">
                <AlertCircle
                  className="mt-0.5 h-4 w-4 shrink-0"
                  aria-hidden="true"
                />
                <p className="leading-6">{result.retrieval_quality.warning}</p>
              </div>
            ) : null}
          </div>

          <div className="space-y-5">
            <div>
              <h3 className="text-sm font-semibold">Missing Skills</h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {result.missing_skills.length > 0 ? (
                  result.missing_skills.map((skill) => (
                    <Badge key={skill.skill} tone="warning">
                      {skill.skill}
                    </Badge>
                  ))
                ) : (
                  <Badge tone="success">None</Badge>
                )}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold">Recommendations</h3>
              <ul className="mt-3 space-y-2">
                {result.recommendations.slice(0, 3).map((recommendation) => (
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
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function InternshipRankClient() {
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
  const [selectedDocumentId, setSelectedDocumentId] = useState("");

  const workspacesQuery = useQuery({
    queryKey: ["workspaces"],
    queryFn: getWorkspaces,
  });
  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
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

  const rankMutation = useMutation({
    mutationFn: runInternshipRankPipeline,
  });

  const isLoadingData = workspacesQuery.isLoading || documentsQuery.isLoading;
  const dataError = workspacesQuery.error ?? documentsQuery.error;
  const canRun =
    Boolean(selectedWorkspace?.owner_id) &&
    Boolean(selectedDocumentId) &&
    !rankMutation.isPending;
  const ranking = rankMutation.data?.ranking;

  function rankInternships() {
    if (!canRun || !selectedWorkspace) {
      return;
    }

    rankMutation.mutate({
      workspace_id: selectedWorkspace.id,
      user_id: selectedWorkspace.owner_id,
      document_id: selectedDocumentId,
    });
  }

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-4 border-b border-border pb-8 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-normal">
            Internship Rank
          </h1>
          <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">
            Rank every active internship in a workspace against one ready CV.
          </p>
        </div>
        <Badge tone="default">Workspace Ranking</Badge>
      </section>

      {dataError ? (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent>
            <p className="text-sm font-medium text-amber-800">
              Could not load ranking data.
            </p>
            <p className="mt-1 text-sm text-amber-700">
              {getErrorMessage(dataError)}
            </p>
          </CardContent>
        </Card>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-muted text-primary">
                <BarChart3 className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <h2 className="text-lg font-semibold tracking-normal">
                  Ranking Input
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Choose the workspace and CV.
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoadingData ? (
              <div className="space-y-3">
                <div className="h-11 animate-pulse rounded-lg bg-muted" />
                <div className="h-11 animate-pulse rounded-lg bg-muted" />
              </div>
            ) : (
              <div className="space-y-5">
                <SelectField
                  id="rank-workspace"
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
                  id="rank-document"
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

                {documents.length === 0 ? (
                  <EmptyState message="Upload and index a ready CV document before ranking internships." />
                ) : null}

                <button
                  type="button"
                  disabled={!canRun}
                  onClick={rankInternships}
                  className={cn(
                    "inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                  )}
                >
                  {rankMutation.isPending ? (
                    <Loader2
                      className="h-4 w-4 animate-spin"
                      aria-hidden="true"
                    />
                  ) : (
                    <Trophy className="h-4 w-4" aria-hidden="true" />
                  )}
                  Rank Internships
                </button>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-5">
          {rankMutation.error ? (
            <Card className="border-amber-200 bg-amber-50">
              <CardContent>
                <div className="flex gap-2 text-sm text-amber-800">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{getErrorMessage(rankMutation.error)}</span>
                </div>
              </CardContent>
            </Card>
          ) : null}

          {ranking ? (
            <>
              <Card>
                <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Ranked internships
                    </p>
                    <p className="mt-1 text-3xl font-semibold tracking-normal">
                      {ranking.total_ranked}
                    </p>
                  </div>
                  <Badge
                    tone="muted"
                    className="h-auto max-w-full whitespace-normal py-1 leading-5"
                  >
                    {ranking.query}
                  </Badge>
                </CardContent>
              </Card>

              {ranking.results.length > 0 ? (
                ranking.results.map((result) => (
                  <RankedInternshipCard
                    key={result.internship_post_id}
                    result={result}
                  />
                ))
              ) : (
                <Card>
                  <CardContent>
                    <EmptyState message="No active internships were found in this workspace." />
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent>
                <EmptyState message="Run ranking to compare the selected CV against every active internship." />
              </CardContent>
            </Card>
          )}
        </div>
      </section>
    </div>
  );
}
