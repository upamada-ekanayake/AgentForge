"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  BriefcaseBusiness,
  Building2,
  Server,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { getHealth, getInternshipPosts, getWorkspaces } from "@/lib/api";
import type { InternshipPost } from "@/types";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong.";
}

function MetricCard({
  icon: Icon,
  label,
  value,
  helper,
}: {
  icon: typeof Building2;
  label: string;
  value: string;
  helper: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-normal">{value}</p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-muted text-primary">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{helper}</p>
      </CardContent>
    </Card>
  );
}

function InternshipCard({ internship }: { internship: InternshipPost }) {
  return (
    <Card className="transition-colors hover:border-primary/35">
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h3 className="text-base font-semibold">{internship.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {internship.company_name}
              {internship.location ? ` - ${internship.location}` : ""}
            </p>
          </div>
          <Badge tone={internship.is_active ? "success" : "muted"}>
            {internship.is_active ? "Active" : "Inactive"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="line-clamp-2 text-sm leading-6 text-muted-foreground">
          {internship.description}
        </p>
        <div className="mt-4 flex items-center justify-between gap-4 text-xs text-muted-foreground">
          <span>Created {formatDate(internship.created_at)}</span>
          {internship.source_url ? (
            <a
              href={internship.source_url}
              className="font-medium text-primary hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              Source
            </a>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardClient() {
  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
  });
  const workspacesQuery = useQuery({
    queryKey: ["workspaces"],
    queryFn: getWorkspaces,
  });
  const internshipsQuery = useQuery({
    queryKey: ["internships"],
    queryFn: getInternshipPosts,
  });

  const workspaces = workspacesQuery.data ?? [];
  const internships = internshipsQuery.data ?? [];
  const isLoading = workspacesQuery.isLoading || internshipsQuery.isLoading;
  const error =
    workspacesQuery.error ?? internshipsQuery.error ?? healthQuery.error;

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-4 border-b border-border pb-8 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-normal">
            Dashboard
          </h1>
          <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">
            Live workspace and internship data from the AgentForge FastAPI
            backend.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm">
          <Server className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <span className="text-muted-foreground">Backend</span>
          <Badge
            tone={
              healthQuery.data?.database === "connected" ? "success" : "warning"
            }
          >
            {healthQuery.isLoading
              ? "Checking"
              : healthQuery.data?.database ?? "Unavailable"}
          </Badge>
        </div>
      </section>

      {error ? (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent>
            <p className="text-sm font-medium text-amber-800">
              Could not load backend data.
            </p>
            <p className="mt-1 text-sm text-amber-700">
              {getErrorMessage(error)}
            </p>
          </CardContent>
        </Card>
      ) : null}

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard
          icon={Building2}
          label="Workspaces"
          value={isLoading ? "..." : String(workspaces.length)}
          helper="Active collaboration spaces"
        />
        <MetricCard
          icon={BriefcaseBusiness}
          label="Internships"
          value={isLoading ? "..." : String(internships.length)}
          helper="Seeded opportunities available"
        />
        <MetricCard
          icon={Activity}
          label="API Health"
          value={healthQuery.data?.status === "ok" ? "Online" : "Checking"}
          helper={healthQuery.data?.service ?? "agentforge-api"}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold tracking-normal">
                Internship Match Workflow
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Run the complete Planner to Match Report pipeline.
              </p>
            </div>
            <Link
              href="/internship-match"
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              Open Workflow
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </CardContent>
        </Card>

        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold tracking-normal">
                Internship Ranking
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Rank all active internships against one CV.
              </p>
            </div>
            <Link
              href="/internship-rank"
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              Open Ranking
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </CardContent>
        </Card>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold tracking-normal">
              Internship Posts
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Data loaded from <code>/internships</code>.
            </p>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {isLoading ? (
            <>
              <Card className="h-44 animate-pulse bg-muted" />
              <Card className="h-44 animate-pulse bg-muted" />
            </>
          ) : (
            internships.map((internship) => (
              <InternshipCard key={internship.id} internship={internship} />
            ))
          )}
        </div>
      </section>
    </div>
  );
}
