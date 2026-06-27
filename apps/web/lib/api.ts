import type {
  AgentRun,
  AgentRunDetail,
  ApiHealthResponse,
  Document,
  InternshipMatchGraphResponse,
  InternshipMatchPipelineInput,
  InternshipMatchPipelineResponse,
  InternshipRankPipelineInput,
  InternshipRankPipelineResponse,
  InternshipPost,
  Workspace,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type RequestOptions = RequestInit & {
  path: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<TResponse>({
  path,
  headers,
  ...init
}: RequestOptions): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  });

  if (!response.ok) {
    let message = `API request failed with status ${response.status}`;

    try {
      const errorBody = (await response.json()) as { detail?: string };
      if (errorBody.detail) {
        message = errorBody.detail;
      }
    } catch {
      // Keep the default message when the backend does not return JSON.
    }

    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<TResponse>;
}

type UploadDocumentInput = {
  file: File;
  workspaceId: string;
  userId: string;
  onProgress?: (progress: number) => void;
};

export function getHealth() {
  return apiRequest<ApiHealthResponse>({ path: "/health" });
}

export function getWorkspaces() {
  return apiRequest<Workspace[]>({ path: "/workspaces" });
}

export function getInternshipPosts() {
  return apiRequest<InternshipPost[]>({ path: "/internships" });
}

export function getDocuments() {
  return apiRequest<Document[]>({ path: "/documents" });
}

export function getAgentRuns() {
  return apiRequest<AgentRun[]>({ path: "/agents/runs?limit=30" });
}

export function getAgentRun(runId: string) {
  return apiRequest<AgentRunDetail>({ path: `/agents/runs/${runId}` });
}

export function uploadDocument({
  file,
  workspaceId,
  userId,
  onProgress,
}: UploadDocumentInput) {
  const formData = new FormData();
  formData.append("workspace_id", workspaceId);
  formData.append("user_id", userId);
  formData.append("file", file);

  return new Promise<Document>((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", `${API_BASE_URL}/documents/upload`);

    request.upload.onprogress = (event) => {
      if (!event.lengthComputable) {
        return;
      }

      onProgress?.(Math.round((event.loaded / event.total) * 100));
    };

    request.onload = () => {
      if (request.status >= 200 && request.status < 300) {
        resolve(JSON.parse(request.responseText) as Document);
        return;
      }

      let message = `API request failed with status ${request.status}`;
      try {
        const errorBody = JSON.parse(request.responseText) as { detail?: string };
        if (errorBody.detail) {
          message = errorBody.detail;
        }
      } catch {
        // Keep the default message when the backend does not return JSON.
      }

      reject(new ApiError(message, request.status));
    };

    request.onerror = () => {
      reject(new ApiError("Could not connect to the API.", request.status));
    };

    request.send(formData);
  });
}

export function runInternshipMatchPipeline(
  input: InternshipMatchPipelineInput,
) {
  return apiRequest<InternshipMatchPipelineResponse>({
    path: "/agents/internship-match/run",
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function runInternshipMatchGraphPipeline(
  input: InternshipMatchPipelineInput,
) {
  return apiRequest<InternshipMatchGraphResponse>({
    path: "/agents/internship-match-graph/run",
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function runInternshipRankPipeline(
  input: InternshipRankPipelineInput,
) {
  return apiRequest<InternshipRankPipelineResponse>({
    path: "/agents/internship-rank/run",
    method: "POST",
    body: JSON.stringify(input),
  });
}
