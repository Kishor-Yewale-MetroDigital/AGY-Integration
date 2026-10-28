import { Department, HiringRequest, User } from "../types/talentflow";

const API_BASE = "/api/v1";

async function apiFetch<T>(
  path: string,
  userId: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": userId,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail));
  }
  return res.json();
}

export const talentflowApi = {
  getUsers: (userId: string) => apiFetch<User[]>("/users", userId),
  getDepartments: (userId: string) => apiFetch<Department[]>("/departments", userId),
  getRequests: (userId: string, queryString = "") =>
    apiFetch<HiringRequest[]>(`/requests${queryString}`, userId),
  createRequest: (userId: string, payload: Record<string, unknown>) =>
    apiFetch<HiringRequest>("/requests", userId, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  submitRequest: (userId: string, requestId: string) =>
    apiFetch<HiringRequest>(`/requests/${requestId}/submit`, userId, {
      method: "POST",
    }),
  decideRequest: (
    userId: string,
    requestId: string,
    decision: "APPROVE" | "REJECT" | "REQUEST_CLARIFICATION",
    comments: string
  ) =>
    apiFetch<HiringRequest>(`/requests/${requestId}/decisions`, userId, {
      method: "POST",
      body: JSON.stringify({ decision, comments }),
    }),
  getDashboardOverview: (userId: string, queryString = "") =>
    apiFetch<Record<string, any>>(`/dashboard/overview${queryString}`, userId),
  triggerBigQuerySync: (userId: string) =>
    apiFetch<Record<string, any>>("/analytics/sync", userId, { method: "POST" }),
  getAuditEvents: (userId: string) =>
    apiFetch<Array<Record<string, any>>>("/audit-events", userId),
};
