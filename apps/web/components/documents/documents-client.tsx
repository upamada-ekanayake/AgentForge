"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  FileText,
  Loader2,
  Upload,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { getDocuments, getWorkspaces, uploadDocument } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Document } from "@/types";

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;
const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt"];

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatFileSize(sizeBytes: number | null) {
  if (sizeBytes === null) {
    return "Unknown";
  }

  if (sizeBytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(sizeBytes / 1024))} KB`;
  }

  return `${(sizeBytes / 1024 / 1024).toFixed(1)} MB`;
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === "string") {
    return error;
  }

  return "Something went wrong.";
}

function getStatusTone(status: Document["status"]) {
  if (status === "uploaded" || status === "ready") {
    return "success";
  }

  if (status === "failed") {
    return "warning";
  }

  return "muted";
}

function validateFile(file: File) {
  const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (!ACCEPTED_EXTENSIONS.includes(extension)) {
    return "Only PDF, DOCX, and TXT files are supported.";
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return "File size must be 10 MB or less.";
  }

  return null;
}

export function DocumentsClient() {
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [clientError, setClientError] = useState<string | null>(null);

  const workspacesQuery = useQuery({
    queryKey: ["workspaces"],
    queryFn: getWorkspaces,
  });
  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
  });

  const workspace = workspacesQuery.data?.[0];

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!workspace) {
        throw new Error("Create or seed a workspace before uploading documents.");
      }

      setUploadProgress(0);
      return uploadDocument({
        file,
        workspaceId: workspace.id,
        userId: workspace.owner_id,
        onProgress: setUploadProgress,
      });
    },
    onSuccess: async () => {
      setSelectedFile(null);
      setUploadProgress(100);
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const documents = documentsQuery.data ?? [];
  const isUploading = uploadMutation.isPending;
  const uploadError = clientError ?? uploadMutation.error;

  function chooseFile(file: File | undefined) {
    if (!file || isUploading) {
      return;
    }

    const validationError = validateFile(file);
    setClientError(validationError);
    uploadMutation.reset();
    setUploadProgress(0);

    if (validationError) {
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  }

  function submitUpload() {
    if (!selectedFile || isUploading) {
      return;
    }

    setClientError(null);
    uploadMutation.mutate(selectedFile);
  }

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-4 border-b border-border pb-8 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-normal">Documents</h1>
          <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">
            Upload CVs and source files into local AgentForge storage.
          </p>
        </div>
        <Badge tone={workspace ? "success" : "warning"}>
          {workspace ? workspace.name : "No workspace"}
        </Badge>
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.45fr)]">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold tracking-normal">
              Upload Document
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              PDF, DOCX, or TXT. Maximum size 10 MB.
            </p>
          </CardHeader>
          <CardContent>
            <input
              ref={inputRef}
              className="hidden"
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(event) => chooseFile(event.target.files?.[0])}
            />

            <button
              type="button"
              className={cn(
                "flex min-h-52 w-full flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/40 px-5 text-center transition-colors",
                isDragging ? "border-primary bg-primary/5" : null,
              )}
              onClick={() => inputRef.current?.click()}
              onDragEnter={(event) => {
                event.preventDefault();
                setIsDragging(true);
              }}
              onDragOver={(event) => event.preventDefault()}
              onDragLeave={(event) => {
                event.preventDefault();
                setIsDragging(false);
              }}
              onDrop={(event) => {
                event.preventDefault();
                setIsDragging(false);
                chooseFile(event.dataTransfer.files[0]);
              }}
            >
              <Upload className="h-9 w-9 text-primary" aria-hidden="true" />
              <span className="mt-4 text-sm font-medium">
                Drop a file here or click to browse
              </span>
              <span className="mt-2 text-xs text-muted-foreground">
                Stored in <code>storage/documents</code>
              </span>
            </button>

            {selectedFile ? (
              <div className="mt-4 rounded-lg border border-border bg-background p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      {selectedFile.name}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                  <FileText
                    className="h-5 w-5 shrink-0 text-muted-foreground"
                    aria-hidden="true"
                  />
                </div>

                {isUploading || uploadProgress > 0 ? (
                  <div className="mt-4">
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary transition-all"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">
                      Upload progress: {uploadProgress}%
                    </p>
                  </div>
                ) : null}
              </div>
            ) : null}

            {uploadError ? (
              <div className="mt-4 flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{getErrorMessage(uploadError)}</span>
              </div>
            ) : null}

            {uploadMutation.isSuccess ? (
              <div className="mt-4 flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                <span>Document uploaded successfully.</span>
              </div>
            ) : null}

            <button
              type="button"
              disabled={!selectedFile || isUploading || !workspace}
              onClick={submitUpload}
              className="mt-5 inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isUploading ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Upload className="h-4 w-4" aria-hidden="true" />
              )}
              Upload
            </button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold tracking-normal">
                  Document Library
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Files loaded from <code>/documents</code>.
                </p>
              </div>
              <Badge tone="muted">{documents.length} total</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {documentsQuery.isLoading ? (
              <div className="space-y-3">
                <div className="h-12 animate-pulse rounded-lg bg-muted" />
                <div className="h-12 animate-pulse rounded-lg bg-muted" />
                <div className="h-12 animate-pulse rounded-lg bg-muted" />
              </div>
            ) : documents.length === 0 ? (
              <div className="flex min-h-48 flex-col items-center justify-center rounded-lg border border-border bg-muted/30 text-center">
                <FileText className="h-8 w-8 text-muted-foreground" />
                <p className="mt-3 text-sm font-medium">No documents yet</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Uploaded files will appear here.
                </p>
              </div>
            ) : (
              <div className="overflow-hidden rounded-lg border border-border">
                <table className="w-full border-collapse text-sm">
                  <thead className="bg-muted text-left text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3 font-medium">Filename</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                      <th className="px-4 py-3 font-medium">Size</th>
                      <th className="px-4 py-3 font-medium">Uploaded</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {documents.map((document) => (
                      <tr key={document.id} className="bg-surface">
                        <td className="max-w-64 px-4 py-3">
                          <div className="flex items-center gap-2">
                            <FileText
                              className="h-4 w-4 shrink-0 text-muted-foreground"
                              aria-hidden="true"
                            />
                            <span className="truncate font-medium">
                              {document.filename}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge tone={getStatusTone(document.status)}>
                            {document.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {formatFileSize(document.size_bytes)}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {formatDate(document.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
